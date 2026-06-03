import base64
import uuid
import json
import logging

import requests

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_INVALIDACION_VERSION = 2   # versión del evento de invalidación (schema MH)
_ANULACION_API_VERSION = 2  # versión del API de anulación del MH


class DteInvalidacion(models.Model):
    _name = 'dte.invalidacion'
    _description = 'Evento de Invalidación DTE'
    _order = 'fecha_invalidacion desc, id desc'
    _rec_name = 'codigo_generacion'

    # ── Relación con la factura ────────────────────────────────────────────────

    move_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
        ondelete='cascade',
        readonly=True,
    )

    # ── Identificación del evento ──────────────────────────────────────────────

    codigo_generacion = fields.Char(
        string='Código de Generación del Evento',
        readonly=True,
        copy=False,
        help='UUID v4 del evento de invalidación generado por el sistema.',
    )

    # ── Estado ────────────────────────────────────────────────────────────────

    estado = fields.Selection(
        selection=[
            ('pendiente', 'Pendiente de Envío'),
            ('enviado',   'Enviado'),
            ('procesado', 'Procesado por MH'),
            ('rechazado', 'Rechazado por MH'),
            ('error',     'Error de Conexión'),
        ],
        string='Estado',
        default='pendiente',
        readonly=True,
        copy=False,
    )

    # ── Datos del motivo ───────────────────────────────────────────────────────

    tipo_anulacion = fields.Selection(
        selection=[
            ('1', 'Anulación con reemplazo (requiere código del DTE sustituto)'),
            ('2', 'Anulación sin reemplazo'),
        ],
        string='Tipo de Anulación',
        required=True,
    )
    motivo_anulacion = fields.Char(
        string='Motivo de Anulación',
        size=200,
        help='Descripción del motivo. Requerido para tipo "Otro".',
    )

    # ── Datos del responsable ──────────────────────────────────────────────────

    nombre_responsable = fields.Char(
        string='Nombre del Responsable',
        required=True,
        size=100,
    )
    tip_doc_responsable = fields.Selection(
        selection=[
            ('13', 'DUI'),
            ('36', 'NIT'),
            ('02', 'Carnet de Residente'),
            ('03', 'Pasaporte'),
            ('37', 'Otro'),
        ],
        string='Tipo Doc. Responsable',
        required=True,
    )
    num_doc_responsable = fields.Char(
        string='Número Doc. Responsable',
        required=True,
        size=20,
    )

    # ── Datos del solicitante ──────────────────────────────────────────────────

    nombre_solicita = fields.Char(
        string='Nombre del Solicitante',
        required=True,
        size=100,
    )
    tip_doc_solicita = fields.Selection(
        selection=[
            ('13', 'DUI'),
            ('36', 'NIT'),
            ('02', 'Carnet de Residente'),
            ('03', 'Pasaporte'),
            ('37', 'Otro'),
        ],
        string='Tipo Doc. Solicitante',
        required=True,
    )
    num_doc_solicita = fields.Char(
        string='Número Doc. Solicitante',
        required=True,
        size=20,
    )

    # ── Documento sustituto (opcional) ────────────────────────────────────────

    codigo_generacion_r = fields.Char(
        string='Código Generación Documento Sustituto',
        size=36,
        help='UUID del DTE que reemplaza al invalidado (si aplica).',
    )

    # ── JSON generado ─────────────────────────────────────────────────────────

    json_evento = fields.Text(
        string='JSON del Evento de Invalidación',
        readonly=True,
        copy=False,
    )

    # ── Respuesta del MH ──────────────────────────────────────────────────────

    sello_recibido = fields.Char(
        string='Sello Recibido MH',
        readonly=True,
        copy=False,
    )
    fecha_invalidacion = fields.Datetime(
        string='Fecha/Hora de Invalidación',
        readonly=True,
        copy=False,
    )
    respuesta_mh = fields.Text(
        string='Respuesta MH (raw)',
        readonly=True,
        copy=False,
    )
    descripcion_mensaje = fields.Char(
        string='Descripción Mensaje MH',
        readonly=True,
        copy=False,
    )
    observaciones = fields.Text(
        string='Observaciones MH',
        readonly=True,
        copy=False,
    )

    # ── Generación del JSON del evento ────────────────────────────────────────

    def _calcular_monto_iva(self):
        """Obtiene el monto IVA del DTE desde el JSON aceptado o lo calcula como fallback."""
        move = self.move_id
        if move.dte_json:
            try:
                dte = json.loads(move.dte_json)
                resumen = dte.get('resumen', {})
                ti = resumen.get('totalIva')
                if ti is not None:
                    return round(float(ti), 2)
                for t in (resumen.get('tributos') or []):
                    if t.get('codigo') == '20':
                        return round(float(t.get('valor', 0.0)), 2)
            except Exception:
                pass
        if move.tipo_dte == '01':
            return round(move.amount_untaxed * 13 / 113, 2)
        return round(move.amount_tax, 2)

    def _generar_json_invalidacion(self):
        """Construye el JSON del evento de invalidación según el schema MH v2."""
        self.ensure_one()
        move = self.move_id
        company = move.company_id
        now = fields.Datetime.now()

        # El MH requiere tipoDocumento del receptor para todos los tipos de DTE
        partner = move.partner_id
        vat = (partner.vat or '').strip()
        tipo_doc_receptor = '36' if vat else None
        num_doc_receptor = vat or None
        nombre_receptor = (partner.name or '')[:250] or None
        telefono_receptor = (partner.phone or '')[:30] or None
        correo_receptor = (partner.email or '')[:100] or None

        # tipo 1 = con reemplazo (UUID requerido); tipo 2 = sin reemplazo (siempre null)
        if self.tipo_anulacion == '1':
            codigo_gen_r = (self.codigo_generacion_r or '').strip().upper() or None
        else:
            codigo_gen_r = None

        evento = {
            'identificacion': {
                'version':          _INVALIDACION_VERSION,
                'ambiente':         '00',
                'codigoGeneracion': self.codigo_generacion,
                'fecAnula':         str(now.date()),
                'horAnula':         now.strftime('%H:%M:%S'),
            },
            'emisor': {
                'nit':                  (company.dte_nit or '').strip(),
                'nombre':               (company.name or '')[:250],
                'tipoEstablecimiento':  company.dte_tipo_establecimiento or '01',
                'nomEstablecimiento': (
                    company.dte_nom_establecimiento
                    or company.dte_nombre_comercial
                    or company.name or ''
                )[:150],
                'codEstableMH':         (company.dte_establecimiento or 'S001').strip()[:4],
                'codEstable':           None,
                'codPuntoVentaMH':      (company.dte_punto_venta or 'P001').strip()[:4],
                'codPuntoVenta':        None,
                'telefono':             (company.phone or '')[:30],
                'correo':               (company.email or '')[:100],
            },
            'documento': {
                'tipoDte':           move.tipo_dte,
                'codigoGeneracion':  move.dte_codigo_generacion or '',
                'selloRecibido':     (move.dte_sello_recepcion or ''),
                'numeroControl':     move.dte_numero_control or None,
                'fecEmi':            str(move.invoice_date or now.date()),
                'montoIva':          self._calcular_monto_iva(),
                'codigoGeneracionR': codigo_gen_r,
                'tipoDocumento':     tipo_doc_receptor,
                'numDocumento':      num_doc_receptor,
                'nombre':            nombre_receptor,
                'telefono':          telefono_receptor,
                'correo':            correo_receptor,
            },
            'motivo': {
                'tipoAnulacion':     int(self.tipo_anulacion),
                'motivoAnulacion':   (self.motivo_anulacion or '').strip() or None,
                'nombreResponsable': (self.nombre_responsable or '')[:100],
                'tipDocResponsable': self.tip_doc_responsable or '',
                'numDocResponsable': (self.num_doc_responsable or '')[:20],
                'nombreSolicita':    (self.nombre_solicita or '')[:100],
                'tipDocSolicita':    self.tip_doc_solicita or '',
                'numDocSolicita':    (self.num_doc_solicita or '')[:20],
            },
        }

        return json.dumps(evento, ensure_ascii=False, indent=2)

    # ── Firma del evento ──────────────────────────────────────────────────────

    def _firmar_evento(self):
        """Envía el evento al firmador Java local y retorna el JWT firmado."""
        self.ensure_one()
        company = self.move_id.company_id
        base_url = (company.dte_url_firmador or 'http://localhost:8113').rstrip('/')
        url = f'{base_url}/firmardocumento/'
        evento_obj = json.loads(self.json_evento)
        payload = {
            'nit':         (company.dte_nit or '').strip(),
            'activo':      True,
            'passwordPri': company.dte_password_certificado or '',
            'dteJson':     evento_obj,
        }
        _logger.info(
            'INVALIDACIÓN FIRMA → POST %s | nit=%s | codigoGeneracion=%s',
            url, payload['nit'], self.codigo_generacion,
        )
        try:
            resp = requests.post(url, json=payload, timeout=30)
        except requests.ConnectionError as e:
            raise UserError(f'El firmador no está disponible en {base_url}: {e}')
        except requests.Timeout:
            raise UserError('El firmador no respondió (timeout 30 s).')
        except Exception as e:
            raise UserError(f'Error al conectar con el firmador: {e}')

        _logger.info('INVALIDACIÓN FIRMA ← HTTP %s | body: %s', resp.status_code, resp.text)
        if not resp.ok:
            raise UserError(f'Error del firmador (HTTP {resp.status_code}):\n{resp.text}')

        data = resp.json()
        if data.get('status') != 'OK':
            raise UserError(f'El firmador rechazó el evento de invalidación:\n{data}')

        return data['body']

    # ── Envío al MH ───────────────────────────────────────────────────────────

    def _enviar_a_mh(self, doc_firmado, token):
        """Envía el evento firmado al endpoint /fesv/anulardte/ y procesa la respuesta."""
        self.ensure_one()
        company = self.move_id.company_id
        url = (
            company.dte_url_anulacion
            or 'https://apitest.dtes.mh.gob.sv/fesv/anulardte/'
        )
        headers = {'Content-Type': 'application/json', 'Authorization': token}
        payload = {
            'ambiente': '00',
            'idEnvio':  1,
            'version':  _ANULACION_API_VERSION,
            'documento': doc_firmado,
        }

        self.write({'estado': 'enviado'})

        _logger.info(
            'INVALIDACIÓN ENVÍO → POST %s | codigoGeneracion=%s',
            url, self.codigo_generacion,
        )

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
        except requests.Timeout:
            self.write({'estado': 'error'})
            self.move_id.write({'estado_dte': 'error_invalidacion'})
            raise UserError('El MH no respondió al envío de invalidación (timeout 30 s).')
        except Exception as e:
            self.write({'estado': 'error'})
            self.move_id.write({'estado_dte': 'error_invalidacion'})
            raise UserError(f'Error al enviar la invalidación al MH: {e}')

        _logger.info('INVALIDACIÓN ENVÍO ← HTTP %s | body: %s', resp.status_code, resp.text)

        if not resp.ok:
            self.write({'estado': 'error'})
            self.move_id.write({'estado_dte': 'error_invalidacion'})
            raise UserError(
                f'Error del MH al recibir la invalidación (HTTP {resp.status_code}):\n{resp.text}'
            )

        data = resp.json()
        self.respuesta_mh = json.dumps(data, ensure_ascii=False, indent=2)

        # El endpoint /anulardte/ usa el campo "estado" (no "status" como /recepciondte/)
        estado_mh = data.get('estado') or data.get('status', '')
        sello = data.get('selloRecibido') or ''
        cod_gen = data.get('codigoGeneracion') or self.codigo_generacion

        if estado_mh == 'PROCESADO':
            self.write({
                'estado':              'procesado',
                'codigo_generacion':   cod_gen,
                'sello_recibido':      sello,
                'fecha_invalidacion':  fields.Datetime.now(),
                'descripcion_mensaje': data.get('descripcionMsg', ''),
            })
            self.move_id.write({
                'estado_dte':        'invalidado',
                'dte_observaciones': False,
            })
            _logger.info(
                'INVALIDACIÓN: %s PROCESADA | sello: %s',
                cod_gen, sello,
            )
        elif estado_mh == 'RECHAZADO':
            obs = data.get('observaciones', [])
            self.write({
                'estado':              'rechazado',
                'descripcion_mensaje': data.get('descripcionMsg', ''),
                'observaciones':       '\n'.join(obs) if obs else '',
            })
            self.move_id.write({'estado_dte': 'error_invalidacion'})
            _logger.warning(
                'INVALIDACIÓN: %s RECHAZADA | msg: %s',
                cod_gen, data.get('descripcionMsg'),
            )
        else:
            _logger.warning('INVALIDACIÓN: estado desconocido del MH: %s', data)

        return data

    # ── Notificación al cliente tras invalidación ─────────────────────────────

    def _enviar_notificacion_invalidacion(self):
        """
        Envía al cliente un correo notificando la anulación del DTE.
        Adjunta: PDF de la factura, JSON del DTE original, JSON del evento de invalidación.
        Registra el intento en dte.mail.log para trazabilidad.
        """
        self.ensure_one()
        move = self.move_id
        partner = move.partner_id
        intento_num = len(move.dte_mail_log_ids) + 1
        destinatario = (partner.email or '').strip()

        if not destinatario:
            _logger.warning(
                'INVALIDACIÓN MAIL: factura %s sin correo de cliente — no se envía notificación',
                move.name,
            )
            move.env['dte.mail.log'].create({
                'move_id':        move.id,
                'destinatario':   '(sin correo)',
                'asunto':         'N/A',
                'exitoso':        False,
                'error':          'El cliente no tiene correo electrónico registrado.',
                'intento_numero': intento_num,
            })
            return

        # ── 1. Generar el PDF ──────────────────────────────────────────────
        try:
            pdf_content, _ = move.env['ir.actions.report']._render_qweb_pdf(
                'account.action_account_original_vendor_bill',
                res_ids=move.ids,
            )
        except Exception:
            try:
                pdf_content, _ = move.env['ir.actions.report']._render_qweb_pdf(
                    'account.action_report_original_vendor_bill',
                    res_ids=move.ids,
                )
            except Exception:
                pdf_content, _ = move.env['ir.actions.report']._render_qweb_pdf(
                    'account.report_invoice',
                    res_ids=move.ids,
                )

        # ── 2. Crear adjuntos ──────────────────────────────────────────────
        cod_gen = move.dte_codigo_generacion or move.name.replace('/', '_')
        nombre_pdf = f'{cod_gen}.pdf'
        nombre_json_dte = f'{cod_gen}.json'
        nombre_json_inv = f'ANULACION_{cod_gen}.json'

        attachment_pdf = move.env['ir.attachment'].create({
            'name':      nombre_pdf,
            'type':      'binary',
            'datas':     base64.b64encode(pdf_content).decode('utf-8'),
            'mimetype':  'application/pdf',
            'res_model': 'account.move',
            'res_id':    move.id,
        })

        attachment_json_dte = move.env['ir.attachment'].create({
            'name':      nombre_json_dte,
            'type':      'binary',
            'datas':     base64.b64encode((move.dte_json or '{}').encode('utf-8')).decode('utf-8'),
            'mimetype':  'application/json',
            'res_model': 'account.move',
            'res_id':    move.id,
        })

        attachment_json_inv = move.env['ir.attachment'].create({
            'name':      nombre_json_inv,
            'type':      'binary',
            'datas':     base64.b64encode((self.json_evento or '{}').encode('utf-8')).decode('utf-8'),
            'mimetype':  'application/json',
            'res_model': 'dte.invalidacion',
            'res_id':    self.id,
        })

        # ── 3. Construir y enviar el correo ────────────────────────────────
        asunto = f'Anulación de Factura Electrónica {move.name} — {move.company_id.name}'
        cuerpo = f"""
            <p>Estimado/a <strong>{partner.name}</strong>,</p>
            <p>Le informamos que la factura electrónica
               <strong>{move.name}</strong>
               emitida por <strong>{move.company_id.name}</strong>
               ha sido <strong>anulada (invalidada)</strong> ante el Ministerio de Hacienda.</p>
            <p>Sello de anulación: <code>{self.sello_recibido or 'N/A'}</code></p>
            <p>Adjunto encontrará el PDF de la factura, el JSON del DTE original
               y el JSON del evento de anulación.</p>
            <p>Si tiene alguna consulta, no dude en contactarnos.</p>
        """

        mail_values = {
            'subject':        asunto,
            'body_html':      cuerpo,
            'email_to':       destinatario,
            'email_from':     move.company_id.email or '',
            'author_id':      move.env.user.partner_id.id,
            'attachment_ids': [
                (4, attachment_pdf.id),
                (4, attachment_json_dte.id),
                (4, attachment_json_inv.id),
            ],
            'auto_delete': True,
        }

        error_msg = None
        exitoso = False
        try:
            mail = move.env['mail.mail'].sudo().create(mail_values)
            mail.sudo().send()
            exitoso = True
            _logger.info(
                'INVALIDACIÓN MAIL: notificación de %s enviada a %s (intento %s)',
                move.name, destinatario, intento_num,
            )
        except Exception as e:
            error_msg = str(e)
            _logger.error(
                'INVALIDACIÓN MAIL: fallo al enviar notificación de %s a %s: %s',
                move.name, destinatario, e,
            )

        # ── 4. Registrar el intento en el log ─────────────────────────────
        move.env['dte.mail.log'].create({
            'move_id':        move.id,
            'destinatario':   destinatario,
            'asunto':         asunto,
            'cuerpo':         cuerpo,
            'adjunto_nombre': f'{nombre_pdf}, {nombre_json_dte}, {nombre_json_inv}',
            'exitoso':        exitoso,
            'error':          error_msg,
            'intento_numero': intento_num,
        })

    # ── Acción principal de invalidación ──────────────────────────────────────

    def action_invalidar_dte(self):
        """Orquesta el flujo completo: generar → firmar → enviar → procesar respuesta."""
        self.ensure_one()
        move = self.move_id
        company = move.company_id

        # Validar credenciales mínimas
        missing = []
        if not (company.dte_nit or '').strip():
            missing.append('NIT Emisor')
        if not (company.dte_password_mh or '').strip():
            missing.append('Contraseña MH')
        if not (company.dte_password_certificado or '').strip():
            missing.append('Contraseña Certificado')
        if missing:
            raise UserError(
                'Faltan campos en Ajustes → Empresas → Facturación Electrónica DTE:\n'
                + '\n'.join(f'  • {f}' for f in missing)
            )

        # Tipo 1 exige un DTE de reemplazo; tipo 2 no debe tener ninguno
        if self.tipo_anulacion == '1' and not (self.codigo_generacion_r or '').strip():
            raise UserError(
                'El tipo "Anulación con reemplazo" requiere el Código de Generación del DTE sustituto.'
            )

        # Generar UUID del evento si no existe
        if not self.codigo_generacion:
            self.codigo_generacion = str(uuid.uuid4()).upper()

        # Generar JSON del evento
        self.json_evento = self._generar_json_invalidacion()

        # Obtener token (reutiliza el método de account.move)
        try:
            token = move._obtener_token_mh()
        except UserError:
            self.write({'estado': 'error'})
            move.write({'estado_dte': 'error_invalidacion'})
            self.env.cr.commit()
            raise

        # Firmar evento
        try:
            doc_firmado = self._firmar_evento()
        except UserError:
            self.write({'estado': 'error'})
            move.write({'estado_dte': 'error_invalidacion'})
            self.env.cr.commit()
            raise

        # Enviar al MH y procesar respuesta
        try:
            self._enviar_a_mh(doc_firmado, token)
        except UserError:
            self.env.cr.commit()
            raise

        self.env.cr.commit()

        # Notificar al cliente si la invalidación fue aceptada por el MH
        if move.estado_dte == 'invalidado':
            try:
                self._enviar_notificacion_invalidacion()
            except Exception as e:
                _logger.error(
                    'INVALIDACIÓN MAIL: error no crítico al enviar notificación: %s', e,
                )
            self.env.cr.commit()

import uuid
import json
import logging
import os
import base64

import requests

try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_DTE_VERSION = {'01': 1, '03': 3, '05': 4}
_SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'schemas')
_SCHEMA_FILE = {'01': 'fe-f-v2.json', '03': 'fe-ccf-v4.json', '05': 'fe-nc-v4.json'}


class AccountMove(models.Model):
    _inherit = 'account.move'

    # ── Campos DTE ─────────────────────────────────────────────────────────────

    dte_codigo_generacion = fields.Char(
        string='Código de Generación', readonly=True, copy=False,
        help='UUID v4 generado automáticamente al confirmar la factura.',
    )
    dte_numero_control = fields.Char(
        string='Número de Control', readonly=True, copy=False,
        help='Número de control secuencial asignado por el sistema.',
    )
    dte_sello_recepcion = fields.Char(
        string='Sello de Recepción', readonly=True, copy=False,
        help='Sello devuelto por el Ministerio de Hacienda al aceptar el DTE.',
    )
    dte_json = fields.Text(
        string='JSON DTE', readonly=True, copy=False,
        help='Representación JSON del documento tributario electrónico.',
    )
    tipo_dte = fields.Selection(
        selection=[
            ('01', 'Factura de Consumidor Final'),
            ('03', 'Comprobante de Crédito Fiscal'),
            ('05', 'Nota de Crédito'),
        ],
        string='Tipo DTE', copy=False,
    )
    estado_dte = fields.Selection(
        selection=[
            ('borrador',  'Borrador'),
            ('enviado',   'Enviado'),
            ('aceptado',  'Aceptado'),
            ('rechazado', 'Rechazado'),
            ('pendiente', 'Pendiente de Envío'),
        ],
        string='Estado DTE', default='borrador', copy=False,
    )
    dte_observaciones = fields.Text(string='Observaciones MH', readonly=True, copy=False)
    dte_fecha_procesamiento = fields.Char(string='Fecha Procesamiento MH', readonly=True, copy=False)
    dte_codigo_mensaje = fields.Char(string='Código Mensaje MH', readonly=True, copy=False)
    dte_descripcion_mensaje = fields.Char(string='Descripción Mensaje MH', readonly=True, copy=False)

    # ── Campos de trazabilidad ─────────────────────────────────────────────────

    dte_intentos_envio = fields.Integer(
        string='Intentos de Envío MH',
        default=0,
        readonly=True,
        copy=False,
        help='Número de veces que se intentó enviar el DTE al Ministerio de Hacienda.',
    )
    dte_ultimo_envio = fields.Datetime(
        string='Último Envío MH',
        readonly=True,
        copy=False,
        help='Fecha y hora del último intento de envío al MH.',
    )
    dte_respuesta_mh = fields.Text(
        string='Respuesta MH (raw)',
        readonly=True,
        copy=False,
        help='JSON completo devuelto por el Ministerio de Hacienda en el último envío.',
    )

    # ── Historial de correos ────────────────────────────────────────────────
    dte_mail_log_ids = fields.One2many(
        'dte.mail.log',
        'move_id',
        string='Historial de correos DTE',
        readonly=True,
        copy=False,
    )

    # ── Helpers de generación ──────────────────────────────────────────────────

    def _numero_a_letras(self, amount):
        try:
            from num2words import num2words
            entero = int(amount)
            centavos = round((amount - entero) * 100)
            return f'{num2words(entero, lang="es").upper()} DOLARES CON {centavos:02d}/100'
        except Exception:
            return f'{amount:.2f} DOLARES'

    def _generar_codigo_generacion(self):
        return str(uuid.uuid4()).upper()

    def _generar_numero_control(self):
        self.ensure_one()
        tipo = self.tipo_dte or '01'
        estab = (self.company_id.dte_establecimiento or 'S001').upper()
        pv = (self.company_id.dte_punto_venta or 'P001').upper()
        correlativo = self.env['ir.sequence'].next_by_code(f'dte.sv.control.{tipo}') or '000000000000001'
        return f'DTE-{tipo}-{estab}{pv}-{correlativo}'

    # ── Construcción del DTE ───────────────────────────────────────────────────

    def _build_identificacion(self, tipo):
        ident = {
            'version':          _DTE_VERSION.get(tipo, 1),
            'ambiente':         '00',
            'tipoDte':          tipo,
            'numeroControl':    self.dte_numero_control or '',
            'codigoGeneracion': self.dte_codigo_generacion or '',
            'tipoModelo':       1,
            'tipoOperacion':    1,
            'tipoContingencia': None,
            'motivoContin':     None,
            'fecEmi':           str(self.invoice_date or fields.Date.today()),
            'horEmi':           fields.Datetime.now().strftime('%H:%M:%S'),
            'tipoMoneda':       'USD',
        }
        if tipo == '05':
            ident['fusion'] = None
        return ident

    def _build_emisor(self, tipo):
        c = self.company_id
        emisor = {
            'nit':                 (c.dte_nit or c.vat or '').strip(),
            'nrc':                 (c.dte_nrc or '').strip(),
            'nombre':              (c.name or '')[:250],
            'codActividad':        c.dte_cod_actividad or '',
            'descActividad':       c.dte_desc_actividad or '',
            'nombreComercial':     (c.dte_nombre_comercial or c.name or '')[:150] or None,
            'tipoEstablecimiento': c.dte_tipo_establecimiento or '01',
            'direccion': {
                'departamento': c.dte_departamento or '',
                'municipio':    c.dte_municipio or '',
                'complemento':  (c.street or '')[:200],
            },
            'telefono': (c.phone or '')[:30],
            'correo':   (c.email or '')[:100],
        }
        if tipo in ('01', '03'):
            emisor.update({
                'codEstableMH':    (c.dte_establecimiento or '').strip() or None,
                'codEstable':      None,
                'codPuntoVentaMH': (c.dte_punto_venta or '').strip() or None,
                'codPuntoVenta':   None,
            })
        return emisor

    def _build_receptor(self, tipo):
        p = self.partner_id

        def _dir(depto, muni, complemento):
            depto = (depto or '').strip()
            muni = (muni or '').strip()
            complemento = (complemento or '').strip()[:200]
            if not (depto and muni and complemento):
                return None
            return {'departamento': depto, 'municipio': muni, 'complemento': complemento}

        if tipo == '03':
            return {
                'nit':              (p.vat or '').strip() or None,
                'nrc':              (p.dte_nrc or '').strip() or None,
                'nombre':           (p.name or '')[:250] or None,
                'codActividad':     (p.dte_cod_actividad or '').strip() or None,
                'descActividad':    (p.dte_desc_actividad or '').strip() or None,
                'nombreComercial': (p.name or '')[:150] or None,
                'direccion':       _dir(p.dte_departamento, p.dte_municipio, p.dte_complemento),
                'telefono':         (p.phone or '').strip() or None,
                'correo':           (p.email or '').strip() or None,
            }
        receptor = {
            'tipoDocumento': '36' if p.vat else None,
            'numDocumento':  (p.vat or '').strip() or None,
            'nrc':           None,
            'nombre':        (p.name or '')[:250] or None,
            'codActividad':  None,
            'descActividad': None,
            'direccion':     _dir(p.dte_departamento, p.dte_municipio, p.dte_complemento),
            'telefono':      (p.phone or '')[:30] or None,
            'correo':        (p.email or '')[:100] or None,
        }
        if tipo == '05':
            receptor['nombreComercial'] = (p.name or '')[:150] or None
        return receptor

    def _build_cuerpo(self, tipo):
        lineas = self.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
        cuerpo = []
        for i, linea in enumerate(lineas, start=1):
            codigo = (linea.product_id.default_code or None) if linea.product_id else None

            if tipo == '01':
                # Precios IVA-incluido (13%); se derivan 4 decimales para que
                # precioUni * cantidad - montoDescu == ventaGravada pase validación MH.
                precio_uni = round(linea.price_unit * 1.13, 4)
                bruto_iva = precio_uni * linea.quantity
                monto_desc = round(bruto_iva * (linea.discount or 0.0) / 100, 4)
                gravada = round(bruto_iva - monto_desc, 4)
                tributos = None
            else:
                precio_uni = linea.price_unit
                bruto = linea.price_unit * linea.quantity
                monto_desc = round(bruto * (linea.discount or 0.0) / 100, 8)
                gravada = round(linea.price_subtotal, 2)
                tributos = ['20'] if gravada > 0 else None

            item = {
                'numItem':         i,
                'tipoItem':        2,
                'numeroDocumento': None,
                'codigo':          codigo,
                'codTributo':      None,
                'descripcion':     (linea.name or '')[:1500],
                'cantidad':        linea.quantity,
                'uniMedida':       99,
                'precioUni':       precio_uni,
                'montoDescu':      monto_desc,
                'ventaNoSuj':      0.0,
                'ventaExenta':     0.0,
                'ventaGravada':    gravada,
                'tributos':        tributos,
                'psv':             0.0,
                'noGravado':       0.0,
            }

            if tipo == '01':
                item['ivaItem'] = round(gravada * 13 / 113, 4)
            elif tipo == '05':
                del item['psv']
                item['numeroDocumento'] = (
                    self.reversed_entry_id.dte_codigo_generacion
                    or self.reversed_entry_id.name or ''
                ) if self.reversed_entry_id else ''
                item['ivaPerci'] = 0.0
                item['totalIva'] = round(gravada * 0.13, 8)
                item['ivaRete'] = 0.0

            cuerpo.append(item)
        return cuerpo

    def _build_resumen(self, tipo, cuerpo):
        total_grav = round(sum(i['ventaGravada'] for i in cuerpo), 2)
        iva_nc = total_nc = tributos_nc = None

        if tipo == '01':
            total_iva_res = round(sum(i.get('ivaItem', 0.0) for i in cuerpo), 2)

        if tipo == '03':
            # IVA derivado del totalGravada para satisfacer la validación MH:
            # tributos[20].valor == totalGravada * 0.13
            iva_ccf = round(total_grav * 0.13, 2)
            total_pagar = round(total_grav + iva_ccf, 2)
            tributos_ccf = [
                {'codigo': '20', 'descripcion': 'Impuesto al Valor Agregado 13%',
                 'valor': iva_ccf}] if total_grav > 0 else None

        if tipo == '05':
            iva_nc = round(total_grav * 0.13, 2)
            total_nc = round(total_grav + iva_nc, 2)
            tributos_nc = [
                {'codigo': '20', 'descripcion': 'Impuesto al Valor Agregado 13%',
                 'valor': iva_nc}] if total_grav > 0 else None

        if tipo == '01':
            return {
                'totalNoSuj':          0.0,
                'totalExenta':         0.0,
                'totalGravada':        total_grav,
                'subTotalVentas':      total_grav,
                'descuNoSuj':          0.0,
                'descuExenta':         0.0,
                'descuGravada':        0.0,
                'porcentajeDescuento': 0.0,
                'totalDescu':          0.0,
                'tributos':            None,
                'subTotal':            total_grav,
                'ivaRete1':            0.0,
                'reteRenta':           0.0,
                'montoTotalOperacion': total_grav,
                'totalNoGravado':      0.0,
                'totalPagar':          total_grav,
                'totalLetras':         self._numero_a_letras(total_grav),
                'totalIva':            total_iva_res,
                'saldoFavor':          0.0,
                'condicionOperacion':  1,
                'pagos':               None,
                'numPagoElectronico':  None,
            }
        if tipo == '03':
            return {
                'totalNoSuj':          0.0,
                'totalExenta':         0.0,
                'totalGravada':        total_grav,
                'totalNoGravado':      0.0,
                'subTotalVentas':      total_grav,
                'descuNoSuj':          0.0,
                'descuExenta':         0.0,
                'descuGravada':        0.0,
                'porcentajeDescuento': 0.0,
                'totalDescu':          0.0,
                'tributos':            tributos_ccf,
                'subTotal':            total_grav,
                'ivaPerci1':           0.0,
                'ivaRete1':            0.0,
                'reteRenta':           0.0,
                'montoTotalOperacion': total_pagar,
                'totalPagar':          total_pagar,
                'totalLetras':         self._numero_a_letras(total_pagar),
                'saldoFavor':          0.0,
                'condicionOperacion':  1,
                'pagos':               None,
                'numPagoElectronico':  None,
            }
        # tipo == '05' — Nota de Crédito
        return {
            'totalNoSuj':          0.0,
            'totalExenta':         0.0,
            'totalGravada':        total_grav,
            'subTotalVentas':      total_grav,
            'totalDescu':          0.0,
            'tributos':            tributos_nc,
            'montoTotalOperacion': total_nc,
            'ivaPerci':            0.0,
            'totalIva':            iva_nc,
            'ivaRete':             0.0,
            'totalNoGravado':      0.0,
            'totalPagar':          total_nc,
            'totalLetras':         None,
            'condicionOperacion':  1,
            'observaciones':       None,
            'codigoRetencionMH':   None,
        }

    def _build_doc_relacionado(self, tipo):
        if tipo != '05' or not self.reversed_entry_id:
            return None
        orig = self.reversed_entry_id
        return [{
            'tipoDocumento':   orig.tipo_dte or '01',
            'tipoGeneracion':  1,
            'numeroDocumento': orig.dte_codigo_generacion or orig.name or '',
            'fechaEmision':    str(orig.invoice_date or fields.Date.today()),
        }]

    def _serializar_dte(self):
        """Construye el JSON DTE conforme al schema oficial del MH El Salvador."""
        self.ensure_one()
        tipo = self.tipo_dte or '01'

        cuerpo = self._build_cuerpo(tipo)
        dte = {
            'identificacion':       self._build_identificacion(tipo),
            'documentoRelacionado': self._build_doc_relacionado(tipo),
            'emisor':               self._build_emisor(tipo),
            'receptor':             self._build_receptor(tipo),
            'ventaTercero':         None,
            'cuerpoDocumento':      cuerpo,
            'resumen':              self._build_resumen(tipo, cuerpo),
            'extension': {
                'nombEntrega': None, 'docuEntrega': None,
                'nombRecibe':  None, 'docuRecibe':  None,
                'observaciones': None, 'placaVehiculo': None,
            } if tipo == '01' else None,
            'apendice': None,
        }
        if tipo in ('01', '03'):
            dte['otrosDocumentos'] = None
        return json.dumps(dte, ensure_ascii=False, indent=2)

    # ── Validación de schema ───────────────────────────────────────────────────

    def _validar_schema_dte(self):
        """Valida self.dte_json contra el schema oficial del MH. Lanza UserError si no cumple."""
        self.ensure_one()
        tipo = self.tipo_dte or '01'

        if not _HAS_JSONSCHEMA:
            _logger.warning('DTE: jsonschema no instalado — omitiendo validación de schema')
            return

        schema_file = _SCHEMA_FILE.get(tipo)
        if not schema_file:
            _logger.warning('DTE: no hay schema configurado para tipo %s', tipo)
            return

        schema_path = os.path.join(_SCHEMA_DIR, schema_file)
        try:
            with open(schema_path, encoding='utf-8') as f:
                schema = json.load(f)
        except FileNotFoundError:
            _logger.error('DTE: schema no encontrado en %s', schema_path)
            return

        dte_dict = json.loads(self.dte_json)
        validator = jsonschema.Draft7Validator(schema)
        errors = sorted(validator.iter_errors(dte_dict), key=lambda e: list(e.absolute_path))

        if errors:
            detalles = [
                f'• [{" → ".join(str(p) for p in e.absolute_path) or "(raíz)"}] {e.message}'
                for e in errors[:10]
            ]
            msg = f'El DTE tipo {tipo} no cumple el schema del MH ({len(errors)} error(es)):\n' + '\n'.join(detalles)
            _logger.error('DTE schema inválido:\n%s', msg)
            raise UserError(msg)

        _logger.info('DTE: schema tipo %s validado correctamente', tipo)

    # ── Métodos de envío al MH ─────────────────────────────────────────────────

    def _obtener_token_mh(self):
        """Autentica ante el MH y guarda el token en la empresa. Retorna el token."""
        self.ensure_one()
        company = self.company_id
        url = company.dte_url_auth or 'https://apitest.dtes.mh.gob.sv/seguridad/auth'
        payload = {
            'user': (company.dte_nit or '').strip(),
            'pwd':  (company.dte_password_mh or '').strip(),
        }
        _logger.info('DTE AUTH → POST %s | body: %s', url, json.dumps({**payload, 'pwd': '***'}))
        try:
            resp = requests.post(url, data=payload, timeout=30)
        except requests.Timeout:
            _logger.error('DTE AUTH ← timeout')
            raise UserError('El Ministerio de Hacienda no respondió (timeout 30 s).')
        except requests.ConnectionError as e:
            _logger.error('DTE AUTH ← conexión fallida: %s', e)
            raise UserError(f'No se pudo conectar al MH: {e}')
        except Exception as e:
            _logger.error('DTE AUTH ← error inesperado: %s', e)
            raise UserError(f'Error al conectar con el MH: {e}')

        _logger.info('DTE AUTH ← HTTP %s | body: %s', resp.status_code, resp.text)
        if not resp.ok:
            raise UserError(f'Error de autenticación MH (HTTP {resp.status_code}):\n{resp.text}')

        data = resp.json()
        if data.get('status') != 'OK':
            raise UserError(f'Autenticación MH rechazada:\n{data}')

        token = data['body']['token']
        company.sudo().write({'dte_token': token})
        _logger.info('DTE AUTH: token obtenido correctamente')
        return token

    def _firmar_dte(self, token):
        """Envía el DTE al firmador Java local y retorna el JWT firmado."""
        self.ensure_one()
        company = self.company_id
        base_url = (company.dte_url_firmador or 'http://localhost:8113').rstrip('/')
        url = f'{base_url}/firmardocumento/'
        dte_obj = json.loads(self.dte_json)
        payload = {
            'nit':         company.dte_nit or '',
            'activo':      True,
            'passwordPri': company.dte_password_certificado or '',
            'dteJson':     dte_obj,
        }
        _logger.info(
            'DTE FIRMA → POST %s | nit=%s | codigoGeneracion=%s | tipoDte=%s',
            url, payload['nit'],
            dte_obj.get('identificacion', {}).get('codigoGeneracion'),
            dte_obj.get('identificacion', {}).get('tipoDte'),
        )
        _logger.debug('DTE FIRMA → payload dteJson: %s', json.dumps(dte_obj, ensure_ascii=False))
        try:
            resp = requests.post(url, json=payload, timeout=30)
        except requests.ConnectionError as e:
            _logger.error('DTE FIRMA ← firmador no disponible en %s: %s', url, e)
            raise UserError('El firmador no está disponible en localhost:8113')
        except requests.Timeout:
            _logger.error('DTE FIRMA ← timeout')
            raise UserError('El firmador no respondió (timeout 30 s).')
        except Exception as e:
            _logger.error('DTE FIRMA ← error inesperado: %s', e)
            raise UserError(f'Error al conectar con el firmador: {e}')

        _logger.info('DTE FIRMA ← HTTP %s | body: %s', resp.status_code, resp.text)
        if not resp.ok:
            raise UserError(f'Error del firmador (HTTP {resp.status_code}):\n{resp.text}')

        data = resp.json()
        if data.get('status') != 'OK':
            raise UserError(f'El firmador rechazó el documento:\n{data}')

        return data['body']

    def _enviar_dte_mh(self, token, documento_firmado):
        """Envía el DTE firmado al MH, registra intento y actualiza estado."""
        self.ensure_one()
        company = self.company_id
        url = company.dte_url_recepcion or 'https://apitest.dtes.mh.gob.sv/fesv/recepciondte/'
        headers = {'Content-Type': 'application/json', 'Authorization': token}
        payload = {
            'ambiente':  '00',
            'idEnvio':   1,
            'version':   _DTE_VERSION.get(self.tipo_dte, 1),
            'tipoDte':   self.tipo_dte,
            'documento': documento_firmado,
        }

        # ── Contabilizar el intento ANTES de llamar al MH ─────────────────
        nuevo_intento = (self.dte_intentos_envio or 0) + 1
        self.write({
            'dte_intentos_envio': nuevo_intento,
            'dte_ultimo_envio':   fields.Datetime.now(),
            'estado_dte':         'enviado',
        })

        _logger.info(
            'DTE ENVÍO → POST %s | tipoDte=%s | codigoGeneracion=%s | intento=%s',
            url, self.tipo_dte, self.dte_codigo_generacion, nuevo_intento,
        )

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
        except requests.Timeout:
            _logger.error('DTE ENVÍO ← timeout (intento %s)', nuevo_intento)
            self.write({'estado_dte': 'pendiente'})
            raise UserError('El MH no respondió. El DTE quedó en estado Pendiente para reenvío.')
        except Exception as e:
            _logger.error('DTE ENVÍO ← error inesperado (intento %s): %s', nuevo_intento, e)
            self.write({'estado_dte': 'pendiente'})
            raise UserError(f'Error al enviar el DTE al MH: {e}')

        _logger.info('DTE ENVÍO ← HTTP %s | body: %s', resp.status_code, resp.text)

        if not resp.ok:
            self.write({'estado_dte': 'pendiente'})
            raise UserError(f'Error de recepción MH (HTTP {resp.status_code}):\n{resp.text}')

        data = resp.json()

        # ── Guardar respuesta raw del MH ──────────────────────────────────
        self.dte_respuesta_mh = json.dumps(data, ensure_ascii=False, indent=2)

        # ── CAMBIO CRÍTICO: Se mapea con la propiedad oficial 'status' que maneja el MH ──
        estado_mh = data.get('status')
        if estado_mh == 'PROCESADO':
            self.write({
                'dte_sello_recepcion':     data.get('selloRecibido', ''),
                'estado_dte':              'aceptado',
                'dte_fecha_procesamiento': data.get('fhProcesamiento', ''),
            })
            _logger.info(
                'DTE ENVÍO: %s PROCESADO | sello: %s | intentos: %s',
                self.dte_codigo_generacion, data.get('selloRecibido'), nuevo_intento,
            )
        elif estado_mh == 'RECHAZADO':
            observaciones = data.get('observaciones', [])
            self.write({
                'estado_dte':              'rechazado',
                'dte_descripcion_mensaje': data.get('descripcionMsg', ''),
                'dte_observaciones':       '\n'.join(observaciones) if observaciones else '',
            })
            _logger.warning(
                'DTE ENVÍO: %s RECHAZADO | msg: %s | obs: %s | intentos: %s',
                self.dte_codigo_generacion, data.get('descripcionMsg'),
                observaciones, nuevo_intento,
            )
        else:
            _logger.warning('DTE ENVÍO: estado desconocido del MH: %s', data)

        return data
    
    def _enviar_pdf_cliente(self):
        """
        Genera el PDF de la factura y lo envía por correo al cliente.
        Registra el intento en dte.mail.log para trazabilidad completa.
        Se llama automáticamente cuando el DTE queda en estado 'aceptado'.
        """
        self.ensure_one()
        intento_num = len(self.dte_mail_log_ids) + 1
        destinatario = (self.partner_id.email or '').strip()

        if not destinatario:
            _logger.warning(
                'DTE MAIL: factura %s sin correo de cliente — no se envía PDF',
                self.name,
            )
            self.env['dte.mail.log'].create({
                'move_id':       self.id,
                'destinatario':  '(sin correo)',
                'asunto':        'N/A',
                'exitoso':       False,
                'error':         'El cliente no tiene correo electrónico registrado.',
                'intento_numero': intento_num,
            })
            return

        # ── 1. Generar el PDF ──────────────────────────────────────────────
        try:
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                'account.action_account_original_vendor_bill',  # report externo de Odoo
                res_ids=self.ids,
            )
        except Exception:
            # Fallback: reporte genérico de factura de ventas
            try:
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    'account.action_report_original_vendor_bill',
                    res_ids=self.ids,
                )
            except Exception:
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    'account.report_invoice',
                    res_ids=self.ids,
                )

        # ── 2. Adjuntar el PDF como ir.attachment temporal ─────────────────
        nombre_pdf = f'Factura_{self.name.replace("/", "_")}.pdf'
        attachment = self.env['ir.attachment'].create({
            'name':     nombre_pdf,
            'type':     'binary',
            'datas':    base64.b64encode(pdf_content),
            'res_model': 'account.move',
            'res_id':    self.id,
        })

        # ── 3. Construir y enviar el correo ────────────────────────────────
        asunto = (
            f'Factura Electrónica {self.name} — {self.company_id.name}'
        )
        cuerpo = (f"""
            <p>Estimado/a <strong>{self.partner_id.name}</strong>,</p>
            <p>Adjunto encontrará su factura electrónica
               <strong>{self.name}</strong>
               emitida por <strong>{self.company_id.name}</strong>,
               con sello de recepción del Ministerio de Hacienda:
               <code>{self.dte_sello_recepcion}</code>.</p>
            <p>Gracias por su preferencia.</p>
        """)

        mail_values = {
            'subject':          asunto,
            'body_html':         cuerpo,
            'email_to':          destinatario,
            'email_from':         self.company_id.email or '',
            'author_id':          self.env.user.partner_id.id,
            'attachment_ids':     [(4, attachment.id)],
            'auto_delete':         True,
        }

        error_msg = None
        exitoso   = False
        try:
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.sudo().send()
            exitoso = True
            _logger.info(
                'DTE MAIL: PDF de %s enviado a %s (intento %s)',
                self.name, destinatario, intento_num,
            )
        except Exception as e:
            error_msg = str(e)
            _logger.error(
                'DTE MAIL: fallo al enviar PDF de %s a %s: %s',
                self.name, destinatario, e,
            )

        # ── 4. Registrar el intento en el log ─────────────────────────────
        self.env['dte.mail.log'].create({
            'move_id':        self.id,
            'destinatario':   destinatario,
            'asunto':         asunto,
            'cuerpo':         cuerpo,
            'adjunto_nombre': nombre_pdf,
            'exitoso':        exitoso,
            'error':          error_msg,
            'intento_numero': intento_num,
        })

    def action_enviar_dte(self):
        """Ejecuta los 3 pasos del envío DTE y envía el PDF al cliente si es aceptado."""
        self.ensure_one()
        company = self.company_id

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

        self._validar_schema_dte()

        try:
            token = self._obtener_token_mh()
        except UserError:
            self.estado_dte = 'pendiente'
            self.env.cr.commit()
            raise

        try:
            documento_firmado = self._firmar_dte(token)
        except UserError:
            self.estado_dte = 'pendiente'
            self.env.cr.commit()
            raise

        try:
            self._enviar_dte_mh(token, documento_firmado)
        except UserError:
            self.env.cr.commit()
            raise

        # ── Enviar PDF automáticamente si fue aceptado ────────────────────
        if self.estado_dte == 'aceptado':
            try:
                self._enviar_pdf_cliente()
            except Exception as e:
                # El envío de correo no debe revertir el DTE ya aceptado
                _logger.error('DTE MAIL: error no crítico al enviar PDF: %s', e)

        self.env.cr.commit()

    # ── Override action_post ───────────────────────────────────────────────────

    def action_post(self):
        res = super().action_post()

        facturas = self.filtered(lambda m: m.move_type in ('out_invoice', 'out_refund'))
        for move in facturas:
            if not move.tipo_dte:
                move.tipo_dte = '05' if move.move_type == 'out_refund' else '01'
            if not move.dte_codigo_generacion:
                move.dte_codigo_generacion = move._generar_codigo_generacion()
            if not move.dte_numero_control:
                move.dte_numero_control = move._generar_numero_control()
            move.dte_json = move._serializar_dte()
            move.estado_dte = 'pendiente'

        return res
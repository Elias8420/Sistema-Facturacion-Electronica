import uuid
import json

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    # ── Campos DTE ─────────────────────────────────────────────────────────────

    dte_codigo_generacion = fields.Char(
        string='Código de Generación',
        readonly=True,
        copy=False,
        help='UUID v4 generado automáticamente al confirmar la factura.',
    )
    dte_numero_control = fields.Char(
        string='Número de Control',
        readonly=True,
        copy=False,
        help='Número de control secuencial asignado por el sistema.',
    )
    dte_sello_recepcion = fields.Char(
        string='Sello de Recepción',
        readonly=True,
        copy=False,
        help='Sello devuelto por el Ministerio de Hacienda al aceptar el DTE.',
    )
    dte_json = fields.Text(
        string='JSON DTE',
        readonly=True,
        copy=False,
        help='Representación JSON del documento tributario electrónico.',
    )
    tipo_dte = fields.Selection(
        selection=[
            ('01', 'Factura de Consumidor Final'),
            ('03', 'Comprobante de Crédito Fiscal'),
            ('05', 'Nota de Crédito'),
        ],
        string='Tipo DTE',
        copy=False,
    )
    estado_dte = fields.Selection(
        selection=[
            ('borrador',  'Borrador'),
            ('enviado',   'Enviado'),
            ('aceptado',  'Aceptado'),
            ('rechazado', 'Rechazado'),
            ('pendiente', 'Pendiente de Envío'),
        ],
        string='Estado DTE',
        default='borrador',
        copy=False,
    )

    # ── Métodos privados ───────────────────────────────────────────────────────

    def _generar_codigo_generacion(self):
        """Genera un UUID v4 en mayúsculas como Código de Generación."""
        return str(uuid.uuid4()).upper()

    def _generar_numero_control(self):
        """
        Genera el Número de Control con formato oficial MH El Salvador:
        DTE-{tipoDte}-{establecimiento}{puntoVenta}-{correlativo15dígitos}
        Ejemplo: DTE-01-S048P001-000000000000001
        """
        self.ensure_one()
        tipo  = self.tipo_dte or '01'
        estab = (self.company_id.dte_establecimiento or 'S001').upper()
        pv    = (self.company_id.dte_punto_venta     or 'P001').upper()

        correlativo = self.env['ir.sequence'].next_by_code(
            f'dte.sv.control.{tipo}'
        ) or '000000000000001'

        return f'DTE-{tipo}-{estab}{pv}-{correlativo}'

    def _serializar_dte(self):
        """Construye el JSON DTE con la estructura básica del MH El Salvador."""
        self.ensure_one()

        cuerpo = []
        for linea in self.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product'
        ):
            cuerpo.append({
                'descripcion':    linea.name,
                'cantidad':       linea.quantity,
                'precioUni':      linea.price_unit,
                'montoDescu':     linea.discount,
                'ventaNoSuj':     0.0,
                'ventaExenta':    0.0,
                'ventaGravada':   round(linea.price_subtotal, 2),
                'tributos':       [],
                'psv':            0.0,
                'noGravado':      0.0,
                'codigoTributo':  None,
            })

        dte = {
            'identificacion': {
                'version':          1,
                'ambiente':         '00',   # 00=pruebas, 01=producción
                'tipoDte':          self.tipo_dte,
                'numeroControl':    self.dte_numero_control or '',
                'codigoGeneracion': self.dte_codigo_generacion,
                'tipoModelo':       1,
                'tipoOperacion':    1,
                'tipoContingencia': None,
                'motivoContin':     None,
                'fecEmi':           str(self.invoice_date or fields.Date.today()),
                'horEmi':           fields.Datetime.now().strftime('%H:%M:%S'),
                'tipoMoneda':       'USD',
            },
            'emisor': {
                'nit':          self.company_id.vat or '',
                'nrc':          '',
                'nombre':       self.company_id.name,
                'codActividad': '',
                'descActividad': '',
                'nombreComercial': self.company_id.name,
                'tipoEstablecimiento': '01',
                'direccion': {
                    'departamento': '',
                    'municipio':    '',
                    'complemento':  self.company_id.street or '',
                },
                'telefono':     self.company_id.phone or '',
                'correo':       self.company_id.email or '',
            },
            'receptor': {
                'nit':          self.partner_id.vat or '',
                'nombre':       self.partner_id.name,
                'codActividad': '',
                'descActividad': '',
                'direccion': {
                    'departamento': '',
                    'municipio':    '',
                    'complemento':  self.partner_id.street or '',
                },
                'telefono':     self.partner_id.phone or '',
                'correo':       self.partner_id.email or '',
            },
            'cuerpoDocumento': cuerpo,
            'resumen': {
                'totalNoSuj':           0.0,
                'totalExenta':          0.0,
                'totalGravada':         round(self.amount_untaxed, 2),
                'subTotalVentas':       round(self.amount_untaxed, 2),
                'descuNoSuj':           0.0,
                'descuExenta':          0.0,
                'descuGravada':         0.0,
                'totalDescu':           0.0,
                'tributos':             [],
                'subTotal':             round(self.amount_untaxed, 2),
                'ivaPerci1':            0.0,
                'ivaRete1':             0.0,
                'reteRenta':            0.0,
                'montoTotalOperacion':  round(self.amount_total, 2),
                'totalLetras':          '',
                'totalIva':             round(self.amount_tax, 2),
                'saldoFavor':           0.0,
                'condicionOperacion':   1,
                'pagos':                [],
                'numPagoElectronico':   '',
            },
        }

        return json.dumps(dte, ensure_ascii=False, indent=2)

    # ── Override action_post ───────────────────────────────────────────────────

    def action_post(self):
        res = super().action_post()

        facturas = self.filtered(
            lambda m: m.move_type in ('out_invoice', 'out_refund')
        )
        for move in facturas:
            # 1. Asignar tipo_dte según move_type si no fue elegido manualmente
            if not move.tipo_dte:
                move.tipo_dte = '05' if move.move_type == 'out_refund' else '01'

            # 2. Generar Código de Generación (UUID v4)
            if not move.dte_codigo_generacion:
                move.dte_codigo_generacion = move._generar_codigo_generacion()

            # 3. Generar Número de Control con formato DTE-{tipo}-{estab}{pv}-{correlativo}
            if not move.dte_numero_control:
                move.dte_numero_control = move._generar_numero_control()

            # 4. Serializar el DTE a JSON
            move.dte_json = move._serializar_dte()

            # 5. Marcar como pendiente de envío al MH
            move.estado_dte = 'pendiente'

        return res

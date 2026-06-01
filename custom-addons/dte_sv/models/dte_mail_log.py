from odoo import models, fields


class DteMailLog(models.Model):
    _name        = 'dte.mail.log'
    _description = 'Historial de correos DTE'
    _order       = 'fecha_envio desc'

    # ── Relación con la factura ──────────────────────────────────────────────
    move_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # ── Datos del envío ─────────────────────────────────────────────────────
    fecha_envio = fields.Datetime(
        string='Fecha de Envío',
        default=fields.Datetime.now,
        readonly=True,
    )
    destinatario = fields.Char(
        string='Destinatario',
        readonly=True,
        help='Correo electrónico al que se envió la factura.',
    )
    asunto = fields.Char(
        string='Asunto',
        readonly=True,
    )
    cuerpo = fields.Html(
        string='Cuerpo del mensaje',
        readonly=True,
    )
    adjunto_nombre = fields.Char(
        string='Nombre del adjunto',
        readonly=True,
    )

    # ── Resultado del envío ──────────────────────────────────────────────────
    exitoso = fields.Boolean(
        string='Enviado con éxito',
        default=False,
        readonly=True,
    )
    error = fields.Text(
        string='Error',
        readonly=True,
        help='Detalle del error si el envío falló.',
    )
    intento_numero = fields.Integer(
        string='Nº de Intento',
        default=1,
        readonly=True,
    )
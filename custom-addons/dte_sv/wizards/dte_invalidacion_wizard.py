from odoo import models, fields, api
from odoo.exceptions import UserError


class DteInvalidacionWizard(models.TransientModel):
    _name = 'dte.invalidacion.wizard'
    _description = 'Wizard de Invalidación de DTE'

    # ── Factura relacionada ────────────────────────────────────────────────────

    move_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
        readonly=True,
    )

    # ── Campos informativos (solo lectura) ────────────────────────────────────

    tipo_dte = fields.Selection(
        related='move_id.tipo_dte',
        string='Tipo DTE',
        readonly=True,
    )
    numero_control = fields.Char(
        related='move_id.dte_numero_control',
        string='Número de Control',
        readonly=True,
    )
    codigo_generacion_dte = fields.Char(
        related='move_id.dte_codigo_generacion',
        string='Código de Generación DTE',
        readonly=True,
    )

    # ── Datos del motivo ───────────────────────────────────────────────────────

    tipo_anulacion = fields.Selection(
        selection=[
            ('1', 'Anulación con reemplazo (requiere código del DTE sustituto)'),
            ('2', 'Anulación sin reemplazo'),
        ],
        string='Tipo de Anulación',
        required=True,
        default='2',
    )
    motivo_anulacion = fields.Char(
        string='Motivo de Anulación',
        size=200,
        help='Descripción opcional del motivo de anulación.',
    )

    # ── Datos del responsable ──────────────────────────────────────────────────

    nombre_responsable = fields.Char(
        string='Nombre del Responsable',
        required=True,
        size=100,
        help='Persona que realiza el evento de invalidación.',
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
        default='13',
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
        help='Persona que solicita el evento de invalidación.',
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
        default='13',
    )
    num_doc_solicita = fields.Char(
        string='Número Doc. Solicitante',
        required=True,
        size=20,
    )

    # ── Documento sustituto (opcional) ────────────────────────────────────────

    tiene_sustituto = fields.Boolean(
        string='¿Existe documento sustituto?',
        default=False,
    )
    codigo_generacion_r = fields.Char(
        string='Código Generación Documento Sustituto',
        size=36,
        help='UUID del DTE que reemplaza al invalidado. Dejar vacío si no aplica.',
    )

    # ── Validación en tiempo real ──────────────────────────────────────────────

    @api.constrains('codigo_generacion_r')
    def _check_codigo_generacion_r(self):
        import re
        patron = r'^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$'
        for rec in self:
            if rec.codigo_generacion_r and not re.match(patron, rec.codigo_generacion_r.upper()):
                raise UserError(
                    'El Código de Generación del documento sustituto debe ser un UUID válido '
                    '(formato: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX).'
                )

    # ── Acción de confirmación ────────────────────────────────────────────────

    def action_confirmar_invalidacion(self):
        self.ensure_one()

        if self.tipo_anulacion == '1' and not (self.codigo_generacion_r or '').strip():
            raise UserError(
                'El tipo "Anulación con reemplazo" requiere el Código de Generación del DTE sustituto.'
            )

        # tipo 2: nunca se envía código de reemplazo al MH
        codigo_r = None
        if self.tipo_anulacion == '1' and (self.codigo_generacion_r or '').strip():
            codigo_r = self.codigo_generacion_r.strip().upper()

        invalidacion = self.env['dte.invalidacion'].create({
            'move_id':             self.move_id.id,
            'tipo_anulacion':      self.tipo_anulacion,
            'motivo_anulacion':    (self.motivo_anulacion or '').strip() or False,
            'nombre_responsable':  self.nombre_responsable,
            'tip_doc_responsable': self.tip_doc_responsable,
            'num_doc_responsable': self.num_doc_responsable,
            'nombre_solicita':     self.nombre_solicita,
            'tip_doc_solicita':    self.tip_doc_solicita,
            'num_doc_solicita':    self.num_doc_solicita,
            'codigo_generacion_r': codigo_r,
        })

        invalidacion.action_invalidar_dte()

        # Después de invalidar, abrir el registro del evento para que el usuario
        # vea el resultado (sello, estado, etc.)
        return {
            'type':      'ir.actions.act_window',
            'name':      'Evento de Invalidación',
            'res_model': 'dte.invalidacion',
            'res_id':    invalidacion.id,
            'view_mode': 'form',
            'target':    'current',
        }

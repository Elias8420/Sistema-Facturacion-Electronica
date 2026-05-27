from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    dte_establecimiento = fields.Char(
        string='Código de Establecimiento',
        default='S001',
        help='Código del establecimiento asignado por Hacienda. Ejemplo: S048',
    )
    dte_punto_venta = fields.Char(
        string='Código de Punto de Venta',
        default='P001',
        help='Código del punto de venta o caja. Ejemplo: P001',
    )

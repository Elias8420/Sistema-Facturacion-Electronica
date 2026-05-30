from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    dte_nrc = fields.Char(
        string='NRC',
        help='Número de Registro de Contribuyente del receptor (requerido en CCF).',
    )
    dte_cod_actividad = fields.Char(
        string='Código Actividad Económica',
        help='Código de actividad económica del receptor según catálogo MH.',
    )
    dte_desc_actividad = fields.Char(
        string='Descripción Actividad Económica',
        help='Descripción de la actividad económica del receptor.',
    )
    dte_departamento = fields.Char(
        string='Departamento',
        size=2,
        help='Código de departamento según catálogo MH (ej. 02 = Santa Ana, 06 = San Salvador).',
    )
    dte_municipio = fields.Char(
        string='Municipio',
        size=2,
        help='Código de municipio según catálogo MH (ej. 15).',
    )
    dte_complemento = fields.Char(
        string='Complemento (Dirección)',
        help='Dirección detallada del receptor tal como debe aparecer en el DTE.',
    )

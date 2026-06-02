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

    # ── Datos del Emisor DTE ──────────────────────────────────────────────────

    dte_nrc = fields.Char(
        string='NRC Emisor',
        help='Número de Registro de Contribuyente del emisor.',
    )
    dte_nombre_comercial = fields.Char(
        string='Nombre Comercial',
        help='Nombre comercial del emisor. Si está vacío se usa el nombre legal de la empresa.',
    )
    dte_cod_actividad = fields.Char(
        string='Código de Actividad',
        help='Código de actividad económica del emisor según catálogo del MH.',
    )
    dte_desc_actividad = fields.Char(
        string='Descripción de Actividad',
        help='Descripción de la actividad económica del emisor.',
    )
    dte_tipo_establecimiento = fields.Char(
        string='Tipo de Establecimiento',
        default='01',
        help='Tipo de establecimiento según catálogo del MH. Ej: 01=Casa Matriz.',
    )
    dte_nom_establecimiento = fields.Char(
        string='Nombre del Establecimiento',
        help='Nombre de la sucursal/establecimiento. Requerido en eventos de invalidación MH.',
    )
    dte_departamento = fields.Char(
        string='Departamento',
        help='Código de departamento según catálogo del MH. Ej: 06=San Salvador.',
    )
    dte_municipio = fields.Char(
        string='Municipio',
        help='Código de municipio según catálogo del MH. Ej: 23=San Salvador.',
    )
    dte_distrito = fields.Char(
        string='Distrito',
        help='Código de distrito según catálogo del MH (requerido en la dirección del DTE).',
    )

    # ── Credenciales y URLs del MH ─────────────────────────────────────────────

    dte_nit = fields.Char(
        string='NIT Emisor',
        help='NIT del emisor registrado ante el Ministerio de Hacienda.',
    )
    dte_password_mh = fields.Char(
        string='Contraseña MH',
        help='Contraseña de acceso al portal del Ministerio de Hacienda (paso de autenticación).',
    )
    dte_password_certificado = fields.Char(
        string='Contraseña Certificado',
        help='Clave privada del certificado .p12 usada por el firmador local.',
    )
    dte_url_firmador = fields.Char(
        string='URL Firmador',
        default='http://localhost:8113',
        help='URL base del servicio firmador Java local.',
    )
    dte_url_auth = fields.Char(
        string='URL Autenticación MH',
        default='https://apitest.dtes.mh.gob.sv/seguridad/auth',
        help='Endpoint de autenticación del Ministerio de Hacienda.',
    )
    dte_url_recepcion = fields.Char(
        string='URL Recepción MH',
        default='https://apitest.dtes.mh.gob.sv/fesv/recepciondte/',
        help='Endpoint de recepción de DTEs del Ministerio de Hacienda.',
    )
    dte_url_anulacion = fields.Char(
        string='URL Anulación MH',
        default='https://apitest.dtes.mh.gob.sv/fesv/anulardte/',
        help='Endpoint de invalidación/anulación de DTEs del Ministerio de Hacienda.',
    )

    # ── Token (gestionado automáticamente) ────────────────────────────────────

    dte_token = fields.Char(
        string='Token MH',
        readonly=True,
        help='Token Bearer devuelto por el MH tras la autenticación. Se actualiza automáticamente.',
    )
    dte_token_expiry = fields.Datetime(
        string='Expiración Token',
        readonly=True,
    )

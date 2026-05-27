{
    'name': 'Facturación Electrónica SV',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Documentos Tributarios Electrónicos (DTE) para El Salvador',
    'description': """
        Módulo para la generación y gestión de Documentos Tributarios Electrónicos (DTE)
        según las especificaciones del Ministerio de Hacienda de El Salvador.

        Funcionalidades:
        - Generación automática de Código de Generación (UUID v4) al confirmar factura
        - Asignación de Número de Control secuencial
        - Serialización del DTE en formato JSON (estructura MH)
        - Gestión de estados: Borrador → Pendiente → Enviado → Aceptado/Rechazado
        - Soporte para Factura Consumidor Final (01), CCF (03) y Nota de Crédito (05)
    """,
    'author': 'Equipo DTE SV',
    'depends': ['account', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/dte_sequence.xml',
        'views/res_company_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

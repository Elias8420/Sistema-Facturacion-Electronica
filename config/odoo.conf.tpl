[options]
; ── Conexión a PostgreSQL ──────────────────────────────────────────────────────
; Estos valores deben coincidir con POSTGRES_USER y POSTGRES_PASSWORD del .env
db_host = db
db_port = 5432
db_user = ${POSTGRES_USER}
db_password = ${POSTGRES_PASSWORD}
db_maxconn = 64

; ── Módulos ────────────────────────────────────────────────────────────────────
; /mnt/extra-addons → carpeta custom-addons/ montada en el contenedor
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons

; ── Seguridad ──────────────────────────────────────────────────────────────────
; Debe coincidir con ODOO_ADMIN_PASSWD del .env
admin_passwd = ${ODOO_ADMIN_PASSWD}

; ── Logging ────────────────────────────────────────────────────────────────────
log_level = info

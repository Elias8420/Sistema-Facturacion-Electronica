# Sistema de Facturación Electrónica — Farmacia DTE SV

Odoo 17 Community dockerizado con módulo personalizado `dte_sv` para facturación
electrónica salvadoreña.

---

## Estructura del proyecto

```
.
├── docker-compose.yml        # Orquestación de contenedores
├── .env                      # Variables de entorno (no subir a git)
├── config/
│   └── odoo.conf             # Configuración de Odoo
├── custom-addons/
│   └── dte_sv/               # Módulo de facturación electrónica (aquí va el código)
└── README.md
```

---

## Configuración inicial

### 1. Ajustar credenciales

Edita `.env` con tus propias contraseñas:

```env
POSTGRES_DB=farmacia_db
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_password_segura
ODOO_ADMIN_PASSWD=tu_master_password
```


## Comandos principales

### Levantar todos los contenedores

```bash
docker compose up -d
```

Odoo quedará disponible en `http://<IP>:8069`

## Ejecutar migracion inicial 

```bash
docker compose exec odoo odoo -i base -d farmacia_db --stop-after-init
```

### Ver logs en tiempo real

```bash
# Todos los servicios
docker compose logs -f

# Solo Odoo
docker compose logs -f odoo

# Solo la base de datos
docker compose logs -f db
```

### Detener los contenedores

```bash
docker compose down
```

> Los datos persisten en los volúmenes Docker (`postgres_data` y `odoo_filestore`).
> Para eliminar también los datos: `docker compose down -v`

### Reiniciar solo Odoo

```bash
docker compose restart odoo
```

### Entrar al contenedor de Odoo

```bash
docker compose exec odoo bash
```

### Actualizar un módulo personalizado

```bash
# Reemplaza "nombre_bd" con el nombre de tu base de datos en Odoo
docker compose exec odoo odoo -u dte_sv -d nombre_bd --stop-after-init
```

---

## Desarrollo del módulo dte_sv

1. Coloca el código del módulo en `custom-addons/dte_sv/`
2. El contenedor monta esa carpeta en `/mnt/extra-addons`
3. Reinicia Odoo y actualiza el módulo:

```bash
docker compose restart odoo
docker compose exec odoo odoo -u dte_sv -d nombre_bd --stop-after-init
```

4. Para que aparezca en la lista de apps, activa el **modo desarrollador** en Odoo y
   haz clic en *Actualizar lista de apps*.

---

## Flujo de trabajo con GitHub

```bash
# Clonar el repo en el VPS
git clone https://github.com/<usuario>/<repo>.git
cd <repo>

# Editar .env con las credenciales del VPS
nano .env

# Levantar
docker compose up -d
```

Para actualizar el módulo desde GitHub:

```bash
git pull
docker compose exec odoo odoo -u dte_sv -d nombre_bd --stop-after-init
```

---

## Volúmenes persistentes

| Volumen          | Contenido                          |
|------------------|------------------------------------|
| `postgres_data`  | Datos de PostgreSQL                |
| `odoo_filestore` | Archivos subidos a Odoo (PDFs, etc.)|

---

## Notas

- El servicio `odoo` no arranca hasta que `db` pase su healthcheck (`pg_isready`).
- `restart: always` garantiza que ambos servicios se reinicien tras un reboot del VPS.
- Sin Nginx ni SSL en esta etapa; acceso directo por puerto `8069`.

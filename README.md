# Sistema de Facturación Electrónica — Farmacia DTE SV

Odoo 17 Community dockerizado con módulo personalizado `dte_sv` para facturación
electrónica salvadoreña según estándares del Ministerio de Hacienda de El Salvador.

---

## 📚 Documentación

**IMPORTANTE**: Consulta la documentación completa en [`docs/`](./docs/INDEX.md)

### Documentos Principales

| Documento | Propósito | Tiempo |
|-----------|-----------|--------|
| **[Arquitectura Inicial](./docs/arquitectura-inicial.md)** | Entender el sistema completo | 10-15 min |
| **[Documentación Técnica](./docs/documentacion-tecnica.md)** | Detalles de implementación | 20-30 min |
| **[Guía de Despliegue](./docs/despliegue.md)** | Instalación y configuración | 15-20 min |
| **[Diagramas](./docs/diagramas/)** | Visualizar arquitectura | 5 min |

---

## Estructura del proyecto

```
Sistema-Facturacion-Electronica/
├── docs/                          ← DOCUMENTACIÓN TÉCNICA
│   ├── INDEX.md                   ← Punto de entrada
│   ├── arquitectura-inicial.md    ← Visión general
│   ├── documentacion-tecnica.md   ← Para desarrolladores
│   ├── despliegue.md              ← Guía instalación
│   └── diagramas/
│       ├── README.md
│       ├── arquitectura-general.png
│       ├── flujo-dte.png
│       └── componentes.png
├── docker-compose.yml             # Orquestación de contenedores
├── Dockerfile                     # Imagen personalizada Odoo
├── .env.example                   # Variables de entorno (copiar a .env)
├── config/
│   ├── odoo.conf.tpl              # Plantilla configuración Odoo
│   └── init.sh                    # Script inicialización
├── custom-addons/
│   └── dte_sv/                    # Módulo de facturación electrónica
│       ├── models/
│       ├── views/
│       ├── security/
│       ├── data/
│       ├── static/schemas/        # JSON schemas MH
│       └── __manifest__.py
├── tests/                         # Test suite
├── seed_data.py                   # Datos iniciales
├── Jenkinsfile                    # CI/CD pipeline
├── .gitignore
└── README.md
```

---

## ⚡ Inicio Rápido (3 pasos)

### 1. Clonar y configurar

```bash
git clone https://github.com/tu-org/Sistema-Facturacion-Electronica.git
cd Sistema-Facturacion-Electronica

# Crear archivo de configuración
cp .env.example .env
# Editar .env con tus credenciales
```

### 2. Levantar contenedores

```bash
docker compose build
docker compose up -d
```

### 3. Instalar módulo

1. Acceder: http://localhost:8069
2. Ir a: Aplicaciones → Buscar "Facturación Electrónica SV"
3. Click "Instalar"

**Para pasos detallados**, consulta [Guía de Despliegue](./docs/despliegue.md#3-configurar-odoo)

---

## 📋 Configuración inicial

### Variables de Entorno (.env)

Crea archivo `.env` en la raíz (copiar desde `.env.example`):

```env
# PostgreSQL
POSTGRES_DB=farmacia_db
POSTGRES_USER=odoo_user
POSTGRES_PASSWORD=tu_password_fuerte_aqui

# Odoo Master Password
ODOO_ADMIN_PASSWD=tu_admin_password_aqui
```

⚠️ **IMPORTANTE**: 
- **NO** subir `.env` a Git (está en `.gitignore`)
- Usar contraseñas **fuertes** en producción
- Ver [Seguridad en Producción](./docs/despliegue.md#11-seguridad-en-producción)


### Configurar Empresa para DTE

1. Ir a: **Ajustes** → **Empresas**
2. Rellenar sección **"Facturación Electrónica DTE"** con:
   - NIT Emisor
   - Contraseña Ministerio de Hacienda
   - Contraseña Certificado
   - URLs de MH

**Para detalles completos**, ver [Sección 4 de Despliegue](./docs/despliegue.md#4-configurar-empresa-para-dte)

---

## 🔧 Comandos Comunes

### Levantar contenedores

```bash
docker compose up -d
```

Odoo estará disponible en: **http://localhost:8069**

### Ver logs en tiempo real

```bash
# Todos los servicios
docker compose logs -f

# Solo Odoo
docker compose logs -f odoo

# Solo base de datos
docker compose logs -f db
```

### Detener contenedores

```bash
docker compose down
```

Los datos persisten en volúmenes (`postgres_data`, `odoo_filestore`).  
Para eliminar todo: `docker compose down -v` ⚠️

### Actualizar módulo DTE_SV

```bash
docker compose restart odoo
docker compose exec odoo odoo -u dte_sv -d farmacia_db --stop-after-init
```

### Entrar al contenedor de Odoo

```bash
docker compose exec odoo bash
```

### Ver estado de volúmenes

```bash
docker volume ls
docker volume inspect postgres_data
```

---

## 🏗️ Desarrollo del Módulo DTE_SV

### Estructura

```
custom-addons/dte_sv/
├── models/              # Lógica de negocio
│   ├── account_move.py  # Generación de DTEs
│   ├── res_company.py   # Configuración emisor
│   └── res_partner.py   # Datos receptor
├── views/               # Interfaces XML
├── security/            # Control de acceso
├── data/                # Secuencias iniciales
├── static/schemas/      # JSON schemas MH
└── __manifest__.py      # Metadata módulo
```

### Flujo de cambios

1. Editar código en `custom-addons/dte_sv/`
2. El contenedor monta esa carpeta automáticamente
3. Reiniciar Odoo
4. Actualizar módulo desde interface de Odoo

```bash
docker compose restart odoo
# Ir a Odoo → Aplicaciones → Buscar "Facturación Electrónica SV" → Actualizar
```

---

## 📊 Volúmenes Persistentes

| Volumen | Contenido | Ubicación |
|---------|-----------|-----------|
| `postgres_data` | Base de datos PostgreSQL | `/var/lib/postgresql/data` |
| `odoo_filestore` | Archivos Odoo (PDFs, etc.) | `/var/lib/odoo` |

Ver ubicación física:
```bash
docker volume inspect postgres_data
```

---

## 🔄 Flujo de Trabajo con Git

```bash
# Clonar repositorio
git clone https://github.com/tu-org/Sistema-Facturacion-Electronica.git
cd Sistema-Facturacion-Electronica

# Crear rama de desarrollo
git checkout -b feature/mi-feature

# Realizar cambios
# ...

# Hacer commit
git add .
git commit -m "feat: descripción de cambios"

# Enviar cambios
git push origin feature/mi-feature

# Crear Pull Request en GitHub
```

### Actualizar desde GitHub (en servidor)

```bash
git pull origin develop
docker compose restart odoo
docker compose exec odoo odoo -u dte_sv -d farmacia_db --stop-after-init
```

---

## 🚨 Troubleshooting

### Odoo no inicia

```bash
docker compose logs odoo | tail -20
docker compose restart odoo
```

### Error de conexión a base de datos

```bash
docker compose ps db
docker compose restart db
docker compose restart odoo
```

### Error de validación DTE

Ver logs: `docker compose logs odoo | grep "schema"`

Verificar que todos los campos requeridos estén rellenos en la factura.

**Para más problemas**, consulta [Troubleshooting completo](./docs/despliegue.md#9-troubleshooting)

---

## 📝 CI/CD Pipeline

Este proyecto incluye `Jenkinsfile` para automatizar:
- Build de imagen Docker
- Pruebas unitarias
- Deploy a producción

Configurar con Jenkins según tus requisitos.

---

## 🔐 Seguridad

### En Desarrollo
- Contraseñas de ejemplo en `.env.example`
- Modo de prueba (apitest.dtes.mh.gob.sv)

### En Producción
- Cambiar todas las contraseñas
- Habilitar SSL/TLS (Nginx proxy)
- Usar variables de entorno seguras
- Configurar cortafuegos
- Habilitar backups automáticos

**Checklist completo**: [Seguridad en Producción](./docs/despliegue.md#11-seguridad-en-producción)

---

## 📚 Recursos

- **Documentación Odoo**: https://www.odoo.com/documentation/
- **Ministerio de Hacienda SV**: https://www.hacienda.gob.sv/
- **Especificaciones DTE**: https://www.hacienda.gob.sv/
- **Documentación del Proyecto**: [docs/](./docs/INDEX.md)

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama: `git checkout -b feature/nombre`
3. Hacer cambios y commit
4. Push y crear Pull Request

---

## 📞 Soporte

- **Problemas técnicos**: Ver [Troubleshooting](./docs/despliegue.md#9-troubleshooting)
- **Preguntas de Odoo**: https://www.odoo.com/
- **Dudas sobre DTE**: Contacta a Ministerio de Hacienda

---

**Última actualización**: 2026-05-31  
**Versión**: Odoo 17.0 | Módulo DTE_SV 1.0.0

# Guía de Despliegue - Sistema DTE SV

## Requisitos Previos

### Hardware Mínimo
- **CPU**: 2 cores
- **RAM**: 2GB
- **Disco**: 10GB (datos)

### Software Requerido
- Docker >= 20.10
- Docker Compose >= 1.29
- Git

### Credenciales (Ministerio de Hacienda)
- NIT registrado ante MH
- Usuario/contraseña portal MH
- Certificado digital (.p12 con clave privada)

## 1. Preparación del Entorno

### 1.1 Clonar el Repositorio

```bash
git clone https://github.com/tu-org/Sistema-Facturacion-Electronica.git
cd Sistema-Facturacion-Electronica
```

### 1.2 Configurar Variables de Entorno

**Crear archivo `.env` en la raíz**:

```bash
# PostgreSQL
POSTGRES_DB=farmacia_db
POSTGRES_USER=odoo_user
POSTGRES_PASSWORD=tu_password_fuerte_aqui

# Odoo Master Password
ODOO_ADMIN_PASSWD=tu_admin_password_aqui
```

⚠️ **Importante**: 
- No subir `.env` a Git (está en `.gitignore`)
- Usar contraseñas fuertes (>12 caracteres, caracteres especiales)
- En producción, usar variables de entorno del servidor

### 1.3 Configurar Certificado Digital

**Ubicación**: El servidor local con el Firmador Java necesita acceso al certificado

```bash
# Copiar certificado a servidor del firmador
# Ruta típica: /var/lib/firmador/certs/emisor.p12
cp tu_certificado.p12 /ruta/firmador/certs/
```

**Nota**: El certificado NO debe estar en este repositorio (es sensible)

## 2. Iniciar Contenedores

### 2.1 Construir Imagen Personalizada de Odoo

```bash
docker compose build
```

Esto:
- Descarga imagen base Odoo 17
- Copia módulo `dte_sv` a `/mnt/extra-addons/dte_sv`
- Instala dependencias Python: `jsonschema`, `num2words`, `requests`

### 2.2 Levantar Servicios

```bash
docker compose up -d
```

**Verificar estado**:

```bash
docker compose ps
```

**Salida esperada**:
```
NAME       STATUS              PORTS
db         Up 2 seconds        5432/tcp
odoo       Up 1 second         8069/tcp
```

### 2.3 Esperar inicialización

```bash
# Ver logs de Odoo
docker compose logs -f odoo

# Esperar hasta ver: "Odoo server is running"
```

**Tiempo típico**: 30-60 segundos

## 3. Configurar Odoo

### 3.1 Acceder a Odoo

Abrir navegador: **http://localhost:8069**

**Credenciales iniciales**:
- Usuario: `admin`
- Contraseña: `admin` (cambiar en producción)

### 3.2 Crear Base de Datos (si no existe)

1. Llenar formulario:
   - DB Name: `farmacia_db` (coincidir con POSTGRES_DB)
   - Master Password: (la de ODOO_ADMIN_PASSWD)
2. Seleccionar idioma: **Spanish**
3. Click "Create Database"

### 3.3 Instalar Módulo DTE_SV

1. Ir a: **Aplicaciones** (Apps)
2. Click en "Actualizar lista de apps"
3. Buscar: **"Facturación Electrónica SV"**
4. Click "Instalar"

**Verifica que se instalen dependencias**:
- `account`
- `sale_management`

### 3.4 Activar Modo Desarrollador (Recomendado)

1. Ir a: **Ajustes** → **Técnico** → **Activar Modo Desarrollador**
2. Ahora verás campos técnicos en formularios

## 4. Configurar Empresa para DTE

### 4.1 Acceder a Configuración de Empresa

1. **Ajustes** → **Empresas** → Seleccionar tu empresa
2. Scroll hasta sección: **"Facturación Electrónica DTE"**

### 4.2 Rellenar Datos del Emisor

```
┌─────────────────────────────────────────┐
│ IDENTIFICACIÓN ANTE MH                  │
├─────────────────────────────────────────┤
│ NIT Emisor               │ 06150000000 │
│ NRC Emisor               │ 123456-7    │
│ Nombre Comercial         │ Farmacia XY │
│ Código de Establecimiento│ S001        │
│ Código de Punto Venta    │ P001        │
│ Tipo de Establecimiento  │ 01          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ACTIVIDAD ECONÓMICA                     │
├─────────────────────────────────────────┤
│ Código Actividad         │ 6210        │
│ Descripción Actividad    │ Farmacias..  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ LOCALIZACIÓN                            │
├─────────────────────────────────────────┤
│ Departamento             │ 06          │ (San Salvador)
│ Municipio                │ 23          │ (San Salvador)
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ CREDENCIALES Y CONEXIÓN                 │
├─────────────────────────────────────────┤
│ Contraseña MH            │ ••••••••    │
│ Contraseña Certificado   │ ••••••••    │
│ URL Autenticación MH     │ (default)   │
│ URL Recepción MH         │ (default)   │
│ URL Firmador             │ (default)   │
└─────────────────────────────────────────┘
```

**Catalógos de referencia**:
- [Departamentos MH](https://www.hacienda.gob.sv/)
- [Municipios por Depto](https://www.hacienda.gob.sv/)
- [Códigos Actividad](https://www.hacienda.gob.sv/)

### 4.3 Guardar

Click "Guardar"

## 5. Configurar Clientes (Partners)

Para facturas tipo CCF (03) o Notas de Crédito, rellenar datos del cliente:

1. **Contactos** → Seleccionar cliente
2. Scroll a sección **"DTE Emisión"**

```
NRC Cliente              │ (opcional)
Departamento             │ 06
Municipio                │ 23
Dirección Complemento    │ Calle, No., Apto.
Código Actividad         │ (si es B2B)
Descripción Actividad    │
```

## 6. Firmware de Integración

### 6.1 Firmador Java (localhost:8113)

**Requisitos**:
- Java 11+
- Certificado .p12 instalado en keystore local
- Puerto 8113 abierto

**Inicio** (en servidor separado):

```bash
java -jar firmador-dte.jar --port 8113
```

**Verificar conexión desde Odoo**:

```bash
curl http://localhost:8113/health
```

**Si está en servidor remoto**, actualizar en Odoo:
- **URL Firmador**: `http://ip-firmador:8113`

### 6.2 URLs de Ministerio (Ambientes)

#### Pruebas (Desarrollo/Testing)
```
Auth:     https://apitest.dtes.mh.gob.sv/seguridad/auth
Recepción: https://apitest.dtes.mh.gob.sv/fesv/recepciondte/
```

#### Producción
```
Auth:     https://api.dtes.mh.gob.sv/seguridad/auth
Recepción: https://api.dtes.mh.gob.sv/fesv/recepciondte/
```

**Cambiar en Odoo**:
1. **Ajustes** → **Empresas** → **Sección DTE**
2. Cambiar URLs a producción
3. Guardar

## 7. Prueba de Funcionamiento

### 7.1 Crear Factura de Prueba

1. **Ventas** → **Facturas** → **Crear**
2. Rellenar:
   - Cliente: Consumidor Final (DNI: 00000000)
   - Línea: Producto, cantidad, precio
3. Confirmar factura
4. Verificar que se generó `Número de Control` y `Código de Generación`

### 7.2 Enviar DTE al MH

1. Click botón **"Enviar DTE"**
2. Verificar logs:

```bash
docker compose logs -f odoo | grep DTE
```

**Salida esperada**:
```
DTE AUTH → POST https://apitest.dtes.mh.gob.sv/seguridad/auth
DTE AUTH ← HTTP 200
DTE FIRMA → POST http://localhost:8113/firmardocumento/
DTE FIRMA ← HTTP 200
DTE ENVÍO → POST https://apitest.dtes.mh.gob.sv/fesv/recepciondte/
DTE ENVÍO ← HTTP 200 | estado: PROCESADO
```

### 7.3 Verificar Resultado

En la factura, verificar:
- **Estado DTE**: `Aceptado`
- **Sello de Recepción**: (valor numérico)
- **Fecha Procesamiento MH**: (timestamp)

## 8. Respaldos y Recuperación

### 8.1 Backup Manual

```bash
# Backup de BD PostgreSQL
docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# Backup de filestore Odoo
docker compose exec odoo tar czf - /var/lib/odoo > filestore.tar.gz
```

### 8.2 Restaurar desde Backup

```bash
# Restaurar BD
docker compose exec -T db psql -U $POSTGRES_USER $POSTGRES_DB < backup.sql

# Restaurar filestore
docker compose exec odoo tar xzf - -C / < filestore.tar.gz
```

### 8.3 Volúmenes Persistentes

Los datos se guardan en:
- `postgres_data` — Base de datos
- `odoo_filestore` — PDFs, archivos

Para ver ubicación física:
```bash
docker volume inspect postgres_data
docker volume inspect odoo_filestore
```

## 9. Troubleshooting

### Odoo no inicia

```bash
# Ver logs completos
docker compose logs odoo

# Reiniciar
docker compose restart odoo
```

### Error de conexión a BD

```bash
# Verificar estado PostgreSQL
docker compose ps db

# Reiniciar BD
docker compose restart db
docker compose restart odoo
```

### Error al enviar DTE: "Firmador no disponible"

```bash
# Verificar conectividad
curl http://localhost:8113/health

# Si está en remoto, verificar firewall
telnet ip-firmador 8113
```

### Error 401 en autenticación MH

- Verificar NIT y contraseña en Odoo
- Verificar ambiente (pruebas vs producción)
- Revisar credenciales en portal MH

### Error de validación schema

```bash
# Ver error detallado
docker compose logs odoo | grep "schema inválido"

# Revisar datos de la factura
# Verificar que todos los campos requeridos estén rellenos
```

## 10. Operaciones Diarias

### Actualizar módulo DTE_SV

```bash
git pull origin develop
docker compose restart odoo
docker compose exec odoo odoo -u dte_sv -d farmacia_db --stop-after-init
```

### Ver logs en tiempo real

```bash
docker compose logs -f odoo
docker compose logs -f db
```

### Detener sistema

```bash
docker compose down
# Los datos persisten en volúmenes
```

### Eliminar todo (cuidado)

```bash
docker compose down -v
# Elimina BD y filestore
```

## 11. Seguridad en Producción

### Checklist

- [ ] Cambiar contraseña de admin Odoo
- [ ] Habilitar SSL/TLS (Nginx proxy)
- [ ] Configurar cortafuegos (solo puertos necesarios)
- [ ] Usar contraseñas fuertes en `.env`
- [ ] Habilitar backups automáticos
- [ ] Monitorear logs de error
- [ ] Usar variables de entorno para credenciales (no en `.env`)
- [ ] Restringir acceso a interface de administración

### Variables de Entorno Recomendadas

```bash
# En lugar de .env, usar variables del sistema
export POSTGRES_PASSWORD=$(aws secretsmanager get-secret-value --secret-id pg-password)
export ODOO_ADMIN_PASSWD=$(aws secretsmanager get-secret-value --secret-id odoo-admin)
export DTE_PASSWORD_MH=$(aws secretsmanager get-secret-value --secret-id mh-password)
```

## Siguientes Pasos

1. [Ver Arquitectura](./arquitectura-inicial.md)
2. [Ver Documentación Técnica](./documentacion-tecnica.md)
3. [Contactar soporte MH](https://www.hacienda.gob.sv/)

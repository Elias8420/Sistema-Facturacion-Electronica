# Documentación Técnica - Sistema DTE SV

## Estructura de Módulo

```
custom-addons/dte_sv/
├── __init__.py
├── __manifest__.py              # Metadata del módulo
├── models/
│   ├── __init__.py
│   ├── account_move.py          # Lógica de facturas DTE
│   ├── res_company.py           # Configuración emisor
│   └── res_partner.py           # Datos receptor
├── views/
│   ├── account_move_views.xml   # Interfaz de facturas
│   ├── res_company_views.xml    # Config empresa
│   └── res_partner_views.xml    # Datos partner
├── security/
│   └── ir.model.access.csv      # Control de acceso
├── data/
│   └── dte_sequence.xml         # Secuencias de control
├── static/
│   └── schemas/
│       ├── fe-f-v2.json         # Schema Factura (01)
│       ├── fe-ccf-v4.json       # Schema CCF (03)
│       └── fe-nc-v4.json        # Schema Nota Crédito (05)
└── ...
```

## Modelos Principales

### 1. AccountMove (account_move.py)

**Herencia**: Extiende `account.move` de Odoo

#### Campos DTE Agregados

```python
# Identificadores
dte_codigo_generacion    # Char - UUID v4
dte_numero_control       # Char - Secuencial único

# Respuesta del MH
dte_sello_recepcion      # Char - Sello oficial
dte_observaciones        # Text - Errores/avisos MH
dte_fecha_procesamiento  # Char - Timestamp MH

# Documento serializado
dte_json                 # Text - JSON estructura MH
tipo_dte                 # Selection - 01/03/05
estado_dte               # Selection - ciclo de vida
```

#### Métodos Principales

| Método | Rol |
|--------|-----|
| `_generar_codigo_generacion()` | Genera UUID v4 |
| `_generar_numero_control()` | Genera número secuencial |
| `_build_identificacion()` | Construye sección "identificacion" |
| `_build_emisor()` | Construye sección "emisor" |
| `_build_receptor()` | Construye sección "receptor" |
| `_build_cuerpo()` | Construye líneas del documento |
| `_build_resumen()` | Construye totales e IVA |
| `_serializar_dte()` | Genera JSON final |
| `_validar_schema_dte()` | Valida JSON con jsonschema |
| `_obtener_token_mh()` | Autentica con MH |
| `_firmar_dte()` | Envía a firmador Java |
| `_enviar_dte_mh()` | Envía DTE al MH |
| `action_enviar_dte()` | Orquesta todo el envío |
| `action_post()` | Hook al confirmar factura |

#### Flujo action_post (Confirmación)

```python
def action_post(self):
    # Confirmar factura en Odoo
    res = super().action_post()
    
    # Procesar solo facturas de salida
    facturas = self.filtered(lambda m: m.move_type in ('out_invoice', 'out_refund'))
    
    for move in facturas:
        # 1. Asignar tipo DTE (01=factura, 05=nota crédito)
        move.tipo_dte = '05' if move.move_type == 'out_refund' else '01'
        
        # 2. Generar UUID
        move.dte_codigo_generacion = move._generar_codigo_generacion()
        
        # 3. Generar número de control secuencial
        move.dte_numero_control = move._generar_numero_control()
        
        # 4. Serializar a JSON
        move.dte_json = move._serializar_dte()
        
        # 5. Marcar como pendiente de envío
        move.estado_dte = 'pendiente'
    
    return res
```

### 2. ResCompany (res_company.py)

**Herencia**: Extiende `res.company` de Odoo

#### Campos Agregados

```python
# Identificación
dte_nit                      # NIT ante Hacienda
dte_nrc                      # Número Registro Contribuyente
dte_nombre_comercial         # Nombre para facturas

# Localización
dte_departamento             # Código depto (Ej: 06)
dte_municipio                # Código municipio (Ej: 23)
dte_tipo_establecimiento     # Tipo (01=Casa Matriz)

# Actividad
dte_cod_actividad            # Código actividad económica
dte_desc_actividad           # Descripción actividad

# Establecimiento & Punto Venta
dte_establecimiento          # Código establecimiento (Ej: S001)
dte_punto_venta              # Código punto venta (Ej: P001)

# Credenciales
dte_password_mh              # Contraseña portal MH
dte_password_certificado     # Clave privada .p12

# URLs (configurables por ambiente)
dte_url_auth                 # Endpoint autenticación
dte_url_recepcion            # Endpoint recepción DTEs
dte_url_firmador             # URL firmador local

# Token (automático)
dte_token                    # Bearer token MH
dte_token_expiry             # Expiración token
```

### 3. ResPartner (res_partner.py)

**Herencia**: Extiende `res.partner` de Odoo

#### Campos Agregados

```python
dte_nrc                  # NRC del cliente
dte_departamento         # Ubicación
dte_municipio            # Ubicación
dte_complemento          # Dirección adicional
dte_cod_actividad        # Código actividad
dte_desc_actividad       # Descripción actividad
```

## Generación de JSON DTE

### Estructura Completa

```javascript
{
  "identificacion": { /* Tipo, número, fecha, etc */ },
  "documentoRelacionado": [ /* Para notas de crédito */ ],
  "emisor": { /* NIT, nombre, dirección, contacto */ },
  "receptor": { /* Datos del cliente */ },
  "ventaTercero": null,
  "cuerpoDocumento": [ /* Array de líneas */ ],
  "resumen": { /* Totales, IVA, tributos */ },
  "extension": { /* Solo para tipo 01 */ },
  "apendice": null,
  "otrosDocumentos": null
}
```

### Cálculo de IVA

#### Tipo 01 (Factura Consumidor Final)
- Precio incluye IVA (13%)
- `precioUni = linea.price_unit * 1.13` (4 decimales)
- `ivaItem = gravada * 13 / 113`

#### Tipo 03 (CCF - B2B)
- Precio sin IVA
- IVA se calcula: `iva = totalGravada * 0.13`
- Incluir en tributos: `[{codigo: '20', valor: iva}]`

#### Tipo 05 (Nota de Crédito)
- Mismo cálculo que CCF
- Relacionar factura original via `documentoRelacionado`
- Incluir UUID original en cuerpo

## Validación

### JSON Schema Validation

**Archivos de schema** (v4 Draft7):
- `fe-f-v2.json` — Factura Consumidor Final
- `fe-ccf-v4.json` — Comprobante Crédito Fiscal
- `fe-nc-v4.json` — Nota de Crédito

**Método**: `_validar_schema_dte()`

```python
def _validar_schema_dte(self):
    # 1. Cargar schema JSON
    # 2. Deserializar dte_json
    # 3. Validar con jsonschema.Draft7Validator
    # 4. Lanzar UserError si hay errores
```

**Errores reportados** (máximo 10):
- Ruta JSON del error
- Mensaje descriptivo
- Contexto del campo

## Integración con Ministerio de Hacienda

### 1. Autenticación

**Endpoint**: `{dte_url_auth}`  
**Método**: POST  
**Body**:
```json
{
  "user": "NIT_EMISOR",
  "pwd": "CONTRASEÑA_MH"
}
```

**Respuesta**:
```json
{
  "status": "OK",
  "body": {
    "token": "Bearer-token-aqui"
  }
}
```

**Manejo en código**:
- Se almacena en `company.dte_token`
- Se obtiene nuevamente en cada envío
- Timeout: 30 segundos

### 2. Firma Digital

**Endpoint**: `{dte_url_firmador}/firmardocumento/`  
**Método**: POST  
**Body**:
```json
{
  "nit": "NIT",
  "activo": true,
  "passwordPri": "CONTRASEÑA_CERTIFICADO",
  "dteJson": { /* JSON completo */ }
}
```

**Respuesta**:
```json
{
  "status": "OK",
  "body": "JWT-FIRMADO"
}
```

### 3. Recepción DTE

**Endpoint**: `{dte_url_recepcion}`  
**Método**: POST  
**Headers**:
```
Content-Type: application/json
Authorization: {token}
```

**Body**:
```json
{
  "ambiente": "00",
  "idEnvio": 1,
  "version": 1,
  "tipoDte": "01",
  "documento": "JWT-FIRMADO"
}
```

**Respuesta ACEPTADO**:
```json
{
  "estado": "PROCESADO",
  "selloRecibido": "...",
  "fhProcesamiento": "2026-05-31 15:30:00"
}
```

**Respuesta RECHAZADO**:
```json
{
  "estado": "RECHAZADO",
  "descripcionMsg": "Motivo del rechazo",
  "observaciones": ["Error 1", "Error 2"]
}
```

## Manejo de Errores

### Errores Capturados en action_enviar_dte

| Tipo | Acción |
|------|--------|
| UserError (validación) | Mostrar al usuario, estado → pendiente |
| UserError (auth) | Estado → pendiente (reintento) |
| UserError (firma) | Estado → pendiente (reintento) |
| Timeout | Estado → pendiente (reintento) |
| ConnectionError | Mostrar error, estado → pendiente |

### Logging

**Logger**: `_logger` (logging estándar Python)

**Niveles**:
- `INFO` — Eventos normales (auth OK, firma OK, envío OK)
- `WARNING` — DTEs rechazados, respuestas inesperadas
- `ERROR` — Conexión fallida, timeout, schema inválido
- `DEBUG` — Payloads completos (auth, firma)

**Logs importantes**:
```
DTE AUTH → POST https://apitest.dtes.mh.gob.sv/seguridad/auth
DTE AUTH ← HTTP 200 | body: {...}
DTE FIRMA → POST http://localhost:8113/firmardocumento/
DTE FIRMA ← HTTP 200 | body: {...}
DTE ENVÍO → POST https://apitest.dtes.mh.gob.sv/fesv/recepciondte/
DTE ENVÍO ← HTTP 200 | estado: PROCESADO
```

## Dependencias Python

```
jsonschema>=3.0       # Validación JSON schema
num2words>=0.5.10     # Conversión números a letras
requests>=2.25        # HTTP requests
```

## Testing

**Archivos de test**: `tests/test_*.py`

**Cobertura**:
- `test_account_move.py` — Lógica de generación DTE
- `test_res_company.py` — Configuración empresa
- `test_res_partner.py` — Datos partner
- `test_schemas.py` — Validación de schemas

**Ejecutar tests**:
```bash
docker compose exec odoo python -m pytest tests/
```

## Notas de Implementación

### UUIDs vs Códigos Secuenciales

- **UUID (Código de Generación)**: Identificador único global, generado aleatoriamente
- **Número Control**: Identificador secuencial por tipo de DTE, formato: `DTE-TIP-ESTABLPV-CORRELATIVO`

### IVA (Impuesto al Valor Agregado)

- El Salvador: 13% (tasa estándar)
- En Factura (01): incluido en precio
- En CCF (03) y NC (05): se suma al total
- Cálculos a 2-4 decimales según contexto

### Estados del DTE

```
BORRADOR    → Factura creada, sin confirmar
PENDIENTE   → Confirmada, lista para envío (o error reintentable)
ENVIADO     → Enviado a MH, en procesamiento
ACEPTADO    → MH procesó y aceptó
RECHAZADO   → MH procesó pero rechazó
```

### Secuencias

**Configuradas en**: `data/dte_sequence.xml`

```xml
<record id="dte_sv_control_01" model="ir.sequence">
    <field name="code">dte.sv.control.01</field>
    <field name="name">DTE SV Control Factura 01</field>
    <field name="number_next">1</field>
</record>
```

Cada tipo de DTE tiene su propia secuencia para garantizar números únicos.

# Arquitectura del Sistema de Facturación Electrónica

## Visión General

Sistema **Odoo 17 dockerizado** especializado en facturación electrónica para El Salvador, con integración directa al Ministerio de Hacienda (MH) para la validación y recepción de Documentos Tributarios Electrónicos (DTE).

## Stack Tecnológico

| Componente | Versión | Rol |
|-----------|---------|-----|
| **Odoo** | 17.0 Community | Framework ERP |
| **PostgreSQL** | 15 | Base de datos |
| **Python** | 3.x | Backend |
| **Docker** | Latest | Contenedorización |
| **Jenkins** | - | CI/CD Pipeline |

## Arquitectura de Capas

```
┌─────────────────────────────────────────┐
│     Interfaz Web Odoo (Puerto 8069)     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    Módulo DTE_SV (custom-addons)        │
│  - Modelos (Account Move, Company)      │
│  - Lógica de generación de DTEs         │
│  - Validación contra schemas MH         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   Servicios Externos (APIs)             │
│  - Ministerio de Hacienda (MH)          │
│  - Firmador Java Local (puerto 8113)    │
│  - PostgreSQL (puerto 5432)             │
└─────────────────────────────────────────┘
```

## Componentes Principales

### 1. Módulo DTE_SV

**Ubicación**: `custom-addons/dte_sv/`

#### Modelos de Datos
- **account_move.py** — Extensión de facturas con campos DTE
- **res_company.py** — Configuración del emisor (credenciales, URLs)
- **res_partner.py** — Datos del receptor

#### Campos DTE en Factura
```
- dte_codigo_generacion    (UUID v4)
- dte_numero_control       (Secuencial)
- dte_json                 (Estructura MH)
- tipo_dte                 (01, 03, 05)
- estado_dte               (Ciclo de vida)
- dte_sello_recepcion      (Respuesta MH)
```

#### Tipos de Documentos
| Tipo | Descripción | Código |
|------|-------------|--------|
| Factura Consumidor Final | B2C | `01` |
| Comprobante Crédito Fiscal | B2B | `03` |
| Nota de Crédito | Devolución | `05` |

### 2. Infraestructura Docker

**Servicios**:
- `db` — PostgreSQL 15 (puerto 5432)
- `odoo` — Odoo 17 (puerto 8069)

**Volúmenes Persistentes**:
- `postgres_data` — Datos de la base de datos
- `odoo_filestore` — Archivos/PDFs

## Flujo de Facturación Electrónica

### Ciclo Completo

```
1. CREACIÓN
   └─ Usuario crea factura en Odoo

2. CONFIRMACIÓN (action_post)
   ├─ Genera UUID (Código de Generación)
   ├─ Asigna Número de Control secuencial
   ├─ Serializa DTE a JSON (estructura MH)
   └─ Estado: BORRADOR → PENDIENTE

3. VALIDACIÓN
   ├─ Valida JSON contra schema oficial
   └─ Si hay errores → Se notifica al usuario

4. FIRMA Y ENVÍO (action_enviar_dte)
   ├─ Autenticación MH (obtiene token)
   ├─ Firma digital (Firmador Java)
   ├─ Envío a MH (recepción)
   └─ Actualiza estado según respuesta

5. ESTADOS FINALES
   ├─ ACEPTADO (Sello de Recepción MH)
   ├─ RECHAZADO (Observaciones MH)
   └─ PENDIENTE (Reintento)
```

### Flujo Detallado de Envío

```
┌─────────────────────────┐
│ Usuario: "Enviar DTE"   │
└────────────┬────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│ 1. AUTENTICACIÓN (MH)                    │
│ POST /seguridad/auth                     │
│ body: { user: NIT, pwd: contraseña }     │
│ ◄─ Respuesta: { token: "...", ... }      │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│ 2. FIRMA DIGITAL (Firmador Java)         │
│ POST http://localhost:8113/firmardocumento│
│ body: { nit, dteJson, passwordPri }      │
│ ◄─ Respuesta: JWT firmado                │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│ 3. RECEPCIÓN (MH)                        │
│ POST /fesv/recepciondte/                 │
│ headers: { Authorization: token }        │
│ body: { documento: JWT, ...}             │
│ ◄─ Respuesta: { estado, selloRecibido }  │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│ 4. ACTUALIZAR ESTADO EN ODOO             │
│ ├─ ACEPTADO → Guardar sello              │
│ ├─ RECHAZADO → Guardar observaciones     │
│ └─ ERROR → Estado PENDIENTE (reintento)  │
└──────────────────────────────────────────┘
```

## Integraciones Externas

### Ministerio de Hacienda (MH)

**Endpoints Base** (Ambiente Pruebas):
- Autenticación: `https://apitest.dtes.mh.gob.sv/seguridad/auth`
- Recepción: `https://apitest.dtes.mh.gob.sv/fesv/recepciondte/`

**Autenticación**: Token Bearer + JSON Web Token (JWT) firmado

**Formatos**: 
- Entrada: JSON (estructura específica del MH)
- Salida: JSON con estado (PROCESADO/RECHAZADO)

### Firmador Java Local

**URL**: `http://localhost:8113`  
**Endpoint**: `/firmardocumento/`  
**Función**: Firma digital del DTE con certificado .p12

## Estructura de Datos DTE

### Ejemplo JSON Generado

```json
{
  "identificacion": {
    "version": 1,
    "ambiente": "00",
    "tipoDte": "01",
    "numeroControl": "DTE-01-S001P001-000000000000001",
    "codigoGeneracion": "UUID-v4-aqui",
    "fecEmi": "2026-05-31",
    "tipoMoneda": "USD"
  },
  "emisor": {
    "nit": "...",
    "nombre": "...",
    "direccion": { "departamento": "06", "municipio": "23", ... }
  },
  "receptor": {
    "tipoDocumento": "36",
    "numDocumento": "...",
    "nombre": "..."
  },
  "cuerpoDocumento": [
    {
      "numItem": 1,
      "descripcion": "...",
      "cantidad": 1.0,
      "precioUni": 10.0,
      "ventaGravada": 10.0,
      "ivaItem": 1.30
    }
  ],
  "resumen": {
    "totalGravada": 10.0,
    "totalIva": 1.30,
    "totalPagar": 11.30
  }
}
```

## Configuración Requerida

### En Odoo (Ajustes → Empresas)

- **NIT Emisor** — Identificación ante MH
- **NRC Emisor** — Número de Registro de Contribuyente
- **Código de Establecimiento** — Ej: S001
- **Código de Punto de Venta** — Ej: P001
- **Contraseña MH** — Portal del Ministerio
- **Contraseña Certificado** — Clave privada .p12
- **URL Firmador** — Endpoint del firmador local
- **URLs MH** — Autenticación y recepción

## Security & Credenciales

⚠️ **Credenciales Sensibles**:
- Contraseña MH
- Contraseña Certificado
- Token MH (almacenado en BD)
- Certificado .p12

**Gestión**:
- Se almacenan en BD (encriptadas en producción)
- Token se obtiene automáticamente en cada envío
- Certificado debe estar en servidor local (firmador)

## Próximos Pasos

1. [Ver Documentación Técnica](./documentacion-tecnica.md)
2. [Ver Guía de Despliegue](./despliegue.md)
3. [Ver Diagramas](./diagramas/)

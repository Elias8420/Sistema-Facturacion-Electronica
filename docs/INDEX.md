# Documentación - Sistema de Facturación Electrónica DTE SV

Bienvenido a la documentación técnica del **Sistema de Facturación Electrónica para El Salvador**.

## 📚 Contenido

### 1. [Arquitectura Inicial](./arquitectura-inicial.md)
**Para**: Entender la visión general del proyecto

Cubre:
- Stack tecnológico (Odoo 17, PostgreSQL, Docker)
- Componentes principales del módulo DTE_SV
- Flujo completo de facturación electrónica
- Integraciones externas (Ministerio de Hacienda, Firmador)
- Estructura de datos DTE (JSON)

**Tiempo de lectura**: 10-15 min

---

### 2. [Documentación Técnica](./documentacion-tecnica.md)
**Para**: Desarrolladores que trabajan con el código

Cubre:
- Estructura del módulo (modelos, vistas, datos)
- API de cada modelo (AccountMove, ResCompany, ResPartner)
- Métodos de generación de JSON DTE
- Cálculo de IVA por tipo de documento
- Validación con JSON Schema
- Integración API con Ministerio (Auth, Firma, Recepción)
- Manejo de errores y logging
- Testing

**Tiempo de lectura**: 20-30 min

---

### 3. [Guía de Despliegue](./despliegue.md)
**Para**: Administradores y DevOps

Cubre:
- Requisitos previos (hardware, software, credenciales)
- Preparación del entorno (.env, certificados)
- Construcción y arranque de contenedores
- Configuración inicial de Odoo
- Instalación del módulo DTE_SV
- Configuración de empresa y datos del emisor
- Setup del Firmador Java
- Pruebas de funcionamiento
- Backups y recuperación
- Troubleshooting
- Checklist de seguridad para producción

**Tiempo de lectura**: 15-20 min

---

### 4. [Diagramas](./diagramas/)
**Para**: Visualizar arquitectura y flujos

Incluye:
- `arquitectura-general.png` — Capas y componentes del sistema
- `flujo-dte.png` — Ciclo completo de facturación electrónica
- `componentes.png` — Relaciones entre modelos y servicios

---

## 🚀 Guía Rápida

### Primeros pasos (sin código)
1. Leer [Arquitectura Inicial](./arquitectura-inicial.md)
2. Ver diagramas en [Diagramas](./diagramas/)
3. Revisar sección "Flujo de Facturación Electrónica"

### Configurar el sistema
1. Seguir [Guía de Despliegue](./despliegue.md)
2. Sección "1. Preparación del Entorno"
3. Sección "3. Iniciar Contenedores"
4. Sección "4. Configurar Odoo"

### Desarrollar o extender
1. Leer [Documentación Técnica](./documentacion-tecnica.md)
2. Entender estructura en "Estructura de Módulo"
3. Revisar "Modelos Principales"
4. Consultar métodos específicos según necesidad

### Solucionar problemas
1. [Troubleshooting](./despliegue.md#9-troubleshooting) en Guía de Despliegue
2. [Logging](./documentacion-tecnica.md#logging) en Documentación Técnica

---

## 📋 Tabla de Contenidos Rápida

| Tema | Ubicación |
|------|-----------|
| Stack tecnológico | [Arquitectura](./arquitectura-inicial.md#stack-tecnológico) |
| Componentes principales | [Arquitectura](./arquitectura-inicial.md#componentes-principales) |
| Flujo DTE | [Arquitectura](./arquitectura-inicial.md#flujo-de-facturación-electrónica) |
| Modelos de datos | [Documentación Técnica](./documentacion-tecnica.md#modelos-principales) |
| Integración API MH | [Documentación Técnica](./documentacion-tecnica.md#integración-con-ministerio-de-hacienda) |
| Cálculo de IVA | [Documentación Técnica](./documentacion-tecnica.md#cálculo-de-iva) |
| Instalación | [Despliegue](./despliegue.md#2-iniciar-contenedores) |
| Configuración | [Despliegue](./despliegue.md#4-configurar-empresa-para-dte) |
| Pruebas | [Despliegue](./despliegue.md#7-prueba-de-funcionamiento) |
| Errores | [Despliegue](./despliegue.md#9-troubleshooting) |
| Seguridad | [Despliegue](./despliegue.md#11-seguridad-en-producción) |

---

## ❓ Preguntas Frecuentes

### ¿Por dónde empiezo?
→ Leer [Arquitectura Inicial](./arquitectura-inicial.md)

### ¿Cómo instalo el sistema?
→ Seguir [Guía de Despliegue](./despliegue.md)

### ¿Cómo funciona la validación de DTE?
→ Ver [Validación](./documentacion-tecnica.md#validación) en Documentación Técnica

### ¿Qué hacer si falla un envío a MH?
→ Ver [Troubleshooting](./despliegue.md#9-troubleshooting)

### ¿Dónde está el código del módulo?
→ `custom-addons/dte_sv/` (explicado en [Documentación Técnica](./documentacion-tecnica.md#estructura-de-módulo))

---

## 🔗 Enlaces Útiles

- **Ministerio de Hacienda SV**: https://www.hacienda.gob.sv/
- **Especificaciones DTE**: https://www.hacienda.gob.sv/
- **Odoo Documentation**: https://www.odoo.com/documentation/
- **Repositorio GitHub**: (Tu URL)

---

## 📝 Notas de Versión

**Última actualización**: 2026-05-31  
**Versión de Odoo**: 17.0  
**Versión de módulo**: 1.0.0

---

## 🤝 Contribuir

Si encuentras errores o tienes sugerencias:
1. Abrir issue en GitHub
2. Hacer pull request con cambios
3. Contactar al equipo

---

**¿Necesitas ayuda?** Consulta la sección correspondiente arriba o abre un issue.

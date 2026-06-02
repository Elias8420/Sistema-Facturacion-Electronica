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

### 3. [Diagramas](./diagramas/)
**Para**: Visualizar arquitectura y flujos

Incluye:
- `arquitectura-general.png` — Capas y componentes del sistema
- `flujo-dte.png` — Ciclo completo de facturación electrónica
- `componentes.png` — Relaciones entre modelos y servicios

---

## 🚀 Guía Rápida

### Primeros pasos
1. Leer [Arquitectura Inicial](./arquitectura-inicial.md)
2. Ver diagramas en [Diagramas](./diagramas/)
3. Revisar sección "Flujo de Facturación Electrónica"

### Desarrollar o extender
1. Leer [Documentación Técnica](./documentacion-tecnica.md)
2. Entender estructura en "Estructura de Módulo"
3. Revisar "Modelos Principales"
4. Consultar métodos específicos según necesidad

### Solucionar problemas
1. Revisar [Documentación Técnica](./documentacion-tecnica.md#logging)

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

---

## 🔗 Enlaces Útiles

- **Ministerio de Hacienda SV**: https://www.hacienda.gob.sv/
- **Especificaciones DTE**: https://www.hacienda.gob.sv/
- **Odoo Documentation**: https://www.odoo.com/documentation/

---

## 📝 Notas de Versión

**Última actualización**: 2026-06-02
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

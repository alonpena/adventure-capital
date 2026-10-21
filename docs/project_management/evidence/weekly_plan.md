# Control semanal de la línea base

Semanas laborales relativas, sin feriados todavía. El Excel es la vista vigente después de cambios. Cada tarea tiene criterio de aceptación en EDT; al iniciar, descomponer sus acciones en bloques diarios de 0,5–2 días. No todo trabajo activo vence esa semana.

| Semana | Trabajo activo de Alonso | Trabajo activo empresa | Decisiones / comercial Alejandro | Entregables que vencen |
|---|---|---|---|---|
| S1 | T01, T02 | Reserva / soporte según contrato | T01 | T01: Ficha de producto y exclusiones; T02: Casos reproducibles y métricas |
| S2 | T03, T08 | Reserva / soporte según contrato | T03 | T03: Encargo técnico y matriz de evaluación; T08: Diccionario de validación |
| S3 | T04, T05, T06, T11 | T05, T06 | T04, T05, T11 | T04: Contrato e hitos de aceptación |
| S4 | T05, T06, T11 | T05, T06 | T05, T11 | T11: Nota metodológica aprobada |
| S5 | T05, T06, T07 | T05, T06, T07, T19 | T05, T07 | T05: 5 entrevistas y mapa de uso; T06: Contrato versionado y ADR propuesto |
| S6 | T07, T16, T17 | T07, T17, T19, T20, T32 | T07, T16, T32 | T07: Backlog contractual aprobado |
| S7 | T16, T09, T17, T33 | T17, T19, T20, T32 | T16, T32, T33 | T16: Contrato de escenarios; T19: Staging y pipeline de despliegue |
| S8 | T09, T17, T18, T21, T33 | T17, T18, T20, T21, T32 | T18, T32, T33 | T17: Prototipo navegable; T20: Modelo multiusuario y pruebas; T32: Política y contrato de tratamiento |
| S9 | T09, T10, T18, T21, T33 | T18, T21, T24 | T18, T33 | T09: Validador y pruebas negativas; T18: Registro de tareas y ajustes; T33: Oferta de piloto y criterios de conversión |
| S10 | T10, T21 | T21, T22, T24, T31 | Seguimiento | T21: Persistencia y migración inicial |
| S11 | T10, T12 | T22, T24, T31 | Seguimiento | T10: Contrato de adquisición fija; T24: Interfaz autenticada |
| S12 | T12, T23 | T22, T23, T31 | Seguimiento | T22: Worker aislado y estados de ejecución; T31: Runbook y restauración probada |
| S13 | T12, T15, T23, T25 | T15, T23, T25 | Seguimiento | T12: Métricas trazables y regresión |
| S14 | T15, T23, T25, T13 | T15, T23, T25, T28 | Seguimiento | T15: Versión y conjunto de casos patrón; T23: Ejecución completa desde API |
| S15 | T25, T13 | T25, T26, T28 | Seguimiento | T25: Captura validada y ayudas |
| S16 | T13, T14 | T26, T28, T30 | Seguimiento | T28: Render aislado y validado; T13: Matriz M1/M4 y límites de uso |
| S17 | T27, T14 | T26, T27, T30 | Seguimiento | T26: Pantalla de ejecuciones; T30: Cuotas y ledger de uso |
| S18 | T27, T14 | T27 | Seguimiento | T14: Informe de estabilidad y tiempos |
| S19 | T27, T29 | T27, T29, T36 | T36 | T27: Recorrido financiero completo |
| S20 | T29 | T29, T36 | T36 | Sin hito; revisar avance y riesgos |
| S21 | T29, T34 | T29, T34, T36 | T36 | T29: HTML/PDF/CSV/XLSX consistentes; T36: Prueba de uso y backlog corregido |
| S22 | T34 | T34, T35, T37 | Seguimiento | T34: Informe QA y defectos |
| S23 | T38 | T35, T37, T38 | T38 | T35: Perfil CPU/RAM/tiempo y límites; T37: Checklist y revisión independiente |
| S24 | T38, T39 | T38, T39 | T38, T39 | T38: Acta go/no-go |
| S25 | T39, T40, T42 | T39, T40 | T39, T42 | T39: 3 casos completos y entrevistas |
| S26 | T40, T42 | T40 | T42 | Sin hito; revisar avance y riesgos |
| S27 | T40, T41, T42, T44 | T40, T41, T44 | T41, T42 | T40: Versión corregida; T42: Propuesta y negociación documentada |
| S28 | T41, T44 | T41, T43, T44 | T41 | T41: Resultados de segunda ronda |
| S29 | T44, T45 | T43, T44, T45 | Seguimiento | T43: Interfaz consolidada y ayuda; T44: Runbooks, accesos y capacitación |
| S30 | T45, T46, T47 | T45, T46, T47 | T46, T47 | T45: Informe final de calidad; T46: Acta de entrega comercial |
| S31 | T47 | T47 | T47 | Sin hito; revisar avance y riesgos |
| S32 | T47 | T47 | T47 | T47: Cierre y backlog posterior |
| S33 | Reserva / coordinación | Reserva / soporte según contrato | Seguimiento | Sin hito; revisar avance y riesgos |
| S34 | Reserva / coordinación | Reserva / soporte según contrato | Seguimiento | Sin hito; revisar avance y riesgos |
| S35 | Reserva / coordinación | Reserva / soporte según contrato | Seguimiento | Sin hito; revisar avance y riesgos |

## Horas por módulo (tareas, sin coordinación recurrente)

| Módulo | Horas-persona | Días-persona a 8 h |
|---|---:|---:|
| Dirección | 10 | 1.25 |
| Ciencia | 364 | 45.50 |
| Proveedor | 18 | 2.25 |
| Producto | 212 | 26.50 |
| Arquitectura | 72 | 9.00 |
| UX | 104 | 13.00 |
| Infraestructura | 40 | 5.00 |
| Backend | 268 | 33.50 |
| Frontend | 264 | 33.00 |
| Seguridad | 92 | 11.50 |
| Reportes | 60 | 7.50 |
| Consumo | 32 | 4.00 |
| Operación | 148 | 18.50 |
| Privacidad | 32 | 4.00 |
| Comercial | 52 | 6.50 |
| QA | 144 | 18.00 |
| Piloto | 118 | 14.75 |

Coordinación recurrente: 70 h Alonso, 35 h Alejandro y 58 h líder backend (S4–S32). Incluida en recursos y presupuesto; no duplicar en tareas.

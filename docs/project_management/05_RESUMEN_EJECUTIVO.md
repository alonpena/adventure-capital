# Adventure Capital · decisión de ejecución para Alejandro Maureira

16 de octubre de 2026 · propuesta de ocho meses, con inicio contractual por definir.

**Recomendación: conservar el motor existente y contratar una empresa para convertirlo en producto SaaS. Alonso debe concentrarse en ciencia, validación e integración y supervisar a la empresa.** El alcance inicial debe ser planificación y escenarios para startups/consultores; portafolios VC e integración tributaria quedan después.

## Qué tenemos y qué falta

El repositorio ya incluye motor financiero Python, optimización determinista, capacidades estocásticas, due diligence por reglas, informes y una interfaz Streamlit. Se ejecutaron **194 pruebas satisfactorias**. No hay que pagar nuevamente por desarrollar desde cero todo ese núcleo.

Faltan autenticación, organizaciones y perfiles, aislamiento de datos, persistencia transaccional, ejecución durable, operación y QA de producto. Además, la auditoría encontró entradas inválidas aceptadas, diferencias entre etapa fija y MILP con canales mixtos y riesgos en el manejo de HTML/rutas. El núcleo necesita validación y correcciones específicas antes de un autoservicio comercial. Pasar pruebas no demuestra que todos los supuestos económicos sean correctos.

## Qué entregaremos

Una organización podrá ingresar supuestos validados, ejecutar el modelo, conservar versiones, comparar dos escenarios y descargar un informe interpretable. Habrá roles, trabajos fuera del navegador, archivos privados, límites de uso, respaldo, monitoreo y soporte inicial. El MVP será determinista; la capacidad estocástica se habilita sólo si pasa validación adicional.

No se promete en esta versión administración integral de fondos, datos SII automáticos, benchmarking sectorial, pricing óptimo, optimización robusta ni agentes autónomos. Tampoco se necesita IA para calcular cifras que ya resuelve el motor.

## Quién hace qué

| Actor | Responsabilidad |
|---|---|
| **Alonso Peña** | Metodología, validación de entradas y resultados, formulación, casos patrón, interpretación, contrato técnico del motor e integración. Supervisa sin asumir el trabajo completo de producto. |
| **Empresa** | Arquitectura SaaS, backend, UI/UX, usuarios/perfiles, datos, jobs, seguridad, QA, hosting y transferencia. Debe demostrar calidad con pruebas y operación reproducible. |
| **Alejandro Maureira** | Segmento comercial, prioridades, contratación, acuerdos con pilotos, venta y aceptación de entregables. |

La empresa debe incorporarse **en la semana 3**. Recibe contratos de datos, ejemplos y motor versionado; entrega código bajo control del proyecto, experiencia de usuario, pruebas, documentación y operación transferible. Alonso participa desde el diseño; UX y seguridad empiezan temprano.

## Plazo y control

| Hito | Semana objetivo |
|---|---:|
| Proveedor contratado | 3 |
| Alcance comercial y contratos técnicos aprobados | 6 |
| Motor determinista aceptado | 14 |
| Recorrido SaaS integrado | 19 |
| Autorización de piloto con datos reales | 24 |
| Segunda ronda de pilotos terminada | 28 |
| Lanzamiento aprobado | 30 |
| Transferencia y acompañamiento completados | 32 |

El Excel contiene 47 tareas, responsables, aceptación, Gantt editable, capacidad diaria y semanal, riesgos y CPM. La red nivelada requiere **159 días hábiles**. En el calendario de ejemplo hay 15 días de reserva antes de ingresar feriados. Se necesita proveedor disponible y tres organizaciones preagendadas para dos rondas de una semana. El escenario conservador excede ocho meses: ante retrasos se reduce alcance o se revisa el plazo.

La ruta crítica pasa por contratación y definición del producto, contratos del motor, validación científica, formulario e informes, QA/seguridad, pilotos y entrega. Hay rutas equivalentes; el Excel identifica todas las tareas de holgura cero.

## Por qué conviene delegar

El plan asigna **690 horas a Alonso**, incluida coordinación, y **1.362 horas a la empresa**. Alonso tiene dedicación media cercana a 20 h/semana, pero requiere disponibilidad mayor en semanas clave. Su contrato debe reconocer esos picos y su responsabilidad científica.

Si además asume backend, frontend y operación, aun manteniendo UX y QA externos, su carga subiría a unas **1.540 horas** suponiendo la misma productividad y descontando supervisión sustituida: más de 38 semanas completas antes de contingencias. Delegar esas disciplinas libera aproximadamente **850 horas** para validar y hacer evolucionar la metodología. El beneficio principal es proteger el trabajo científico y permitir paralelismo; no sólo ahorrar programación.

## Recursos y decisión económica

Mantener inicialmente el MacBook M1. No comprar equipo de cálculo dedicado sin medir necesidad. Racionalizar ChatGPT/Claude/Gemini a una herramienta principal y, si se justifica, una segunda. El MVP no necesita API LLM obligatoria ni licencia Enterprise. Usar infraestructura gestionada pequeña y ampliar por carga medida.

Como referencia secundaria, el plan completo exige alrededor de **55,5 millones CLP de caja**, incluyendo ocho meses de Alonso a 1,4 millones, empresa por horas estimadas, operación y reserva. No es cotización; tipo de remuneración, impuestos y contrato se confirman. Si el recurso disponible es sólo Semilla Inicia, corresponde financiar un piloto de validación más acotado y buscar complemento para el SaaS completo. **No se presupone adjudicación ni elegibilidad de todos los gastos.**

Las decisiones iniciales son aprobar segmento y MVP, confirmar dedicación de Alonso, contratar la empresa por hitos verificables y reservar pilotos. La aceptación exige cifras reconciliadas, clientes aislados, recuperación demostrada y una oferta de primera venta. Repositorio, cuentas, datos y documentación deben permanecer bajo control de Adventure Capital.

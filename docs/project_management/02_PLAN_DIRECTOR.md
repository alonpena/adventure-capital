# Plan director · Adventure Capital 2026–2027

Propuesta para Alejandro Maureira y Alonso Peña. Fecha de evaluación: 16-10-2026. Ocho meses desde inicio contractual editable. **Propuesta por aprobar, no alcance comercial ya contratado.** Se basa en la auditoría `01_AUDITORIA_REPOSITORIO.md`; no se implementan aquí nuevas funcionalidades.

## Decisión recomendada

**Alonso debe dirigir la metodología, validar el motor y supervisar la integración; la empresa debe responsabilizarse del empaquetamiento SaaS, UI/UX, autenticación, perfiles, persistencia, QA, seguridad y operación.** Alejandro define comprador, prioridad, acuerdos comerciales y aceptación del negocio. Externalizar no elimina la supervisión técnica, pero evita convertir al autor del modelo en el único desarrollador y operador de toda la plataforma.

Reutilizar el paquete Python, sus reglas, informes, casos y pruebas. Construir alrededor una capa de producto acotada y reemplazar únicamente piezas cuya auditoría lo justifique. La programación asistida por IA ya está considerada en los esfuerzos de integración; no se supone que reduzca en igual proporción validación científica, UX con usuarios o seguridad.

## Objetivo y producto de los ocho meses

Un SaaS de planificación financiera y escenarios, inicialmente para startups y consultores/incubadoras que acompañan casos individuales. El comprador inicial exacto se confirma en T01. Resultado vendible: una organización puede registrar sus supuestos, ejecutar un modelo versionado, interpretar restricciones y resultados, comparar dos escenarios y descargar un informe, con control de acceso, trazabilidad y soporte.

| Prioridad | Incluye | Criterio de producto |
|---|---|---|
| MVP indispensable | Captura validada; núcleo determinista corregido; DCF/unit economics con alcance explícito; DD por reglas; organizaciones, roles y escenarios versionados; jobs durables; informes privados; comparación básica; cuotas; respaldo, logs y soporte | Recorrido completo validado con 3 organizaciones, sin defectos críticos y con una oferta comercial concreta |
| Importante, condicionado | Evaluación estocástica y SAA existentes, después de paridad/estabilidad; mejores diagnósticos; sensibilidad por reruns acotados | No bloquea lanzamiento determinista. Habilitación sólo con aceptación científica y límites de ejecución |
| Posterior | Portafolios VC, datos reales vs presupuesto, SII automatizado, benchmarking sectorial, reactivación, pricing endógeno, optimización robusta, agentes autónomos, RAG amplio, facturación por consumo automática | Requiere demanda, datos y financiación propios; no está vendido dentro del MVP |

Motor funcional significa calcular. SaaS operable además exige saber quién accede a qué, conservar versiones, ejecutar fuera del navegador, recuperar datos, atender incidentes y cobrar por una oferta clara. Un piloto asistido con Streamlit puede vender consultoría antes; no debe presentarse como cumplimiento de todo el alcance SaaS.

## Ejecución, etapas y aceptación

La hipótesis «seis meses de desarrollo y luego dos de UX/pruebas» no es adecuada. UX, arquitectura, validación y seguridad empiezan desde las primeras semanas. Los últimos dos meses concentran pilotos, correcciones, transferencia y lanzamiento; no comienzan esas disciplinas.

| Etapa / ventana orientativa | Paquetes y entregables | Gate |
|---|---|---|
| S1–S6 · encuadre | T01–T07: segmento, baseline, proveedor, entrevistas, contratos de datos y backlog | Alejandro aprueba alcance; Alonso acepta frontera del motor; empresa acepta entrega y capacidades |
| S1–S18 · ciencia, en paralelo | T08–T16: validación, paridad fija/MILP, caja/DCF, unit economics; evaluación M4 separada | Motor determinista aceptado S14; M4 sigue cerrado si no valida |
| S5–S21 · SaaS | T17–T33: UX, datos, perfiles, jobs, integración, informes, consumo, recuperación y oferta | Recorrido integrado S19; exportaciones reconciliadas S21 |
| S19–S28 · calidad y pilotos | T34–T41: carga, aislamiento, accesibilidad, seguridad y dos rondas de tres organizaciones | Autorización piloto S24; repetición validada S28 |
| S25–S32 · comercial y operación | T42–T47: negociación, UX final, transferencia, aceptación y acompañamiento | Oferta negociada S27, lanzamiento S30, cierre operativo S32 |
| Resto hasta ocho meses | Reserva de calendario | Absorber feriados, respuesta de usuarios y defectos; no agregar módulos por disponer de margen |

**Supuestos de factibilidad:** proveedor contratado en S3, perfiles reservados en las semanas de carga, decisiones de Alejandro dentro de dos días hábiles y tres organizaciones preagendadas para dos rondas de cinco días. Si no se cumplen, no mantener la fecha fingiendo que la duración no cambió. Usar reserva, reducir alcance o renegociar plazo.

## Trabajo personal de Alonso y encargo a la empresa

| Alonso entrega a la empresa | Empresa entrega a Alonso / Adventure Capital | Forma de verificar |
|---|---|---|
| Diccionario de inputs, unidades y rangos; ejemplos válidos/ inválidos | Formularios, importaciones y errores consistentes con contrato | Pruebas automáticas de contrato + recorrido observado |
| Motor versionado, estados del solver y 3 casos patrón | Adaptador de ejecución, cola, cancelación y artefactos privados | Igualdad de cifras dentro de tolerancia declarada; nunca convertir Infeasible en éxito |
| Reglas de interpretación, advertencias y supuestos | UX e informes que conservan su significado | Alonso revisa cifras/lenguaje; usuarios explican resultado |
| Especificación de comparación de escenarios | Versiones inmutables y diff de parámetros/resultados | Repetir ejecución con misma versión reproduce resultado dentro de tolerancia |
| Criterios técnicos de aceptación | Tests E2E, aislamiento, carga, seguridad, respaldo y despliegue | Evidencia ejecutable y logs, no capturas como única prueba |
| Revisión técnica breve y respuesta a dudas | Documentación operativa, migraciones, cuentas y transferencia | Despliegue/restauración por alguien distinto del proveedor |

La empresa entra en **S3**, con diseño y arquitectura, mientras Alonso valida el núcleo. No espera al mes seis ni recibe la instrucción ambigua de «hacer una web». El núcleo puede integrarse usando contratos y respuestas de ejemplo antes de su aprobación final; los datos reales sólo entran tras los gates científicos y de seguridad.

### Supervisión sin duplicar desarrollo

Alonso reserva **70 h de coordinación recurrente** (2 h/semana durante 35 semanas), además de revisiones e integración ya incluidas en tareas: arquitectura T06, contrato T16, integración T23, formulario T25, informe T29, QA T34 y transferencia T44. No se suman esas revisiones otra vez como un porcentaje oculto. Total personal base: **620 h de tareas +70 h de coordinación =690 h**; aproximadamente 20 h/semana en promedio, con picos de 35,6 h/semana incluyendo coordinación. Promedio parcial no implica disponibilidad parcial uniforme.

Rutina propuesta: una reunión semanal técnica de 45 minutos, revisión asíncrona de contrato/cifras de 45 minutos y preparación de decisiones de 30 minutos. Revisiones mayores se cargan a su tarea concreta. La empresa administra su equipo, tickets de producto y QA; Alonso no reemplaza a su jefe de proyecto.

### Costo de oportunidad: hacerlo personalmente o supervisar

| Alternativa | Carga aproximada para Alonso | Efecto en plazo y ciencia | Juicio |
|---|---:|---|---|
| Empresa construye producto; Alonso integra/supervisa | 690 h, incluidas 70 h recurrentes | Paralelismo con validación; exige reservar picos | **Recomendada** |
| Alonso toma backend, frontend y operación; se mantiene UX/QA externos | 690 +970 −120 ≈ **1.540 h** a igual productividad | 38,5 semanas de 40 h antes de contingencia; excede ocho meses de capacidad útil | No es ahorro gratuito; desplaza metodología y crea dependencia personal |
| Misma opción con aprendizaje/context switching de 15–35% en las 970 h | ≈1.686–1.880 h | 42–47 semanas de 40 h; mayor riesgo operativo | No defendible para el mismo alcance/plazo |
| Alonso conserva Streamlit; proveedor sólo endurece piloto asistido | Alcance y carga menores, a reestimar | Puede ser válido para primeras ventas de consultoría; no ofrece SaaS completo | Alternativa si no se financia el equipo |

970 h = backend/arquitectura/coordinación 486 + frontend 284 + operación 200. Las 120 h de supervisión sustituible son **supuesto comparativo**, no recorte aprobado del plan; una parte de integración seguirá existiendo. El ahorro de tiempo base al delegar esas disciplinas sería ≈850 h, unas 21 semanas completas. La empresa completa requiere 1.362 h incluyendo UX y QA; éstos aportan especialidad e independencia y no conviene eliminarlos aunque Alonso programe.

A tarifa ilustrativa de 25.000 CLP/h, esas 970 h cuestan ≈24,25 millones: ≈28.500 CLP por hora de Alonso liberada bajo el supuesto anterior. **No es un retorno financiero probado**: faltan margen comercial, demanda y valor de la demora. El beneficio defendible es reservar el recurso difícil de sustituir —autor y validador del modelo— y evitar que la fecha dependa de una sola persona. Si la empresa no entrega independencia QA, conocimiento operativo y paralelismo real, su ventaja disminuye.

## RACI

R ejecuta; A responde y aprueba (uno por fila); C consultado; I informado. «Empresa» debe identificar un responsable técnico y quién prueba lo que otra persona construyó.

| Entregable / decisión | Alonso | Alejandro | Empresa |
|---|---|---|---|
| Segmento, propuesta y prioridad comercial | C | A/R | C |
| Selección, contrato y pagos al proveedor | C | A/R | I |
| Formulación y criterios de validez científica | A/R | C | C |
| Contrato de entradas/salidas del motor | A/R | I | R |
| Arquitectura SaaS e integración técnica | C | I | A/R |
| UI/UX y accesibilidad | C | C | A/R |
| Organizaciones, permisos y seguridad | C | I | A/R |
| Persistencia, jobs, observabilidad y respaldo | C | I | A/R |
| Correctitud de cifras e interpretación | A/R | C | R |
| QA de producto y evidencias automatizadas | C | I | A/R |
| Consentimientos y acuerdos de clientes | C | A/R | C |
| Piloto: ejecución técnica | R | C | A/R |
| Piloto: aceptación comercial / primera venta | C | A/R | C |
| Transferencia operativa | R | I | A/R |
| Lanzamiento y aceptación contractual | C | A/R | R |

La aprobación científica no se delega al proveedor; la aceptación comercial no se delega a Alonso. La empresa responde por calidad de producto aunque Alonso supervise. Para privacidad o revisión de seguridad especializada puede subcontratar un profesional identificado, manteniendo su responsabilidad técnica; Alejandro aprueba acuerdos y uso de datos.

## Contratación y salida del proveedor

Contratar por entregables pequeños aceptables: (1) diseño/contratos/entorno; (2) usuarios, datos y ejecución; (3) experiencia e informes; (4) QA/pilotos; (5) transferencia. Cada pago requiere demo en staging, código revisable, tests, documentación y lista de defectos. No proponer porcentajes de pago sin negociación. Reservar una parte final condicionada al ensayo de salida.

Desde el primer día: repositorio, dominio, cloud, almacenamiento y cuentas bajo titularidad del proyecto; licencias y componentes documentados; exportación de datos y migraciones; sin módulo opaco indispensable ni credenciales exclusivamente personales del proveedor. Exigir propiedad/licencia suficiente sobre código y diseños, confidencialidad, reglas de subcontratación, garantía de defectos y precio separado de mantenimiento.

El ensayo de salida T44 consiste en que Alonso o un tercero despliegue desde cero, restaure un respaldo y ejecute un caso sin asistencia del autor. Esto reduce dependencia; no obliga a Alonso a asumir soporte permanente. El mantenimiento después del acompañamiento T47 requiere un responsable y acuerdo propio.

## Cronograma y CPM realmente calculados

La fuente editable es `03_PLAN_OPERACIONAL.xlsx`, con 47 tareas, siete hojas y fórmulas de duración/fechas, Gantt y capacidad. `tools/plan.py` calcula red y nivelación; `plan_data.json` conserva inputs. `evidence/plan_validation.json` contiene resultados y las ocho rutas críticas alternativas. La red incluye cuatro tipos de dependencia: técnica, validación, contrato y recurso; todas son fin–inicio. No se usa una secuencia entre etapas sólo para ordenar el gráfico.

Convención: ES y EF internos son offsets de días hábiles, intervalo [ES,EF). ES=max(EF predecesoras); EF=ES+duración; LF=min(LS sucesoras), o fin del proyecto para terminales; LS=LF−duración; holgura=LS−ES. Calendario lunes–viernes; feriados editables. Días-persona=horas/8, una convención de comparación, no duración de la actividad.

**CPM lógico: 149 días hábiles. Red nivelada: 159 días, aproximadamente 31,8 semanas laborales.** Se agregaron 14 enlaces R sólo al detectar conflictos de recursos; la heurística es transparente pero no pretende resolver óptimamente RCPSP. Holgura cero significa crítica para esta red y asignación, no que sea imposible mejorarla con otro equipo.

Una ruta crítica representativa:

`T01 → T03 → T04 → T05 → T07 → T16 → T09 → T10 → T12 → T25 → T26 → T27 → T29 → T34 → T35 → T38 → T39 → T40 → T41 → T43 → T45 → T46 → T47`.

Hay caminos equivalentes por T06 en lugar de T05, T37 en lugar de T35 y T44 en lugar de T41→T43. Se deben vigilar todos, no solamente la ruta mostrada. Parte de la criticidad en la transición ciencia/formulario se debe a disponibilidad de Alonso; no es una dependencia matemática entre todo el desarrollo científico y la UI.

Con inicio **sólo ilustrativo 02-11-2026**, ocho meses terminan 01-07-2027; la red acaba 10-06-2027, con **15 días hábiles de reserva antes de ingresar feriados**. No considerar las 35 semanas equivalentes a ocho meses exactos. El Excel usa EDATE para límite contractual y WORKDAY con feriados para tareas. Al completar el calendario real, disminuye la reserva.

Duraciones optimistas ≈75% de base y conservadoras ≈150%, redondeadas por tarea, como rango exploratorio. CPM agregado de esa red: **126 /159 /241 días**. El caso optimista puede exceder capacidad diaria con el mismo esfuerzo: es un límite temporal de red, no una promesa factible sin reestimar esfuerzo/nivelar. El conservador no cabe en ocho meses. No es PERT probabilístico ni P80. Revisar O/P/C con proveedor en S3 y datos reales de throughput en S6.

El escenario base es **condicionalmente factible**, no robusto frente a todos los riesgos. No autorizar el alcance completo si sólo se dispone de Alonso 20 h/semana rígidas o no se reserva la empresa. En ese caso: posponer M4 público, comparación avanzada y autoservicio completo; mantener piloto asistido y replanificar. Terminar remuneración de Alonso al mes seis deja validación, transferencia y lanzamiento sin responsable técnico; requiere extensión o reemplazo, no trabajo gratuito implícito.

## Capacidad y esfuerzo

| Recurso | Horas tareas | Coordinación | Total | Pico semanal tareas | Disponibilidad que debe reservarse |
|---|---:|---:|---:|---:|---|
| Alonso | 620 | 70 | 690 | 33,6 | Hasta 40 h/sem en picos; 36 para tareas, 2 coordinación y reserva |
| Alejandro | 106 | 35 | 141 | 10,0 | Hasta 12 h/sem en decisiones/pilotos; no desarrollo |
| Backend / arquitectura empresa | 428 | 58 | 486 | 35,6 | 38 h tareas +2 coordinación en semanas activas |
| Frontend empresa | 284 | — | 284 | 28,0 | Hasta 40 h/sem reservables |
| UX empresa | 152 | — | 152 | 16,0 | Hasta 20 h/sem |
| QA empresa | 240 | — | 240 | 27,6 | Hasta 32 h/sem |
| Operación / seguridad empresa | 200 | — | 200 | 20,4 | Hasta 24 h/sem |
| **Total** | **2.030** | **163** | **2.193** | — | Perfiles parciales; no siete personas full-time |

Se verificó capacidad **diaria y semanal**, incluyendo horas de colaboradores; no sólo capacidad total de ocho meses. Coordinación AP/AM se reserva fuera de sus límites de tarea; backend mantiene 2 h adicionales dentro de una jornada máxima supuesta de 40. Si una persona del proveedor combina backend y operación, debe sumarse su carga y volver a nivelar: el plan asume recursos distintos en semanas de solapamiento.

La hoja RECURSOS incluye el detalle diario para detectar sobreasignación tras editar. FTE promedio es total/(40×35); no es compromiso contractual ni disponibilidad por semana. Una capacidad negativa/insuficiente no se corrige declarando ficticiamente más horas.

## Herramientas y equipos: decisión cualitativa

Mantener el **MacBook M1** inicialmente. No hay evidencia de que comprar portátil acelere los gates científicos o comerciales. Medir memoria, disco, batería y tiempo de tareas representativas en T02/T35. Si efectivamente limita el trabajo, reemplazo razonable: Apple Silicon, mínimo 16 GB de RAM (preferible 24 GB al usar contenedores/datos mayores), SSD 512 GB y respaldo. No se prescribe el modelo más reciente ni una GPU para MILP.

No comprar equipo dedicado SSH ahora. Para pruebas largas, usar workers CPU cloud con presupuesto y apagado; comparar compra sólo tras medir carga sostenida, administración, respaldo y acceso remoto. No alojar el SaaS en el portátil personal. Render ofrece separación entre servicios web, base de datos y workers; esto respalda la opción gestionada, no una recomendación cerrada de proveedor. [Documentación de workers](https://render.com/docs/background-workers).

Racionalizar **ChatGPT, Claude y Gemini**: una herramienta principal para código/documentación y una segunda sólo si durante cuatro semanas demuestra utilidad diferencial; usar nivel gratuito para la tercera cuando alcance. No hay evidencia para Enterprise en un desarrollador. Las licencias de desarrollo y la API de producción son cuentas distintas; el MVP no necesita consumo LLM obligatorio. La documentación de OpenAI diferencia precios API y uso por suscripción; Claude publica planes individuales, sin que ello pruebe adecuación al caso. [OpenAI](https://learn.chatgpt.com/docs/pricing), [Claude](https://claude.com/pricing).

## Presupuesto breve y financiación

El presupuesto es secundario según la aclaración del usuario: sirve para dimensionar, no sustituye propuestas comerciales ni estudio de remuneraciones. Tarifa empresa supuesta **18–35 mil CLP/h**, base 25 mil; no se investigó una supuesta «tarifa de mercado». Las horas incluyen desarrollo asistido por IA. Precio cerrado por hitos puede diferir.

| Concepto | Referencia base |
|---|---:|
| Alonso, 8×1,4 millones | 11,20 millones CLP |
| Empresa, 1.362 h×25 mil | 34,05 millones CLP |
| Licencias, infraestructura, dominio y revisión especializada | 3,02 millones CLP |
| Subtotal caja | 48,27 millones CLP |
| Reserva explícita 15% | 7,24 millones CLP |
| **Caja referencial** | **55,51 millones CLP** |
| Tiempo Alejandro valorizado, no desembolso contratado | 2,12 millones CLP |
| **Costo económico** | **57,63 millones CLP** |

Con banda de tarifa empresa y la misma reserva, caja ≈44,5–71,2 millones. Impuestos, cargas laborales y clasificación de honorarios se deben fijar al contratar; la reserva no prueba cobertura tributaria completa. Portátil nuevo, máquina SSH y API LLM productiva tienen compra/consumo cero en base. Distribución mensual del Excel es provisión lineal editable, no calendario de pagos negociado.

Remuneración Alonso: seis meses=8,4 millones; ocho=11,2 millones, sin asumir bruto/líquido. A 40 h/sem, ≈8.077 CLP/h comprometida; a 20 h/sem, ≈16.154 CLP/h (52/12 semanas por mes). Sobre las 690 h asignadas en ocho meses, ≈16.232 CLP/h efectiva de tareas/coord.; las horas reservadas no usadas tienen valor de disponibilidad. No concluir que 1,4 millones remunera apropiadamente toda la responsabilidad técnica sólo por esos cocientes; pactar funciones, picos, propiedad intelectual y continuidad.

Operación SaaS, órdenes de magnitud de planificación, sin cotizaciones: 10 usuarios activos/100 ejecuciones al mes, 100–250 mil CLP/mes; 100/1.000, 250–700 mil; 1.000/10.000, 0,8–2,5 millones, excluyendo soporte humano y comisiones. Supone jobs CPU de minutos y pocas ejecuciones concurrentes; SAA pesado puede invalidarlo. Modelo de costo: base web/DB/worker/respaldos + número de jobs×CPU-tiempo + almacenamiento/transferencia + soporte. Medir antes de fijar precio por consulta. Licencias personales no cubren uso API del producto.

**CORFO no se considera adjudicado.** La página vigente de Semilla Inicia informa hasta 75% y 15 millones y las convocatorias 2026 listadas están cerradas. La RM 2026 se usa sólo como referencia documental porque no se conoce región/expediente: exige condiciones de antigüedad/sin ventas y orienta el resultado a validación y primeras ventas/contrato de servicio. [Programa](https://www.corfo.gob.cl/sites/cpp/programa/semilla-inicia/), [RM 2026](https://www.corfo.gob.cl/sites/cpp/convocatoria/cdpr-metropolitano-semilla-inicia-2026/).

Las bases enlazadas por RM establecen hasta 10 meses, y en §12 limitan honorarios de socios a 700 mil mensuales por persona, hasta dos, sumando subsidio y aportes; inversión hasta 20% del subsidio. Esto puede impedir imputar íntegros los 1,4 millones si Alonso es socio. Personal nuevo/preexistente tiene reglas distintas (§7.2). No se concluye elegibilidad sin verificar convocatoria, vínculo, convenio, fechas y patrocinador. [Bases, §§5, 7 y 12](https://saowcsblobassets.blob.core.windows.net/assets/CONV/26INI-RM1/BASES%20SEMILLA%20INICIA%202025.pdf).

El presupuesto **económico** del SaaS y el presupuesto **financiable** son distintos. El primero está estimado; el segundo queda por confirmar, no en cero ni en 55,5 millones. La magnitud de Semilla Inicia hace más coherente financiar validación y un piloto vendible acotado que prometer toda la plataforma VC. Si ésa es la única fuente disponible, recortar el contrato SaaS y buscar financiación complementaria; no recortar QA/seguridad conservando la misma promesa comercial. Incorporar mentoría y actividades exigidas por el convenio al confirmar la convocatoria.

## Control operacional y riesgos

Cada lunes Alonso y líder técnico revisan tareas activas, capacidad y decisiones. Diariamente se actualizan estado, avance y bloqueo. El viernes se muestra un entregable verificable. Cada dos semanas Alejandro reprioriza y acepta hitos; todo cambio afecta esfuerzo, calendario o alcance visible. Ningún porcentaje de avance sustituye aceptación.

Los principales riesgos están en la hoja RIESGOS: discrepancias metodológicas, aislamiento de clientes, proveedor tardío, absorción de trabajo por Alonso, usuarios no disponibles, supuestos de mercado, plazo conservador, financiación, dependencia y rendimiento. Disparadores: defecto científico material o seguridad crítica bloquea piloto; más de cinco días consumidos de reserva en un mes activa revisión del alcance; ausencia de disposición a pagar en segunda ronda suspende extensiones. No convertir problemas en horas extra permanentes.

T01–T04 son las primeras acciones: confirmar comprador, congelar baseline, emitir encargo técnico y pactar equipo. No requieren una compra de hardware ni una arquitectura de agentes. El plan semanal detallado y los entregables de vencimiento se incluyen en `evidence/weekly_plan.md` y en el Excel.

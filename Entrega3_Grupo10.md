Escuela de Ingeniería Industrial

Entregable 3: Informe Final Corregido

**Diseño de una metodología estandarizada para la aceleración y valorización de startups**

por

**Alonso Peña Domarchi**

EII 6160 - Proyecto de Ingeniería Industrial 2

Profesor Guía: Ignacio Beláustegui

Profesor Evaluador: Bruno Lavín

Mandante: Alejandro Maureira

Junio, 2026

---

**Glosario**

**Aceleración:** Proceso mediante el cual una startup planifica y ejecuta un crecimiento rápido basado en adquisición y retención de clientes, ajustando su modelo comercial para escalar ingresos.

**Adquisición de clientes (Customer Acquisition):** Conjunto de actividades destinadas a captar nuevos clientes para incrementar la base activa.

**CAC (Customer Acquisition Cost):** Costo de adquisición de un cliente. Incluye todos los gastos relativos a marketing, ventas y procesos comerciales necesarios para incorporar clientes nuevos.

**Churn:** Tasa de pérdida de clientes en un período determinado.

**CVaR (Conditional Value at Risk):** Métrica de riesgo de cola que resume el valor esperado en los peores escenarios de la distribución; en M4 se usa sobre el VAN al 5% como objetivo conservador.

**Adquisición realizada:** Adquisición efectivamente observada en cada escenario estocástico tras aplicar los multiplicadores de eficiencia comercial al plan comprometido por canal.

**Ventana de comisión de terceros:** Número limitado de períodos durante los cuales el canal de terceros recibe comisión sobre ingresos atribuibles a cohortes originadas por ese canal, incluyendo ventas iniciales y recurrentes dentro de la ventana.

**Cohorte de servicio:** Conjunto de clientes adquiridos para un servicio específico en un período de planificación, cuya supervivencia y recompra se modelan a lo largo del horizonte.

**Due Diligence:** Flujo iterativo de evaluación, recomendación y recalibración que envuelve al modelo determinista, emitiendo un veredicto y determinando la elegibilidad para la valorización estocástica.

**Flujo de Caja Descontado (DCF):** Método de valorización que calcula el valor presente de los flujos futuros usando una tasa de descuento ajustada al riesgo.

**Gross Profit (GP):** Margen bruto generado por la diferencia entre ingresos y costos variables del servicio o producto.

**LHS (Latin Hypercube Sampling):** Técnica de muestreo estratificado utilizada para construir escenarios del módulo estocástico, tanto en la optimización SAA como en la evaluación ex-post fuera de muestra.

**LTV (Lifetime Value):** Valor total esperado que un cliente generará durante toda su relación con la empresa.

**Evaluación ex-post LHS:** Evaluación de una estrategia fija sobre una muestra amplia fuera de muestra generada por hipercubo latino, mediante recursión de forma cerrada y sin re-resolver el modelo de optimización.

**Múltiplos de Mercado:** Método de valorización basado en indicadores comparables; en este sistema constituye una metodología de referencia, no calibrada a comparables de mercado.

**Plan de Crecimiento Acelerado:** Escenario operativo y comercial optimizado que proyecta la estrategia necesaria para alcanzar metas de ingresos, valorización y escala.

**Recta publicitaria:** Relación lineal continua entre la inversión publicitaria y la adquisición atribuible (*A_ad = a + b·I_ad*).

**SAA (Sample Average Approximation):** Aproximación por promedio de muestra que resuelve una versión discreta del problema estocástico sobre escenarios. En el módulo M4 canónico se usa con un objetivo conservador basado en CVaR del VAN.

**Tasa de Descuento:** Parámetro utilizado en el DCF que refleja el riesgo asociado a los flujos y a la incertidumbre del modelo de negocio.

**Unit Economics:** Métricas que resumen la eficiencia comercial de una startup considerando el comportamiento unitario del cliente (CAC, LTV, ticket promedio, churn).

**Vista derivada de artefactos:** Capa de presentación (*postprocessed_results*) que reorganiza por audiencia los artefactos canónicos sin recomputar métricas; no constituye fuente de verdad.

---

**Lista de Abreviaturas**

**AC:** Adventure Capital
**ADR:** Architecture Decision Record (Registro de Decisión de Arquitectura)
**ARPU:** Average Revenue Per User
**ARR:** Annual Recurring Revenue
**CAC:** Customer Acquisition Cost
**CAPM:** Capital Asset Pricing Model
**CBC:** COIN-OR Branch and Cut (solver)
**DCF:** Discounted Cash Flow (Flujo de Caja Descontado)
**DD:** Due Diligence
**EBITDA:** Earnings Before Interest, Taxes, Depreciation and Amortization
**ETL:** Extraction, Transformation and Loading
**GP:** Gross Profit (Margen Bruto)
**LHS:** Latin Hypercube Sampling
**LTV:** Lifetime Value
**MILP:** Mixed-Integer Linear Programming (Programación Lineal Entera Mixta)
**MoM:** Month over Month
**PMBOK:** Project Management Body of Knowledge
**SAA:** Sample Average Approximation
**VAN:** Valor Actual Neto
**VC:** Venture Capital / Capital de trabajo inicial (ticket de financiamiento)

---

# I. Resumen Ejecutivo

El proyecto tiene por objetivo diseñar e implementar un sistema integrado que permita a Adventure Capital, consultora financiera especializada en startups, estandarizar y automatizar las etapas de planificación del crecimiento acelerado, valorización financiera y generación de informes, reduciendo la variabilidad de los tiempos de ejecución y la dependencia del trabajo manual del mandante. El diagnóstico evidenció una operación artesanal, con tiempos por caso entre 16 y 55 horas y una capacidad mensual restringida a entre 6 y 10 startups, configurando un cuello de botella estructural que limita la escalabilidad y la rentabilidad del servicio.

La metodología transforma la planilla financiera del mandante en una canalización modular en Python, con control de versiones, que encadena la normalización de la instancia, un modelo determinista de optimización lineal entera mixta para el plan de crecimiento, una capa de *due diligence* basada en reglas que gobierna la elegibilidad del análisis estocástico, un módulo de valorización por flujos de caja descontados y *unit economics*, una extensión estocástica canónica por SAA con muestreo LHS y objetivo CVaR del VAN, y un generador de informe en formato HTML. Sobre esta base se incorporó un refinamiento determinista en cinco fases, una capa de artefactos postprocesados como vista derivada auditable, y una interfaz de exploración (*MVP*) que lee dichos artefactos sin recomputar la lógica del modelo.

Los resultados, verificados sobre el caso canónico base, muestran una optimización con estado óptimo, ingresos acumulados por USD 3,00 millones, EBITDA acumulado por USD 1,69 millones, un VAN DCF de USD 0,53 millones sobre un capital de trabajo de USD 100 mil, y un veredicto de *due diligence* de ajuste menor que habilita M4 en modo advertencia. La evaluación estocástica canónica, sobre mil escenarios LHS fuera de muestra, entrega un VAN esperado de USD 1,54 millones, una mediana de USD 1,54 millones, un CVaR 5% de USD 0,83 millones y probabilidad nula de VAN negativo, aunque con presión de liquidez en la totalidad de los escenarios evaluados. El sistema avanza así desde una metodología manual hacia un flujo reproducible, trazable y extensible; la medición empírica del impacto operacional con casos reales del mandante queda como etapa pendiente.

*Palabras-clave:* valorización de startups, optimización entera mixta, programación estocástica, unit economics, due diligence.

---

# II. Definición del Problema, Contexto y Metodología

## 2.1 Descripción del problema y la oportunidad

Adventure Capital es una empresa de consultoría financiera especializada en la valorización y aceleración de startups, que opera fundamentalmente como la personalidad jurídica de su fundador, Alejandro Maureira. La consultora trabaja con startups provenientes de portafolios de incubadoras y *hubs* tecnológicos (3IE, Knowhub, Hubtec), y su propuesta de valor integra el diagnóstico del modelo de negocio, la planificación del crecimiento acelerado y un informe de valorización defendible ante fondos de *venture capital*.

El problema central es una limitación estructural de escalabilidad: toda la operación recae en el CEO, quien destina cerca del 60% de su tiempo a elaborar informes críticos. Esta dependencia individual genera alta variabilidad en los tiempos de entrega, restringe la capacidad mensual de atención y limita la rentabilidad, estableciendo un techo para el crecimiento del negocio.

## 2.2 Diagnóstico y modelo de la situación actual

Los registros de tiempo por tipo de servicio muestran un esfuerzo elevado y heterogéneo: el modelamiento financiero prototipo se sitúa en torno a 7 horas, los casos de valorización y aceleración sin ventas crecientes cerca de 16 horas, los proyectos con ventas menores a 12 meses aproximadamente 31 horas, y las startups con historial consolidado alrededor de 55 horas, con casos atípicos sobre 65 horas. Esta distribución escalonada, analizada mediante un diagrama de Ishikawa, se asocia a métodos manuales y fragmentados, dependencia del criterio experto, calidad heterogénea de la información de entrada, limitaciones de las herramientas y ausencia de mecanismos de medición. En conjunto, la capacidad efectiva se acota a entre 6 y 10 startups mensuales.

Las métricas de desempeño definidas para el proyecto consideran el tiempo total por valorización (estado actual cercano a 40 horas, deseado entre 28 y 32), la variabilidad del tiempo, la capacidad mensual efectiva (de 6 a una meta de 8 casos en operación estable) y el margen operacional por startup.

## 2.3 Objetivos y alcance

El **objetivo general** es diseñar e implementar un sistema integrado que permita estandarizar y automatizar las etapas de planificación del crecimiento acelerado, valorización financiera y generación de informes, reduciendo la variabilidad de los tiempos, aumentando la capacidad operativa y mejorando la trazabilidad y consistencia de los resultados.

Los **objetivos específicos** son: (1) formalizar el flujo financiero y de datos; (2) diseñar una capa de evaluación cuantitativa del caso (*due diligence*); (3) formular e implementar el plan de crecimiento acelerado óptimo; (4) desarrollar el módulo de valorización financiera y *unit economics*; (5) incorporar una extensión estocástica para análisis bajo incertidumbre; (6) automatizar la generación del informe de valorización; y (7) validar y documentar el sistema integrado.

El **alcance** comprende el diseño del motor de valorización, la estandarización de plantillas y generación automatizada de reportes, la integración con el plan de crecimiento acelerado, la definición de métricas de desempeño, la capa de *due diligence* cuantitativo y la extensión estocástica y de sensibilidad. Se **excluyen** las etapas dependientes del criterio experto del CEO (*due diligence* comercial y modelamiento financiero inicial cualitativo), el marketing y la gestión comercial, y el desarrollo de nuevos productos o líneas de servicio.

## 2.4 Marco teórico

**Lean Startup y Unit Economics.** Los enfoques clásicos de planificación estratégica presuponen procesos maduros y una relación lineal entre volumen, costos marginales y eficiencia, paradigma que pierde vigencia en startups tecnológicas caracterizadas por incertidumbre, velocidad de cambio y escalamiento no lineal (Ries, 2011). En estos modelos, la rentabilidad no proviene de la eficiencia productiva sino de la capacidad de adquirir, retener y monetizar clientes; los *unit economics* establecen al cliente como unidad mínima de análisis (ticket, CAC, LTV, churn, retención) y constituyen la base analítica de las metodologías de valorización empleadas (Blank, 2013).

**Valorización.** La valoración de startups se sustenta principalmente en dos enfoques complementarios: los flujos de caja descontados, que entregan una lectura estructural vinculada a la capacidad de generar valor en el tiempo, y los múltiplos de mercado, que ofrecen una aproximación técnica basada en empresas comparables (Köhn, 2018; Montani et al., 2020). La tasa de descuento, construida desde el CAPM ajustado por riesgo, actúa como mecanismo de conciliación entre ambos enfoques.

**PMBOK.** El desarrollo del sistema se enmarca en las buenas prácticas del *Project Management Body of Knowledge* (Project Management Institute, 2021), articulando la gestión de la integración, del alcance, del tiempo y costos, de la calidad y de los interesados, en una secuencia metodológica que coordina etapas, dependencias y entregables.

## 2.5 Metodología del proyecto

La metodología estructura el trabajo en una secuencia modular: reanudación del proyecto; formalización de la metodología de modelamiento; diseño de la capa de *due diligence* cuantitativo; desarrollo del módulo de optimización del plan de crecimiento; incorporación del análisis estocástico y de sensibilidad; desarrollo del módulo de valorización; generación automática del informe; integración y validación del sistema; y documentación metodológica e informática (transversal). Cada etapa produce artefactos canónicos en formato CSV y JSON que constituyen interfaces estables entre módulos.

> *Acta de Corrección.* ⚠️ **SIN EVIDENCIA EN REPO**: El detalle de las correcciones incorporadas respecto de las observaciones de los profesores guía y evaluador en entregas anteriores debe completarse manualmente y adjuntarse como documento separado (ver §IV y nota final).

---

# III. Diseño de la Solución y Análisis de Resultados

El sistema desarrollado es una solución modular en Python, con control de versiones en GitHub, que separa la configuración, la lógica de modelamiento, la valorización, el análisis de sensibilidad y la generación de reportes. Esta sección presenta el diseño final, organizado por componentes técnicos, el refinamiento determinista incorporado, la capa de artefactos, la interfaz de exploración, y los resultados obtenidos sobre el caso canónico, junto con el estado de implementación y las limitaciones.

## 3.1 Arquitectura de la canalización

La canalización encadena las etapas de la metodología en un flujo extremo a extremo:

```
startup.yaml → instancia normalizada (model_instance.json)
  → optimización determinista (MILP) → plan de crecimiento acelerado (artefactos)
  → valorización + unit economics (workbook) → due diligence (veredicto)
  → si la DD lo permite: optimización estocástica (SAA + CVaR) → evaluación ex-post LHS
  → artefactos postprocesados → informe HTML → interfaz de exploración
```

El modelo determinista constituye la línea base; la *due diligence* es la capa de interpretación y elegibilidad; la extensión estocástica canónica se invoca cuando el veredicto es aprobado, aprobado con advertencias o requiere solo ajuste menor. Los casos con ajuste mayor o rechazo estructural vuelven al YAML para recalibración antes de M4.

El diseño preserva un conjunto de invariantes que garantizan la consistencia metodológica: el piso de caja es una restricción dura y no una penalización del objetivo; la publicidad se modela como recta lineal continua; los ratios de CAC se calculan como aritmética posterior a la optimización y no como variables del solver; la infactibilidad se enruta como diagnóstico de brecha de financiamiento; la adquisición del primer año es inmutable; la mezcla de canales se expresa como cotas de proporción a nivel de empresa; la inflación del ratio LTV/CAC se señala como artefacto conocido y no se corrige silenciosamente; y la interfaz y el reporte leen artefactos sin recomputar la lógica del modelo.

## 3.2 Formalización de la metodología

La metodología se descompone en flujos fundamentales con variables exógenas, decisiones estratégicas y variables de estado. El flujo de clientes se modela como un balance dinámico (clientes del período anterior, ajustados por *churn*, más adquisición). El flujo de servicios distingue ventas nuevas y recurrentes según la frecuencia de recompra. El flujo de ingresos resulta de multiplicar los servicios vendidos por el ticket promedio. Los costos operacionales presentan una estructura en escalón asociada a la capacidad instalada, y los costos de adquisición se construyen desde la estructura comercial. El resultado operacional se resume en el EBITDA, base del flujo de caja y la valorización.

## 3.3 Capa de Due Diligence basada en reglas

La capa de *due diligence* implementa un proceso iterativo de evaluación, recomendación y recalibración que envuelve al modelo determinista. Cada regla recibe una clase de severidad y, en caso de falla, emite un mensaje y una recomendación. La taxonomía considera cinco niveles: *estructural* (rechaza la valorización estocástica), *mayor* (exige recalibración antes de ejecutar M4 canónico), *menor* (permite M4 en modo advertencia), *advertencia* (permite M4 en modo final, conservando las alertas) y *aprobado*. El veredicto agregado se construye con criterio del peor caso observado, y se acompaña de campos de decisión: si el análisis estocástico está habilitado, el modo de valorización, el nivel de ajuste, las razones bloqueantes y las recomendaciones de recalibración.

Las reglas se organizan en pre-reglas sobre la instancia cruda (validez de la configuración, margen unitario positivo, presencia de financiamiento, validez y severidad del *churn*), reglas de síntesis sobre los resultados del modelo (alcance del *breakeven*, presión sobre el *runway*, severidad de la brecha de financiamiento, régimen de EBITDA al tercer año y crecimiento de ingresos) y verificaciones técnicas de calibración reutilizadas como evidencia. La arquitectura admite la incorporación incremental de reglas, ya que cada una es una función pura sobre la configuración o los resultados.

## 3.4 Modelo determinista de optimización entera mixta

El núcleo cuantitativo es un modelo de optimización lineal entera mixta que determina el plan óptimo de adquisición, dotación comercial y costos sobre un horizonte mensual configurable. Se implementa mediante la librería PuLP y se resuelve con el solver de código abierto CBC. La función objetivo maximiza la suma del EBITDA descontado a lo largo del horizonte, *proxy* de valorización que evita incorporar el DCF completo dentro del problema:

*max  Σ_t descuento[t] · EBITDA[t]*

Las restricciones estructurales comprenden la inmutabilidad de la adquisición del primer año (*A_base*), el suavizado del crecimiento a partir del mes 13, las ecuaciones de cohorte con supervivencia y recompra, la capacidad operativa en escalón con piso de costo (el costo operacional es el mayor entre el costo variable y el costo mínimo de la capacidad instalada), la capacidad comercial (la adquisición vía fuerza de ventas se acota por la productividad de los vendedores activos), y la identidad de caja. La política de liquidez es configurable y el piso de caja opera como restricción dura.

## 3.5 Refinamiento determinista en cinco fases

Respecto de la versión anterior, el modelo determinista fue refinado en cinco fases secuenciales, cada una con respaldo documental y pruebas automatizadas:

1. **Techo logarítmico de adquisición.** Cota superior adicional y monótonamente decreciente sobre la adquisición total a partir del mes 13, que modela la saturación de mercado. Desactivada por defecto, preserva la inmutabilidad del primer año y no eleva el valor esperado.
2. **Separación de canales y recta publicitaria.** La adquisición total se descompone por canal (fuerza de ventas, publicidad y terceros). La publicidad se modela como recta lineal continua (*A_ad = a + b·I_ad*) y la mezcla se controla mediante cotas de proporción lineales a nivel de empresa, sin introducir bilinealidades. Una configuración sin canales reproduce exactamente la salida previa.
3. **Agregación y trazabilidad del CAC.** El CAC se descompone en componentes lineales del modelo (costo de fuerza de ventas, costo de terceros, costo publicitario), mientras que los ratios por usuario (período y acumulado) se calculan posteriormente a la optimización, nunca como variables del solver.
4. **Piso de caja de capital de trabajo con diagnóstico de brecha.** El piso de caja se indexa al ticket de financiamiento (*Caja[t] ≥ −VC*) como restricción dura. Ante infactibilidad, un modelo diagnóstico separado relaja el piso con holguras y reporta la brecha de financiamiento y el primer mes de quiebre, sin alterar el modelo principal.
5. **Unit economics anualizado, LTV/CAC y breakeven.** Las métricas se reescriben como anuales y sumadas sobre los servicios. Con la corrección, el caso canónico arroja un ratio LTV/CAC elevado que el sistema señala como artefacto de fórmula (regla C08), sin corregirlo.

## 3.6 Módulo de valorización y unit economics

El módulo de valorización reconstruye, a partir de los flujos operacionales del plan, el flujo de caja relevante: ajusta el EBITDA por impuestos (aplicados solo cuando el EBITDA es positivo), descuenta a la tasa mensual derivada de la tasa anual e incorpora el capital de trabajo inicial y un valor terminal configurable (métodos *none*, múltiplo de EBITDA o Gordon). El valor actual neto se obtiene como la suma de los flujos descontados, menos el capital de trabajo, más el valor terminal en valor presente.

Complementariamente, se calcula la valorización por múltiplos de ingresos y de EBITDA del último año. Esta valorización constituye una **metodología de referencia, no calibrada a comparables de mercado**: el propio artefacto declara que los múltiplos son configurables y no representan comparables de mercado salvo que se aporte evidencia externa.

La tabla de *unit economics* articula la lectura comercial y financiera del plan (CAC, ticket, recurrencia, ARPU, LTV, LTV/CAC, *burn rate*, capital de trabajo y valor por DCF), con trazabilidad explícita entre cada métrica, su fórmula y su fuente mediante un artefacto de traza de fórmulas.

## 3.7 Extensión estocástica canónica

El modelo determinista resuelve un único escenario con parámetros puntuales. Para evaluar el comportamiento del plan bajo incertidumbre se implementó un módulo estocástico canónico (M4) como problema SAA de dos etapas con muestreo por hipercubo latino (LHS). A diferencia del prototipo neutral al riesgo inicial, el módulo actualizado replica las estrategias comerciales del determinista —fuerza de ventas, publicidad y comisión vía terceros— y optimiza un plan de primera etapa antes de observar la realización de las eficiencias comerciales.

Las decisiones de primera etapa corresponden al plan comprometido: vendedores, líderes, inversión publicitaria y adquisición planificada por canal. En cada escenario, la adquisición realizada se obtiene aplicando multiplicadores de eficiencia a dicho plan, por lo que la base activa de clientes, los ingresos, el CAC, el EBITDA, la caja y el VAN varían por escenario. El modelo no permite *recourse* comercial dentro del escenario: si una estrategia rinde menos por saturación o menor eficiencia, el impacto se refleja en la distribución de resultados y es castigado por el objetivo.

El objetivo de optimización es conservador: maximiza el CVaR al 5% del VAN, con un término de desempate marginal por VAN esperado. El VAN de cada escenario se calcula con impuestos lineales, ticket de financiamiento fijo, piso de liquidez indexado a −VC y valor terminal lineal; se evitan formulaciones no lineales o con truncamientos binarios dentro del solver. Tras resolver el SAA, la estrategia de primera etapa queda fija y se evalúa sobre una muestra LHS fuera de muestra de mayor tamaño, generando la distribución de VAN, clientes activos finales, *breakeven*, *runway*, brecha de financiamiento y métricas de *unit economics*.

El diseño mantiene límites explícitos: los primeros doce meses del plan consensuado permanecen fijos desde `A_base`; la incertidumbre de adquisición opera desde las proyecciones posteriores; la optimización robusta de peor caso y el *recourse* comercial quedan fuera de alcance. Esta decisión prioriza una formulación trazable y resoluble que captura el riesgo de cola sin transformar el problema en una política dinámica multi-etapa.

## 3.8 Capa de artefactos postprocesados

Para sostener la trazabilidad y la futura interfaz, se incorporó una capa de artefactos postprocesados (*postprocessed_results*) definida como **vista derivada no canónica** (decisión registrada en el ADR 0007). Esta capa solo copia los artefactos JSON canónicos o selecciona y renombra columnas de los CSV canónicos, con transformaciones triviales de presentación; **nunca recomputa** la valorización, los *unit economics*, la *due diligence* ni las métricas estocásticas. Se construye con una única función idempotente que lee los archivos planos desde el directorio de salida, lo que la hace estructuralmente incapaz de recomputar la lógica del modelo, y cada carpeta se escribe solo si existen sus artefactos fuente. Las fuentes de verdad permanecen en los artefactos planos, el paquete de datos de reporte y el manifiesto de artefactos.

Las carpetas se organizan por audiencia: el plan de crecimiento acelerado (flujos de clientes, servicios, ingresos, plan comercial, capacidad, costos y caja) para el emprendedor; el *workbook* de valorización (flujo DCF, insumos, cálculo, valor terminal, resumen, *unit economics* y traza de fórmulas) para auditoría; la *due diligence* (evaluación, hallazgos y palancas recomendadas); y la evaluación estocástica (escenarios, resumen, *breakeven*, diagnósticos y estado del método).

## 3.9 Interfaz de exploración (MVP)

Se desarrolló una interfaz local de exploración construida sobre Streamlit, compuesta por una página de configuración y cuatro páginas de resultados. La página de configuración es la única que ejecuta la canalización: construye la configuración mediante un formulario, la valida y ejecuta el flujo, almacenando el directorio de salida. Las páginas de resultados (plan de crecimiento, valorización, *due diligence* y análisis estocástico) leen exclusivamente los artefactos postprocesados y no recomputan la lógica del modelo, en coherencia con el invariante de separación entre cálculo y presentación. La página estocástica muestra el estado del método tal como está registrado, sin sobre-afirmar robustez. La interfaz constituye una herramienta de exploración local y no un servicio multiusuario.

## 3.10 Resultados obtenidos con el caso canónico

Para validar funcionalmente el sistema integrado se ejecutó el caso canónico base, una instancia de un servicio sobre un horizonte de 36 meses con un capital de trabajo de USD 100 mil y una tasa de descuento anual de 35%. Esta ejecución verifica el flujo completo M1-M4 y se complementó con una auditoría de configuración mixta de canales para comprobar la paridad comercial del M4. Los resultados no sustituyen la validación con casos reales del mandante, pero evidencian salidas coherentes, interpretables y auditables.

**Tabla 3.1 — Resultados generales del escenario determinista.** Fuente: elaboración propia a partir de los artefactos del caso canónico.

| Indicador | Resultado | Interpretación |
| --- | --- | --- |
| Estado del solver | Óptimo | El plan se resuelve a optimalidad. |
| Horizonte de evaluación | 36 meses | Tres años de crecimiento. |
| Ingresos acumulados | USD 3,00 MM | Trayectoria de ingresos escalable. |
| EBITDA acumulado | USD 1,69 MM | Rentabilidad operacional acumulada. |
| Caja final | USD 1,79 MM | Holgura de caja al cierre del horizonte. |
| Caja mínima | USD −18 M | Presión de liquidez intermedia durante la aceleración. |
| Adquisición total | 1.621 clientes | Fuerte crecimiento comercial requerido. |
| Mes de *breakeven* | Mes 23 | Cruce a EBITDA acumulado positivo. |

**Tabla 3.2 — Evolución anual del desempeño.** Fuente: elaboración propia.

| Año | Adquisición | Ingresos | EBITDA | Caja fin de año | Lectura |
| --- | --- | --- | --- | --- | --- |
| Año 1 | 69 clientes | USD 83 M | USD −112 M | USD −12 M | Etapa de inversión inicial con presión de caja. |
| Año 2 | 316 clientes | USD 526 M | USD 187 M | USD 175 M | Cruce hacia rentabilidad operacional. |
| Año 3 | 1.236 clientes | USD 2,40 MM | USD 1,62 MM | USD 1,79 MM | Consolidación y captura de escala. |

La trayectoria es consistente con una startup en aceleración: un primer año de inversión con EBITDA negativo, seguido por el crecimiento de la base de clientes y la recurrencia que permiten alcanzar EBITDA positivo y holgura de caja.

**Tabla 3.3 — Resultados de valorización.** Fuente: elaboración propia.

| Método | Base utilizada | Múltiplo / criterio | Valorización |
| --- | --- | --- | --- |
| Flujos descontados (VP de flujos) | Flujos operacionales descontados | Tasa de descuento 35% | USD 0,63 MM |
| VAN neto | Flujos descontados menos capital inicial | VC inicial USD 100 M | USD 0,53 MM |
| Múltiplo de ingresos | Referencia, no calibrado a mercado | 1,5× | USD 3,60 MM |
| Múltiplo de EBITDA | Referencia, no calibrado a mercado | 3,0× | USD 4,85 MM |

La diferencia entre el flujo de caja descontado y los múltiplos no constituye una inconsistencia, sino una brecha metodológica: el DCF entrega una lectura estructural conservadora, mientras que los múltiplos ofrecen una referencia asociada al potencial de escalamiento que, en este sistema, no está calibrada a comparables de mercado.

**Tabla 3.4 — Unit economics principales.** Fuente: elaboración propia.

| Métrica | Resultado | Interpretación |
| --- | --- | --- |
| CAC | USD 359 / cliente | Costo promedio de adquisición bajo el plan. |
| Ticket promedio | USD 700 | Base de monetización por servicio. |
| Gross profit | 95,4% | Margen elevado; calibración lo marca como potencial subestimación de costos. |
| ARPU | USD 250,3 | Ingreso por usuario. |
| LTV | USD 5.360 | Valor estimado por cliente. |
| LTV/CAC | 14,93× | Ratio dentro de banda, aunque sensible a supuestos de margen y churn. |

**Tabla 3.5 — Veredicto de due diligence.** Fuente: elaboración propia.

| Campo | Valor |
| --- | --- |
| Veredicto | Requiere ajuste menor |
| Permite análisis estocástico | Sí |
| Modo de valorización | Advertencia |
| Alertas activas | Runway/caja bajo piso, gross profit alto y concentración de mix |

La instancia se clasifica como ajuste menor: no existen bloqueos estructurales ni fallas mayores de elegibilidad, por lo que M4 puede ejecutarse, pero el resultado se interpreta en modo advertencia. Las alertas principales se relacionan con presión de caja intermedia, margen bruto fuera de banda y concentración del mix, lo que recomienda revisar capital de trabajo y supuestos de costo antes de presentar el caso como decisión final.

**Tabla 3.6 — Resultados del análisis estocástico (evaluación ex-post LHS, mil escenarios).** Fuente: elaboración propia.

| Indicador | Resultado | Interpretación |
| --- | --- | --- |
| Escenarios evaluados | 1.000 | Evaluación amplia bajo incertidumbre. |
| VAN esperado | USD 1,54 MM | Valor positivo esperado. |
| CVaR 5% del VAN | USD 0,83 MM | Valor esperado de cola en escenarios adversos. |
| Percentil 10 del VAN | USD 1,06 MM | Aun en escenarios adversos el valor permanece positivo. |
| Mediana del VAN | USD 1,54 MM | Resultado central. |
| Percentil 90 del VAN | USD 2,03 MM | Potencial favorable. |
| Probabilidad de VAN negativo | 0% | El plan no destruye valor en los escenarios evaluados. |
| Clientes activos finales medianos | 1.359 | Base viva esperada al cierre del horizonte. |
| Probabilidad de alcanzar 1.000 clientes activos finales | 96,7% | Alta probabilidad de superar el hito intermedio. |
| Probabilidad de caja bajo piso | 100% | El plan requiere gestión explícita de liquidez. |
| Brecha esperada de financiamiento | USD 20,8 M | Magnitud promedio del capital adicional requerido. |
| *Breakeven* mediano | Mes 23 | Equilibrio hacia el segundo año. |

El análisis estocástico permite una conclusión más rica que la determinista: el plan mantiene valor positivo incluso en escenarios de cola, reflejado en un CVaR 5% positivo, pero presenta presión de liquidez generalizada. La lectura final es favorable en valorización y adquisición de clientes, aunque debe acompañarse de una estrategia explícita de capital de trabajo antes de presentarse como caso sin advertencias.

## 3.11 Estado de implementación por módulo

**Tabla 3.7 — Estado de implementación por módulo.** Fuente: elaboración propia a partir del repositorio.

| Módulo | Estado | Evidencia |
| --- | --- | --- |
| Modelo determinista (MILP) | Implementado | `model.py`; solver óptimo |
| Refinamiento determinista (5 fases) | Implementado | `docs/STAGE_1..5.md` |
| Valorización DCF | Implementado | `valuation.py`; `valuation_summary.json` |
| Valor terminal | Implementado (configurable; *none* en el caso) | `valuation.py`; `terminal_value.json` |
| Múltiplos | Implementado como referencia, no calibrado a mercado | `valuation_summary.json` |
| Unit economics | Implementado (*breakeven*/*payback* no persistidos) | `unit_economics.py` |
| Due diligence (reglas, veredicto, palancas) | Implementado | `due_diligence/rules.py` |
| Estocástico SAA con LHS | Implementado | `stochastic/scenarios.py`; LHS e ICDF triangular |
| M4 con paridad de canales | Implementado | `stochastic/model.py`; fuerza de ventas, publicidad y terceros |
| Objetivo CVaR del VAN | Implementado | `stochastic/model.py`; `cvar_van` |
| Evaluación ex-post LHS | Implementado | `stochastic/evaluate.py`; 1.000 escenarios fuera de muestra |
| Artefactos estocásticos M4 | Implementado | `saa_solution.json`, `stochastic_summary.csv`, `stochastic_diagnostics.json` |
| Optimización robusta de peor caso | Fuera de alcance | CVaR implementado como objetivo averso al riesgo, no worst-case |
| Capa de artefactos postprocesados | Implementado | `postprocess.py`; ADR 0007 |
| Paquete de reporte y manifiesto | Implementado | `standard_report/package.py` |
| Informe HTML | Implementado parcialmente / en estabilización | Existe generación HTML; se está simplificando M5 para leer artefactos canónicos M1-M4 |
| Interfaz de exploración (MVP) | Implementado (local) | `app.py`, `streamlit_pages/` |
| Calibración de comparables de mercado | No iniciado | fuera de alcance declarado |
| Validación con casos reales | No iniciado | pendiente (ver §IV) |

## 3.12 Limitaciones: especificado versus implementado

Se distingue de forma explícita lo implementado de lo especificado:

- **Implementado y verificado:** el modelo determinista refinado en cinco fases; el DCF con valor terminal configurable y los *unit economics* anualizados; la *due diligence* con veredicto y gate M4; el M4 canónico con LHS, paridad de canales, adquisición realizada variable por escenario, CVaR del VAN y evaluación ex-post LHS; la capa de artefactos postprocesados; y la interfaz de exploración local que lee artefactos sin recomputar.
- **En estabilización operativa:** el CLI de instancias/ejecuciones y el informe HTML simple que consolida M1-M4 desde artefactos canónicos. La ejecución M4 mixta requiere tiempos de solver mayores que el determinista, por lo que el flujo operativo debe exponer un límite de tiempo específico.
- **Brechas y artefactos conocidos:** los múltiplos no están calibrados contra comparables de mercado; el alto margen bruto del caso canónico sugiere revisar costos operacionales; la primera anualidad consensuada no se descompone aún por canal en M4; y la validación con casos reales del mandante sigue pendiente.
- **Fuera de alcance:** la optimización robusta de peor caso, el *recourse* comercial multi-etapa, un servicio multiusuario completo, la calibración automática de comparables y la validación empírica con casos reales. ⚠️ **SIN EVIDENCIA EN REPO** de validación contra casos reales.

---

# IV. Conclusiones

El proyecto cumple el objetivo general de diseñar, implementar y validar funcionalmente un sistema integrado que permite a Adventure Capital estandarizar y automatizar las etapas de planificación del crecimiento acelerado, valorización financiera y generación de informes, migrando desde un entorno de planillas y *notebooks* hacia una arquitectura modular de software gestionada en un repositorio, con artefactos canónicos como interfaz estable entre fases.

Respecto del cumplimiento de los objetivos específicos: la **formalización del flujo financiero y de datos** se considera cumplida, con instancias declarativas en YAML, validación de la estructura y un manifiesto de artefactos. La **capa de evaluación previa** se considera cumplida, con un motor de reglas extensible que emite un veredicto de cinco niveles y campos de decisión. El **plan de crecimiento acelerado óptimo** se considera cumplido y, además, refinado en cinco fases que incorporan techo de adquisición, separación de canales con recta publicitaria, trazabilidad del CAC, piso de caja con diagnóstico de brecha y *unit economics* anualizado. El **módulo de valorización y unit economics** se considera cumplido, con DCF posterior a la optimización, valor terminal configurable y múltiplos de referencia explícitamente no calibrados a mercado. La **extensión estocástica** se considera cumplida como M4 canónico, con SAA, muestreo LHS, paridad de canales comerciales, adquisición realizada variable por escenario, evaluación ex-post LHS y objetivo conservador CVaR del VAN. La **generación automática del informe** se considera parcialmente cumplida: existe una salida HTML funcional y se encuentra en estabilización una versión simple de M5 que lee directamente los artefactos canónicos M1-M4. La **validación y documentación** se considera cumplida a nivel funcional, mediante pruebas automatizadas, registros de decisiones de arquitectura y documentación de etapas; la validación empírica con casos reales permanece pendiente.

En cuanto a la aplicación de la metodología, la separación entre cálculo y presentación —materializada en la capa de artefactos como vista derivada no canónica y en la interfaz que lee dichos artefactos sin recomputar— resultó decisiva para garantizar trazabilidad y auditabilidad. Igualmente relevante fue la disciplina de no sobre-afirmar: las limitaciones, las brechas de paridad y los artefactos conocidos se declaran de forma explícita, condición necesaria para que el sistema sea defendible ante un comité académico y ante inversionistas.

Como **trabajo futuro** se propone: estabilizar el flujo operativo de instancias y ejecuciones por CLI y luego por interfaz; extender M4 hacia *recourse* comercial acotado si la evidencia del mandante lo justifica; incorporar esquemas de validación de artefactos; calibrar los múltiplos contra comparables de mercado; descomponer el plan consensuado del primer año por canal si el proceso de levantamiento de datos lo permite; evolucionar la interfaz hacia un servicio una vez estabilizado el contrato de artefactos; y, de manera prioritaria, ejecutar la validación con casos reales de la cartera del mandante para medir la reducción de tiempos, la disminución de la variabilidad y el aumento de la capacidad mensual.

> **Nota sobre documentos obligatorios complementarios.** ⚠️ La rúbrica exige adjuntar, como documentos PDF separados de este informe: (i) la Declaración de Uso de IA para esta entrega, (ii) la Declaración de Contribución al trabajo realizado firmada y (iii) el Acta de Corrección de Informe Final. La omisión de cualquiera de ellos implica que el informe no será revisado y se obtendrá la nota mínima. Estos documentos deben prepararse manualmente y no forman parte del presente archivo.

---

# Bibliografía

Blank, S. (2013). *Why the lean start-up changes everything*. Harvard Business Review, 91(5), 63–72.

Bortolini, R. F., Nogueira Cortimiglia, M., Danilevicz, A. de M. F., & Ghezzi, A. (2018). Lean Startup: A comprehensive review. *IEEE Transactions on Engineering Management*, 65(3), 424–440.

Köhn, A. (2018). The determinants of startup valuation in the venture capital context. *Venture Capital*, 20(2), 113–136.

Montani, D., Frigerio, M., & Marchesi, A. (2020). Startup company valuation: The state of art and future trends. *Journal of Innovation and Entrepreneurship*, 9(1), 1–23.

Project Management Institute. (2021). *A guide to the project management body of knowledge (PMBOK® guide) – Seventh edition*. Project Management Institute.

Ries, E. (2011). *The lean startup: How today's entrepreneurs use continuous innovation to create radically successful businesses*. Crown Business.

Asociación Chilena de Venture Capital (ACVC). (2025). *Impact report ACVC 2025*.

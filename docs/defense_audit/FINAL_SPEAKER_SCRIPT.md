# FINAL SPEAKER SCRIPT — Defensa Adventure Capital

Duración objetivo: 14–16 minutos de exposición + demo 2 min + cierre 1 min. Los tiempos por slide suman ~14:00.

---

## Apertura (Slides 1–2) — 1:30

Buenos días. Mi tesis aborda un problema concreto en evaluación de startups: las decisiones financieras tempranas se toman con incertidumbre, información incompleta y supuestos que quedan dispersos entre Excel, notebooks y narrativa.

El objetivo de Adventure Capital fue convertir esa evaluación en un proceso reproducible: partir de un YAML con los supuestos del caso, generar una instancia financiera mensual, optimizar un plan de crecimiento con un modelo MILP determinista, calcular valorización DCF y unit economics, aplicar una capa de due diligence y producir artefactos auditables que alimentan reporte y UI.

La idea central no es reemplazar al consultor ni automatizar la decisión de inversión. La idea es estructurar y hacer trazable el juicio experto: explicitar supuestos, ordenar evidencia y mostrar qué condiciones sostienen o debilitan una valorización.

## Mandante y problema (Slide 3) — 0:45

El mandante ya tenía un método operacional coherente: clientes, servicios, ingresos, CAC, costos y RRHH, EBITDA, y de ahí a valor de empresa. El problema era la implementación: un notebook exportado de Colab donde cálculo, narrativa y ejecución estaban mezclados. Era difícil auditar de dónde salía cada métrica y reproducir un análisis meses después. No se trata de eliminar Excel; se trata de separar el cálculo canónico de las vistas de negocio.

## Objetivo y alcance (Slide 4) — 0:50

El alcance es deliberadamente acotado: un MVP metodológico local. Incluye el pipeline completo, la due diligence cuantitativa, el análisis de robustez y una UI de consulta. Excluye tres cosas que declaro desde ahora: no es un SaaS productivo, no es due diligence legal, y los múltiplos de valorización son referencias configurables, no comparables calibrados a mercado. Declarar límites es parte del diseño metodológico, no una omisión.

## Metodología (Slide 5) — 1:00

La metodología es operacionalizable de punta a punta. El YAML declara servicios, costos, canales de adquisición, inversión y la tesis de crecimiento. El preprocesamiento construye la instancia mensual: cohortes, churn, recurrencia, tasa de descuento. El MILP determinista genera el plan oficial. Después vienen valorización, unit economics, due diligence y, si el gate lo permite, el análisis de robustez M4. El solver no inventa supuestos: busca el plan factible y eficiente bajo lo declarado.

## Cumplimiento (Slide 6) — 1:15

Antes del detalle técnico, el cumplimiento. Cada objetivo comprometido tiene evidencia concreta y un artefacto verificable en el repositorio: la formalización de datos vive en YAML versionable; el plan de crecimiento es un CSV generado por el solver; la valorización es un JSON trazable a supuestos; la due diligence emite un reporte con veredicto; el sistema genera reporte HTML descargable; y la suite completa de tests pasa: 186 tests, 3 omitidos. Cada fila de esta matriz tiene además una lectura defendible que declara su límite.

## Arquitectura (Slide 7) — 1:00

La decisión de arquitectura más importante es la separación en capas con dependencia unidireccional. El core financiero es la única fuente de verdad. Due diligence y análisis estocástico son capas de juicio que leen los resultados del core. Reportes y UI son presentación pura: consumen artefactos generados y no reescriben nada. Auditar el sistema es auditar archivos, no pantallas.

## Trazabilidad (Slide 8) — 1:00

Este mapa responde la pregunta operativa: ¿de dónde sale este número? El YAML entra, se congela como instancia, el solver produce el plan mensual canónico en `optimized_results.csv`, y de ahí derivan valorización, unit economics y due diligence. Dos artefactos cierran el círculo: `formula_trace.json`, que documenta las fórmulas aplicadas, y `artifacts_manifest.json`, el inventario de outputs. La trazabilidad que afirmo es técnica y reproducible; no afirmo auditoría legal ni contable total.

## Target-driven growth (Slide 9) — 1:45

Este es el punto metodológico central, y también la corrección final del proyecto.

La Entrega 3 ya integraba los módulos M1 a M5, la due diligence, el análisis estocástico, la CLI y el reporte HTML. Pero la revisión final detectó un problema sutil: con margen positivo, el modelo podía sobre-expandir la adquisición de clientes — crecimiento especulativo generado por el optimizador, no respaldado por una tesis.

Se corrigió el core hacia target-driven growth. La tesis de inversión fija el crecimiento objetivo — por defecto, triplicar el stock de clientes entre el mes 12 y el mes 36. El compromiso de crecimiento es un piso, y un envelope de adquisición acota el camino superior con slack declarado. El optimizador busca factibilidad y eficiencia de capital dentro de ese marco; no inventa upside. El VAN y el crecimiento mensual son consecuencias del plan, no parámetros calibrados.

Y hay un detalle importante: si el problema resulta infeasible, eso no es un bug. Es un diagnóstico de negocio: la tesis de crecimiento no se sostiene con esos supuestos. M4, el análisis estocástico, queda como robustez técnica; el plan oficial es el determinista.

## Due diligence (Slide 10) — 1:10

La due diligence es la capa que impide sobreinterpretar resultados. Evalúa inputs, outputs deterministas, calibración y liquidez, y emite un veredicto graduado: desde aprobado hasta rechazado para análisis estocástico. Ese veredicto es un gate real. En las corridas del repositorio hay casos aceptados con advertencias, casos que exigen ajuste mayor y casos bloqueados para M4. No es due diligence legal ni comercial: estructura y hace trazable el juicio financiero-metodológico.

## Resultados gold (Slide 11) — 1:15

Corrida gold disponible: `outputs/executions/run_20260706-045427_28a63258`.

Estos son los resultados del caso final: instancia `configs/gold/gold-b2b-saas.yaml`, VAN `USD 4,583,212`, ingresos año 3 `USD 4,503,277`, veredicto de due diligence `passed_with_warnings`. Lo que subrayo no es el número, sino su condición: es la consecuencia de un plan factible bajo una tesis declarada, con veredicto explícito. Si el comité cambia un supuesto del YAML, el sistema regenera todo el análisis de forma reproducible. Lo defendible es la trazabilidad del resultado, no su infalibilidad.

## UI y demo (Slide 12) — 1:20

La UI existe para el consultor, no para el cálculo. Permite gestionar instancias y ejecuciones y navegar los resultados: informe ejecutivo, plan de crecimiento, valorización, due diligence, robustez y la carpeta completa de artefactos descargables. El punto de diseño: la UI consume artefactos generados. Si borro la UI, los resultados siguen intactos y auditables en disco. [Transición a demo si corresponde — ver `FINAL_DEMO_SCRIPT.md`.]

## Validación y límites (Slide 13) — 1:20

La validación tiene dos capas. La técnica: 186 tests pasan, cubriendo modelo, valorización, due diligence y contratos de artefactos. La metodológica: el sistema corrió sobre cuatro casos de benchmark y los cuatro resolvieron Optimal bajo commitment y envelope. Lo relevante es que el sistema discrimina: beloop pasa con advertencias y VAN positivo cercano a dos millones; kavacomex arroja VAN negativo y exige ajuste mayor. Un sistema que solo produce buenas noticias no sirve para due diligence. El límite también es claro: el benchmark identifica brechas y soporta calibración; no constituye validación universal ni de mercado.

## Cierre (Slide 14) — 1:00

En síntesis: Adventure Capital aporta una forma reproducible de pasar desde supuestos de negocio hasta un plan financiero, una valorización y un diagnóstico de inversión. La contribución no es prometer una valorización perfecta; es que cada resultado queda vinculado a un supuesto, una transformación y un artefacto verificable.

Las limitaciones son igual de claras: no es due diligence legal, no es SaaS productivo, los múltiplos no están calibrados a mercado salvo evidencia externa, y M4 es robustez técnica, no el plan oficial.

El valor académico y práctico está en convertir una metodología experta en un pipeline defendible, extensible y auditable, manteniendo la decisión final bajo juicio humano. Muchas gracias.

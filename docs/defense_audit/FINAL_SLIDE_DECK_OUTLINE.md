# FINAL SLIDE DECK OUTLINE — Defensa Adventure Capital

**Tesis del deck (una frase):**
Adventure Capital convierte una evaluación financiera experta y ad hoc de startups en un pipeline reproducible, trazable y auditable: la tesis de inversión fija el crecimiento objetivo, el optimizador busca ejecución eficiente y factible, y la decisión final permanece bajo juicio experto.

**Storyline (pirámide):**
1. Conclusión (slides 1–6): existe un MVP metodológico que cumple el alcance comprometido.
2. Evidencia de soporte (slides 7–12): arquitectura, flujo de artefactos, modelo target-driven, DD como gate, resultados, UI.
3. Apéndice técnico (slides 13–14 + anexos): validación, benchmark, limitaciones, roadmap.

**Gramática visual (consistente en todo el deck):**
- Azul/teal `#1F6F8B` / `#2E8B8B`: sistema y método.
- Ámbar `#C77D00` / rojo oxblood `#7A1F1F`: gates, riesgos, límites.
- Gris `#6B6B6B`: artefactos y trazabilidad.
- Verde `#2E7D32`: solo evidencia verificada (tests pass, DD passed).
- Formas simples: pipelines horizontales, matrices, capas, mapas input→output. Sin iconos decorativos.

---

## Slide 1 — Adventure Capital: evaluación financiera reproducible para startups

**Mensaje principal:** Esta tesis convierte una metodología experta de evaluación de startups en un sistema reproducible y auditable.

**Bullets:**
- MVP metodológico: optimización de crecimiento, valorización DCF, due diligence, trazabilidad.
- Autor, carrera (ICI PUCV), profesor guía, mandante, fecha.
- Caso final: `configs/gold/gold-b2b-saas.yaml`.

**Visual recomendado:**
- Type: portada sobria.
- Layout: título + subtítulo + mini-pipeline lineal de 5 bloques (YAML → MILP → Valorización → DD → Artefactos) en gris al pie.
- Data/evidence: n/a.
- Notes for PPT designer: fondo claro, tipografía serif para título, sin imágenes stock ni iconos.

**Speaker notes (30–45s):**
"Buenos días. Mi tesis aborda un problema concreto: las decisiones financieras tempranas sobre startups se toman con supuestos dispersos entre Excel, notebooks y narrativa. Voy a mostrar cómo convertí esa evaluación en un sistema reproducible, donde cada resultado queda vinculado a un supuesto declarado, una transformación verificable y un artefacto auditable. La decisión de inversión sigue siendo humana; el sistema ordena la evidencia."

**Evidencia:**
- `README.md`
- `docs/defense_audit/DEFENSE_MASTER_BRIEF.md`

**Pregunta probable:** ¿Qué es exactamente lo que se defiende: el software o la metodología?

**Respuesta corta:** Ambos como unidad: una metodología de evaluación operacionalizada en un pipeline reproducible con evidencia técnica (tests, artefactos, ADRs).

---

## Slide 2 — Invertir en startups exige decidir con información incompleta

**Mensaje principal:** El problema de fondo no es calcular, sino hacer explícitos y trazables los supuestos que sostienen una valorización.

**Bullets:**
- Startups: alta incertidumbre, historia corta, datos incompletos.
- La evaluación mezcla crecimiento, caja, unit economics y valor de salida.
- Los supuestos suelen quedar dispersos e inauditables.
- La decisión final es —y debe seguir siendo— humana.

**Visual recomendado:**
- Type: embudo VC + cadena de bloques.
- Layout: izquierda embudo (deal flow → screening → evaluación → decisión); derecha cadena "supuestos → plan → valor → riesgo" en azul.
- Data/evidence: cualitativo.
- Notes for PPT designer: embudo plano en 2D, sin gradientes ni sombras.

**Speaker notes (30–45s):**
"Un fondo o un consultor evalúa startups combinando proyección de crecimiento, consumo de caja, economía unitaria y valor terminal. El problema práctico es que esos supuestos viven dispersos: una celda de Excel, un párrafo de memo, un notebook. La herramienta no pretende eliminar la incertidumbre; pretende ordenar la evidencia y mostrar qué supuestos sostienen o debilitan la valorización."

**Evidencia:**
- `CONTEXT.md`
- `docs/DUE_DILIGENCE.md`

**Pregunta probable:** ¿Esto no lo resuelven ya herramientas comerciales de modelamiento financiero?

**Respuesta corta:** Las planillas modelan; no imponen trazabilidad supuesto→artefacto ni un gate metodológico de due diligence. El aporte es la estandarización reproducible del proceso completo, no la aritmética.

---

## Slide 3 — El mandante evaluaba con notebook y Excel: cálculo, narrativa y ejecución mezclados

**Mensaje principal:** El proceso original del mandante era experto pero ad hoc: difícil de reproducir, auditar y escalar a más casos.

**Bullets:**
- Método del mandante: clientes → servicios → ingresos → CAC → costos/RRHH → EBITDA → EV.
- Implementación original: notebook Colab + planillas (`legacy/`).
- Consecuencia: imposible separar supuestos, solver, valorización y reporte.
- Cada métrica era difícil de rastrear a su origen.

**Visual recomendado:**
- Type: before/after de dos paneles.
- Layout: izquierda "antes" (bloque monolítico gris: notebook con todo mezclado); derecha "después" (capas separadas en azul: configs / core / DD / reportes / UI).
- Data/evidence: `legacy/optimizacion_plan_crecimiento_acelerado_v3 (1).py` vs `src/adventure_capital/`.
- Notes for PPT designer: no ridiculizar Excel; el mensaje es separación de responsabilidades, no crítica.

**Speaker notes (30–45s):**
"El mandante ya tenía un método operacional coherente: partir de clientes y servicios, derivar ingresos y costos, llegar a EBITDA y valor de empresa. El problema era la implementación: un notebook exportado de Colab donde cálculo, narrativa y ejecución estaban mezclados. No se elimina Excel; se separa el cálculo canónico de las vistas de negocio, para que cada métrica sea rastreable."

**Evidencia:**
- `legacy/optimizacion_plan_crecimiento_acelerado_v3 (1).py`
- `docs/model.md`
- `PLAN.md`

**Pregunta probable:** ¿Qué estaba mal en el notebook si el método era correcto?

**Respuesta corta:** Nada en la matemática; el problema era reproducibilidad y auditoría: sin contratos de entrada/salida, sin tests, sin artefactos versionables.

---

## Slide 4 — Objetivo: un MVP metodológico local, con alcance explícito y límites declarados

**Mensaje principal:** El proyecto comprometió un pipeline reproducible de evaluación —no un SaaS ni una due diligence legal— y ese alcance se declara desde el diseño.

**Bullets:**
- Objetivo: pipeline local reproducible desde YAML hasta artefactos auditables.
- Incluye: optimización MILP, valorización DCF/EV, due diligence cuantitativo, robustez M4, reportes y UI.
- Fuera de alcance: SaaS productivo, DD legal/comercial, comparables de mercado automáticos.
- Salida esperada: evidencia estructurada para decisión experta.

**Visual recomendado:**
- Type: matriz incluido / fuera de alcance.
- Layout: dos columnas; "incluido" con checks verdes, "fuera de alcance" en gris con borde ámbar.
- Data/evidence: `README.md`, `docs/END_TO_END_FLOW_CONTEXT.md`.
- Notes for PPT designer: la columna "fuera de alcance" debe verse deliberada (diseño), no como carencia.

**Speaker notes (30–45s):**
"El alcance es deliberadamente acotado: un MVP metodológico local. Incluye el pipeline completo desde supuestos YAML hasta reportes y una UI de consulta. Excluye explícitamente tres cosas que quiero dejar claras desde ahora: no es un SaaS productivo, no es due diligence legal, y los múltiplos de valorización son referencias configurables, no comparables calibrados a mercado. Declarar límites es parte del diseño metodológico."

**Evidencia:**
- `README.md`
- `docs/END_TO_END_FLOW_CONTEXT.md`
- `docs/defense_audit/07_red_flags_and_safe_wording.md`

**Pregunta probable:** ¿Por qué no llegar a SaaS si la arquitectura lo permite?

**Respuesta corta:** La tesis prioriza cerrar metodología y trazabilidad. SaaS exige autenticación, base de datos, colas y operación cloud; está documentado como evolución, no como deuda.

---

## Slide 5 — La metodología es operacionalizable: de supuestos declarados a plan, valor y juicio

**Mensaje principal:** Todo el flujo de evaluación se ejecuta como pipeline reproducible desde YAML, con etapas separadas y verificables.

**Bullets:**
- YAML declara servicios, costos, canales, inversión y tesis de crecimiento.
- Preprocesamiento construye instancia mensual: cohortes, churn, recurrencia, descuento.
- MILP determinista genera plan de crecimiento target-driven.
- Post-solve: valorización DCF, unit economics, due diligence, robustez M4, artefactos.

**Visual recomendado:**
- Type: pipeline horizontal de 9 nodos (Diagrama 1 en `FINAL_DIAGRAMS.md`).
- Layout: YAML → Validación → Instancia → MILP → Valorización → DD → M4 → Artefactos → UI/Reporte; DD en ámbar (gate), artefactos en gris, resto azul.
- Data/evidence: `src/adventure_capital/{config,instance,model,valuation}.py`.
- Notes for PPT designer: una sola fila; nombre de módulo bajo cada nodo en tipografía mono pequeña.

**Speaker notes (30–45s):**
"La metodología se ejecuta en etapas separadas. Un YAML declara todos los supuestos. El preprocesamiento genera la instancia financiera mensual. Un modelo MILP determinista resuelve el plan de crecimiento. Sobre ese plan se calcula valorización DCF y unit economics. La capa de due diligence emite un veredicto que decide si el análisis estocástico corre y cómo interpretar la valorización. Todo termina en artefactos: el reporte y la UI solo los consumen. El solver no inventa supuestos: busca el plan factible y eficiente bajo lo declarado."

**Evidencia:**
- `src/adventure_capital/config.py`, `instance.py`, `model.py`, `valuation.py`, `unit_economics.py`
- `docs/defense_audit/02_pipeline_audit.md`

**Pregunta probable:** ¿Por qué MILP y no simulación o heurística?

**Respuesta corta:** El plan combina decisiones discretas y continuas bajo restricciones de caja, capacidad y crecimiento; MILP entrega optimalidad verificable y diagnóstico de infactibilidad, que aquí es información de negocio.

---

## Slide 6 — El entregable cumple el alcance definido

**Mensaje principal:** El sistema operacionaliza los objetivos comprometidos en una metodología reproducible, trazable y auditable.

**Bullets:**
- Cada objetivo comprometido tiene evidencia ejecutable y artefacto verificable.
- Los límites de cada componente están declarados, no ocultos.
- Validación: `uv run pytest -q` → 186 passed, 3 skipped.

**Visual recomendado:**
- Type: matriz objetivo → evidencia (Diagrama 5 en `FINAL_DIAGRAMS.md`).
- Layout: tabla de 7 filas × 4 columnas; columna "Lectura defendible" en gris; checks verdes solo donde hay evidencia ejecutada.
- Data/evidence: tabla siguiente.
- Notes for PPT designer: esta tabla es el corazón del deck; máxima legibilidad, sin decoración.

| Objetivo | Evidencia | Artefacto | Lectura defendible |
|---|---|---|---|
| Formalización de datos | YAML/configuración estándar | `outputs/executions/<run>/config.yaml`, `artifacts_manifest.json` | Supuestos trazables |
| Due diligence cuantitativo | Gate financiero/metodológico | `due_diligence_report.md` | No reemplaza DD legal/comercial |
| Plan de crecimiento | Target-driven growth (ADR 0014) | `optimized_results.csv` | Plan oficial determinístico |
| Valorización/unit economics | DCF + métricas unitarias | `valuation_summary.json`, `unit_economics.csv` | Valorización trazable a supuestos |
| Robustez | M4 / escenarios (ADR 0015) | `stochastic_summary.csv` o evidencia de estado bloqueado | Robustez técnica, no plan oficial |
| Informe automático | Reporte HTML/PDF | `report.html` (`report.pdf` si WeasyPrint disponible) | Entregable auditable y descargable |
| Validación | Tests + benchmark | `pytest`: 186 passed, 3 skipped; `docs/analysis/growth_commitment_benchmarks.md` | Reproducibilidad técnica |

**Speaker notes (30–45s):**
"Antes de entrar al detalle técnico, esta matriz resume el cumplimiento. Cada objetivo comprometido tiene una evidencia concreta y un artefacto verificable en el repositorio: la formalización de datos vive en YAML versionable; el plan de crecimiento es un CSV generado por el solver; la valorización es un JSON trazable a supuestos; la due diligence emite un reporte con veredicto. Y cada fila tiene una lectura defendible que declara su límite. La suite de tests pasa completa: 186 tests."

**Evidencia:**
- `docs/defense_audit/06_claim_to_evidence_matrix.md`
- `docs/defense_audit/17_presentation_evidence_pack.md`
- `outputs/executions/run_20260701-115242_a8cf74ae/` (ejemplo de run con artefactos completos)

**Pregunta probable:** ¿Estos artefactos existen o son diseño?

**Respuesta corta:** Existen: hay ejecuciones históricas completas en `outputs/executions/` con los 30+ artefactos por corrida; puedo abrir cualquiera en vivo.

---

## Slide 7 — Arquitectura modular: cálculo, juicio y presentación viven separados

**Mensaje principal:** La arquitectura separa el cálculo canónico, el juicio de due diligence y las capas de presentación, lo que hace el sistema auditable y extensible.

**Bullets:**
- `configs/`: supuestos versionables (YAML).
- `src/adventure_capital/`: core financiero + MILP + valorización (fuente de verdad).
- `due_diligence/` y `stochastic/`: juicio estructurado y robustez, desacoplados del core.
- `standard_report/` + Streamlit: presentación que consume artefactos, nunca recalcula.

**Visual recomendado:**
- Type: arquitectura en capas (Diagrama 2 en `FINAL_DIAGRAMS.md`).
- Layout: 4 capas horizontales: entrada (gris) → core (azul) → juicio/robustez (ámbar) → presentación (gris); flechas solo hacia abajo.
- Data/evidence: estructura real del repo.
- Notes for PPT designer: rotular cada capa con directorio real en mono; flecha única de retorno prohibida (refuerza "UI no recalcula").

**Speaker notes (30–45s):**
"La decisión de arquitectura más importante es la separación en capas con dependencia unidireccional. El core financiero —modelo, valorización, unit economics— es la única fuente de verdad. Due diligence y análisis estocástico son capas de juicio que leen resultados del core. Reportes y UI son presentación pura: consumen artefactos generados y no reescriben nada. Esto significa que auditar el sistema es auditar archivos, no pantallas."

**Evidencia:**
- `docs/defense_audit/01_repo_architecture_audit.md`
- `src/adventure_capital/`, `app.py`, `streamlit_pages/`

**Pregunta probable:** ¿Cómo garantizas que la UI no altera resultados?

**Respuesta corta:** La UI lee CSV/JSON/HTML generados por el pipeline; no importa módulos de cálculo para reescribir métricas. La fuente de verdad son los archivos en `outputs/`.

---

## Slide 8 — Cada resultado se rastrea de supuesto a artefacto descargable

**Mensaje principal:** El flujo input-output está completamente mapeado: cada métrica del reporte tiene un archivo fuente y una función de origen.

**Bullets:**
- Entrada: YAML versionable → instancia congelada (`model_instance.json`).
- Núcleo: plan mensual canónico (`optimized_results.csv`).
- Derivados: `valuation_summary.json`, `unit_economics.csv`, `due_diligence_report.md`.
- Auditoría: `formula_trace.json` + `artifacts_manifest.json` mapean cada valor a su fuente.

**Visual recomendado:**
- Type: mapa input→output (Diagrama 3 en `FINAL_DIAGRAMS.md`).
- Layout: tres columnas: supuestos (gris) → outputs de modelo (azul) → artefactos descargables/UI (gris); nombres de archivo reales en mono.
- Data/evidence: `docs/defense_audit/15_input_output_traceability.md`.
- Notes for PPT designer: máximo 12 cajas; los nombres de archivo son el contenido, no decoración.

**Speaker notes (30–45s):**
"Este mapa es la respuesta operativa a la pregunta ¿de dónde sale este número? El YAML entra, se congela como instancia, el solver produce el plan mensual canónico, y de ahí derivan valorización, unit economics y due diligence. Dos artefactos cierran el círculo: formula_trace.json documenta las fórmulas aplicadas y artifacts_manifest.json es el inventario de outputs. La trazabilidad que afirmo es técnica y reproducible; no afirmo auditoría legal o contable total."

**Evidencia:**
- `docs/defense_audit/15_input_output_traceability.md`
- `outputs/executions/run_20260701-115242_a8cf74ae/formula_trace.json`

**Pregunta probable:** ¿Trazabilidad significa que un auditor externo puede validar todo?

**Respuesta corta:** Puede validar la cadena técnica input→output completa. No cubre validez legal/contable de los supuestos: eso queda en el dominio del experto.

---

## Slide 9 — La tesis de inversión fija el crecimiento; el optimizador solo busca ejecución eficiente

**Mensaje principal:** El core vigente es determinista target-driven: el crecimiento objetivo es un compromiso declarado del inversionista, no un resultado especulativo del solver.

**Bullets:**
- Tesis por defecto: triplicar stock de clientes entre mes 12 y mes 36 (C36 ≥ 3·C12).
- `growth_commitment` es piso; `acquisition_envelope` acota el camino superior con slack declarado.
- VAN y crecimiento mensual son consecuencias del plan, no parámetros calibrados.
- Infeasible es diagnóstico de negocio ("la tesis no se sostiene con estos supuestos"), no bug.

**Visual recomendado:**
- Type: curva de stock de clientes con hitos C12, C24, C36 (línea azul), banda envelope (gris) y piso de compromiso (línea ámbar punteada).
- Layout: gráfico único, ejes mes/clientes; anotar "C36 ≥ 3·C12".
- Data/evidence: `optimized_results.csv` de `outputs/executions/run_20260706-045427_28a63258` o demo `configs/demo-growth-core.yaml`.
- Notes for PPT designer: sin ejes 3D; una sola serie con banda.

**Speaker notes (30–45s):**
"Este es el punto metodológico central y también la corrección final del proyecto. La Entrega 3 ya integraba los módulos M1–M5, due diligence, análisis estocástico, CLI y reporte HTML. Pero la revisión final detectó un problema: con margen positivo, el modelo podía sobre-expandir adquisición y generar crecimiento especulativo. Se corrigió el core hacia target-driven growth: la tesis de inversión fija el crecimiento objetivo —por defecto triplicar el stock entre mes 12 y 36— y el optimizador busca factibilidad y eficiencia de capital dentro de un envelope trazable. El optimizador no inventa upside. Y si el problema resulta infeasible, eso es un diagnóstico de negocio valioso: la tesis no se sostiene con esos supuestos. M4 queda como robustez técnica, no como plan oficial."

**Evidencia:**
- `docs/adr/0014-growth-commitment-hiring-friction.md`
- `docs/analysis/final_growth_decision.md`
- `tests/test_acquisition_envelope.py`

**Pregunta probable:** ¿Por qué el crecimiento objetivo no lo decide el optimizador si tiene la información?

**Respuesta corta:** Porque optimizar crecimiento con margen positivo produce expansión especulativa sin ancla en la tesis del inversionista. El objetivo de crecimiento es un juicio de inversión; el optimizador aporta factibilidad y eficiencia de capital, no la ambición.

---

## Slide 10 — Due diligence actúa como gate: decide si los resultados merecen interpretarse

**Mensaje principal:** La due diligence cuantitativa estructura y hace trazable el juicio experto: clasifica hallazgos, emite veredicto y bloquea o habilita el análisis estocástico.

**Bullets:**
- Evalúa inputs, outputs deterministas, calibración y liquidez.
- Veredictos graduados: passed / passed_with_warnings / requires_minor_adjustment / requires_major_adjustment / rejected_for_stochastic.
- El veredicto decide si M4 corre y cómo leer la valorización.
- No es due diligence legal ni recomendación automática de inversión.

**Visual recomendado:**
- Type: tabla de veredictos con semáforo + flujo de gate.
- Layout: izquierda escala de veredictos (verde→ámbar→rojo); derecha mini-flujo "resultados → DD → [gate] → M4 / recalibrar".
- Data/evidence: veredictos reales de corridas: `passed_with_warnings` (beloop), `requires_major_adjustment` (caso base), `rejected_for_stochastic` (godemos bench).
- Notes for PPT designer: semáforo sobrio (puntos de color, no señalética).

**Speaker notes (30–45s):**
"La due diligence es la capa que impide sobreinterpretar resultados. Revisa la calidad de los inputs, la coherencia de los outputs deterministas, la calibración y la liquidez, y emite un veredicto graduado. Ese veredicto es un gate real: en las corridas del repositorio hay casos aceptados con advertencias, casos que exigen ajuste mayor y casos bloqueados para análisis estocástico. Importante: esto no reemplaza la due diligence legal ni comercial; estructura y hace trazable el juicio financiero-metodológico."

**Evidencia:**
- `docs/DUE_DILIGENCE.md`
- `src/adventure_capital/due_diligence/`
- `outputs/executions/run_20260701-115242_a8cf74ae/due_diligence_report.md`

**Pregunta probable:** ¿Quién define las reglas del gate y con qué autoridad?

**Respuesta corta:** Reglas codificadas desde el método del mandante y práctica financiera estándar, declaradas en `configs/due_diligence.yaml` y documentadas; son configurables y auditables, no una caja negra.

---

## Slide 11 — Resultados del caso final: plan, valor y veredicto trazables a un solo YAML

**Mensaje principal:** El caso gold demuestra el ciclo completo: de supuestos declarados a plan oficial, valorización y veredicto de due diligence, todo auditable.

**Bullets:**
- Instancia: `configs/gold/gold-b2b-saas.yaml` — ejecución: `outputs/executions/run_20260706-045427_28a63258`.
- VAN (DCF): `USD 4,583,212` — Ingresos año 3: `USD 4,503,277` — EBITDA año 3: `USD 3,557,712`.
- Veredicto DD: `passed_with_warnings`.
- Alcance: resultados condicionales a supuestos declarados; no es predicción de mercado.

**Visual recomendado:**
- Type: tarjetas de KPI + curva de plan.
- Layout: fila de 4 tarjetas (VAN / Ingresos Y3 / EBITDA Y3 / veredicto DD) sobre gráfico de ingresos-EBITDA mensual desde `optimized_results.csv`.
- Data/evidence: `outputs/executions/run_20260706-045427_28a63258/valuation_summary.json`, `growth_plan_summary.json`.
- Notes for PPT designer: tarjeta DD coloreada por veredicto (verde solo si passed).

**Speaker notes (30–45s):**
"Estos son los resultados del caso final. Corrida gold disponible: `outputs/executions/run_20260706-045427_28a63258`. Lo que quiero subrayar no es el número de VAN en sí, sino su condición: es la consecuencia de un plan factible bajo una tesis de crecimiento declarada, con veredicto de due diligence explícito. Si el comité cambia un supuesto del YAML, el sistema regenera todo el análisis de forma reproducible. Eso es lo defendible: la trazabilidad del resultado, no su infalibilidad."

**Evidencia:**
- `outputs/executions/run_20260706-045427_28a63258/valuation_summary.json`
- `outputs/executions/run_20260706-045427_28a63258/optimized_results.csv`
- `outputs/executions/run_20260706-045427_28a63258/due_diligence_report.md`

**Pregunta probable:** ¿Ese VAN es realista?

**Respuesta corta:** Es internamente consistente bajo supuestos declarados y trazables. El sistema no valida mercado; para eso están el gate de DD y el juicio experto, que es exactamente el diseño.

---

## Slide 12 — La UI es una capa de consulta: los artefactos son la fuente de verdad

**Mensaje principal:** La UI Streamlit gestiona instancias y ejecuciones y presenta artefactos generados; nunca recalcula resultados.

**Bullets:**
- Gestión: crear instancia desde YAML, lanzar ejecución, revisar estados.
- Consulta: informe ejecutivo, plan de crecimiento, valorización, DD, robustez, artefactos.
- Fuente de verdad: archivos en `outputs/executions/<run>/`, no widgets.
- Reporte HTML descargable por corrida.

**Visual recomendado:**
- Type: screenshot UI + demo path (Diagrama 4 en `FINAL_DIAGRAMS.md`).
- Layout: screenshot grande (`[PENDIENTE: capturar screenshot UI — sugerido docs/defense_audit/assets/ui_informe_ejecutivo.png]`) con demo path de 7 pasos como cinta inferior: seleccionar ejecución → informe ejecutivo → plan de crecimiento → valoración → DD → robustez → artefactos.
- Data/evidence: `app.py`, `streamlit_pages/`.
- Notes for PPT designer: screenshot real sin retoque; cinta en gris con paso activo en azul.

**Speaker notes (30–45s):**
"La UI existe para el consultor, no para el cálculo. Permite gestionar instancias y ejecuciones, y navegar los resultados: informe ejecutivo, plan de crecimiento, valorización, due diligence, robustez y la carpeta completa de artefactos descargables. El punto de diseño es que la UI consume artefactos generados: si borro la UI, los resultados siguen intactos y auditables en disco. En la demo sigo exactamente este camino de siete pasos."

**Evidencia:**
- `app.py`, `streamlit_pages/`
- `[PENDIENTE: capturar screenshot UI — sugerido docs/defense_audit/assets/ui_informe_ejecutivo.png]`
- `outputs/executions/run_20260706-045427_28a63258/report.html`

**Pregunta probable:** ¿La UI soporta múltiples usuarios o casos simultáneos?

**Respuesta corta:** Es local y mono-usuario por diseño de MVP; multiusuario exige auth, DB y colas, documentado como evolución SaaS futura.

---

## Slide 13 — Validación por tests y benchmark: el sistema diagnostica, incluso cuando el caso es malo

**Mensaje principal:** La validación combina suite de tests reproducible y benchmark de casos reales que demuestra que el sistema discrimina casos fuertes y débiles.

**Bullets:**
- Tests: `uv run pytest -q` → 186 passed, 3 skipped.
- Benchmark growth core (4 casos, `benchmark_v0`): todos Optimal bajo commitment + envelope.
- El sistema discrimina: beloop VAN 1.973.394 (passed_with_warnings) vs kavacomex VAN −416.453 (requires_major_adjustment).
- Límites: benchmark identifica brechas y soporta calibración; no es validación universal ni de mercado.

**Visual recomendado:**
- Type: tabla benchmark de 4 filas con semáforo DD.
- Layout: caso | VAN | Ingresos Y3 | veredicto DD | lectura; VAN negativo en oxblood, positivo en azul (verde solo para tests pass).
- Data/evidence: `docs/analysis/growth_commitment_benchmarks.md`.
- Notes for PPT designer: mostrar los negativos con la misma dignidad visual que los positivos — son evidencia de diagnóstico, no fracaso.

| Caso | VAN core | Ingresos Y3 | Veredicto DD |
|---|---:|---:|---|
| godemos | 942.635 | 1.038.995 | requires_minor_adjustment |
| entrena-en-casa | −69.622 | 304.266 | requires_major_adjustment |
| beloop | 1.973.394 | 2.618.430 | passed_with_warnings |
| kavacomex | −416.453 | 217.140 | requires_major_adjustment |

**Speaker notes (30–45s):**
"La validación tiene dos capas. Primero, la técnica: 186 tests pasan, cubriendo modelo, valorización, due diligence y contratos de artefactos. Segundo, la metodológica: corrí el sistema sobre cuatro casos de benchmark. Los cuatro resuelven Optimal, y lo relevante es que el sistema discrimina: beloop pasa con advertencias y VAN positivo; kavacomex arroja VAN negativo y exige ajuste mayor. Un sistema que solo produce buenas noticias no sirve para due diligence. El límite también es claro: el benchmark identifica brechas y soporta calibración; no constituye validación universal."

**Evidencia:**
- `docs/analysis/growth_commitment_benchmarks.md`
- `docs/defense_audit/11_instances_benchmarks_and_results.md`
- `tests/`

**Pregunta probable:** ¿Cuatro casos bastan para validar?

**Respuesta corta:** Bastan para demostrar comportamiento y capacidad de discriminación del sistema; no afirmo validación estadística. Es la limitación declarada y parte del roadmap de calibración.

---

## Slide 14 — Aporte: una metodología experta convertida en pipeline defendible, extensible y auditable

**Mensaje principal:** La contribución es metodológica y de ingeniería: evaluación financiera reproducible con juicio experto trazable; los límites y el roadmap están declarados.

**Bullets:**
- Aporte: pipeline reproducible YAML→artefactos; DD como gate; plan oficial determinista target-driven.
- Aprendizaje: la corrección target-driven muestra que la ambición de crecimiento es un juicio de inversión, no un output del solver.
- Limitaciones: MVP local, DD financiero-metodológico (no legal), múltiplos de referencia, benchmark acotado.
- Roadmap: API/SaaS, base de datos, calibración con datos externos, recourse estocástico.

**Visual recomendado:**
- Type: tres columnas cerradas.
- Layout: "Contribuciones" (azul) / "Limitaciones" (gris con borde ámbar) / "Roadmap" (gris); 3–4 ítems por columna.
- Data/evidence: `DEFENSE_MASTER_BRIEF.md`.
- Notes for PPT designer: cierre sobrio; sin frases motivacionales.

**Speaker notes (30–45s):**
"En síntesis: Adventure Capital aporta una forma reproducible de pasar desde supuestos de negocio hasta plan financiero, valorización y diagnóstico de inversión. La contribución no es prometer una valorización perfecta; es que cada resultado queda vinculado a un supuesto, una transformación y un artefacto verificable. Las limitaciones son igual de claras: no es DD legal, no es SaaS, los múltiplos no están calibrados a mercado y M4 es robustez técnica. El valor académico está en convertir una metodología experta en un pipeline defendible, manteniendo la decisión final bajo juicio humano. Gracias."

**Evidencia:**
- `docs/defense_audit/DEFENSE_MASTER_BRIEF.md`
- `docs/defense_audit/07_red_flags_and_safe_wording.md`

**Pregunta probable:** ¿Qué haría distinto si empezara de nuevo?

**Respuesta corta:** Fijar la tesis target-driven desde el diseño inicial en vez de descubrir la sobre-expansión en revisión final; el resto de la arquitectura por capas demostró sostener bien la evolución.

---

## Apéndice A — Corrección final: de crecimiento oportunista a plan target-driven

*(usar como slide de respaldo si el comité profundiza en slide 9)*

**Mensaje principal:** La iteración final fortalece la estandarización al impedir que la optimización genere crecimiento especulativo.

**Bullets:**
- Entrega 3 ya integraba M1–M5, DD, M4, CLI y reporte HTML.
- La revisión final detectó que, con margen positivo, el modelo podía sobre-expandir adquisición.
- Se corrigió el core hacia target-driven growth.
- La tesis de inversión fija el crecimiento objetivo.
- El optimizador busca factibilidad y eficiencia de capital.
- M4 queda como robustez técnica, no como plan oficial.

**Evidencia:**
- `docs/adr/0014-growth-commitment-hiring-friction.md`
- `docs/analysis/final_growth_decision.md`
- `docs/defense_audit/16_evolution_and_version_differences.md`

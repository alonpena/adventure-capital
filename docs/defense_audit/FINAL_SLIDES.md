---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: Georgia, 'Times New Roman', serif;
    background: #FBFAF7;
    color: #1E1E1E;
    padding: 56px 64px;
  }
  h1 { font-size: 1.45em; color: #1F6F8B; }
  h2 { font-size: 1.05em; color: #6B6B6B; font-weight: normal; }
  code { font-family: 'SF Mono', Menlo, monospace; font-size: 0.85em; color: #444; }
  table { font-size: 0.72em; }
  th { background: #EFEDE8; }
  strong { color: #7A1F1F; }
  footer { color: #9A9A9A; font-size: 0.55em; }
---

<!-- _paginate: false -->

# Adventure Capital
## Evaluación financiera reproducible para startups

MVP metodológico: optimización de crecimiento, valorización DCF, due diligence y trazabilidad.

Alonso Peña · Ingeniería Civil Industrial · PUCV
Caso final: `configs/gold/gold-b2b-saas.yaml`

<!-- Voy a mostrar cómo convertí una metodología financiera de evaluación de startups en un sistema reproducible, auditable y defendible. La decisión de inversión sigue siendo humana; el sistema ordena la evidencia. -->

---

# Invertir en startups exige decidir con información incompleta

**El problema no es calcular: es hacer explícitos los supuestos que sostienen una valorización.**

- Startups: alta incertidumbre, historia corta, datos incompletos.
- La evaluación mezcla crecimiento, caja, unit economics y salida.
- Los supuestos quedan dispersos e inauditables.
- La decisión final es —y debe seguir siendo— humana.

<!-- La herramienta no elimina incertidumbre; ordena la evidencia y muestra qué supuestos sostienen o debilitan la valorización. Evidencia: CONTEXT.md, docs/DUE_DILIGENCE.md -->

---

# El mandante evaluaba con notebook y Excel: cálculo, narrativa y ejecución mezclados

- Método experto: clientes → servicios → ingresos → CAC → costos → EBITDA → EV.
- Implementación original: Colab + planillas (`legacy/`).
- Imposible separar supuestos, solver, valorización y reporte.
- Cada métrica era difícil de rastrear a su origen.

<!-- El método era correcto; el problema era reproducibilidad y auditoría. No se elimina Excel: se separa el cálculo canónico de las vistas de negocio. Evidencia: legacy/, docs/model.md -->

---

# Objetivo: MVP metodológico local con límites declarados

| Incluido | Fuera de alcance |
|---|---|
| Pipeline reproducible desde YAML | SaaS productivo |
| Optimización MILP target-driven | Due diligence legal/comercial |
| Valorización DCF + unit economics | Comparables de mercado automáticos |
| DD cuantitativo, robustez M4, reportes, UI | Automatización de la decisión |

<!-- Declarar límites es parte del diseño metodológico, no una omisión. Evidencia: README.md, END_TO_END_FLOW_CONTEXT.md -->

---

# La metodología es operacionalizable: de supuestos a plan, valor y juicio

**YAML → Validación → Instancia → MILP determinista → Valorización → DD → M4 robustez → Artefactos → UI/Reporte**

- YAML declara servicios, costos, canales, inversión y tesis de crecimiento.
- Preprocesamiento: cohortes, churn, recurrencia, descuento.
- MILP determinista genera el plan oficial target-driven.
- Post-solve: DCF, unit economics, due diligence, M4, artefactos.

Ver Diagrama 1 en `FINAL_DIAGRAMS.md`.

<!-- El solver no inventa supuestos: busca el plan factible y eficiente bajo lo declarado. Evidencia: config.py, instance.py, model.py, valuation.py -->

---

# El entregable cumple el alcance definido

| Objetivo | Artefacto | Lectura defendible |
|---|---|---|
| Formalización de datos | `config.yaml`, `artifacts_manifest.json` | Supuestos trazables |
| DD cuantitativo | `due_diligence_report.md` | No reemplaza DD legal/comercial |
| Plan de crecimiento | `optimized_results.csv` | Plan oficial determinístico |
| Valorización/unit economics | `valuation_summary.json`, `unit_economics.csv` | Trazable a supuestos |
| Robustez | `stochastic_summary.csv` o bloqueo DD | Robustez técnica, no plan oficial |
| Informe automático | `report.html` (PDF si WeasyPrint) | Auditable y descargable |
| Validación | `pytest`: 186 passed, 3 skipped | Reproducibilidad técnica |

<!-- El sistema operacionaliza los objetivos comprometidos en una metodología reproducible, trazable y auditable. Cada fila tiene evidencia ejecutable y un límite declarado. -->

---

# Arquitectura modular: cálculo, juicio y presentación viven separados

- `configs/` — supuestos versionables (YAML).
- `src/adventure_capital/` — core financiero + MILP + valorización: **fuente de verdad**.
- `due_diligence/`, `stochastic/` — juicio estructurado y robustez.
- `standard_report/` + Streamlit — presentación que consume artefactos, **nunca recalcula**.

Ver Diagrama 2 en `FINAL_DIAGRAMS.md`.

<!-- Dependencia unidireccional. Auditar el sistema es auditar archivos, no pantallas. Evidencia: 01_repo_architecture_audit.md -->

---

# Cada resultado se rastrea de supuesto a artefacto descargable

- YAML → instancia congelada (`model_instance.json`).
- Núcleo: plan mensual canónico (`optimized_results.csv`).
- Derivados: `valuation_summary.json`, `unit_economics.csv`, `due_diligence_report.md`.
- Auditoría: `formula_trace.json` + `artifacts_manifest.json`.

Ver Diagrama 3 en `FINAL_DIAGRAMS.md`.

<!-- Respuesta operativa a "¿de dónde sale este número?". Trazabilidad técnica y reproducible; no auditoría legal/contable total. Evidencia: 15_input_output_traceability.md -->

---

# La tesis de inversión fija el crecimiento; el optimizador busca ejecución eficiente

- Tesis por defecto: **C36 ≥ 3·C12** (triplicar stock entre mes 12 y 36).
- `growth_commitment` es piso; `acquisition_envelope` acota el camino con slack declarado.
- VAN y MoM son consecuencias del plan, no parámetros calibrados.
- Infeasible = diagnóstico de negocio, no bug.

<!-- Corrección final: Entrega 3 ya integraba M1–M5, DD, M4, CLI y reporte HTML. La revisión final detectó que, con margen positivo, el modelo podía sobre-expandir adquisición. Se corrigió el core hacia target-driven growth: la tesis de inversión fija el crecimiento objetivo; el optimizador busca factibilidad y eficiencia de capital; M4 queda como robustez técnica, no como plan oficial. Evidencia: docs/adr/0014-growth-commitment-hiring-friction.md, docs/analysis/final_growth_decision.md, tests/test_acquisition_envelope.py -->

---

# Due diligence actúa como gate: decide si los resultados merecen interpretarse

- Evalúa inputs, outputs deterministas, calibración y liquidez.
- Veredictos graduados: passed → warnings → minor/major adjustment → rejected_for_stochastic.
- El veredicto habilita o bloquea M4 y condiciona la lectura de la valorización.
- **No es due diligence legal** ni recomendación automática de inversión.

<!-- Gate real en corridas del repo: passed_with_warnings (beloop), requires_major_adjustment (caso base), rejected_for_stochastic (godemos bench). Estructura y hace trazable el juicio experto. Evidencia: docs/DUE_DILIGENCE.md, due_diligence/ -->

---

# Resultados del caso final: plan, valor y veredicto trazables a un solo YAML

- Instancia: `configs/gold/gold-b2b-saas.yaml` — ejecución: `outputs/executions/run_20260706-045427_28a63258`
- VAN (DCF): `USD 4,583,212`
- Ingresos año 3: `USD 4,503,277` — EBITDA año 3: `USD 3,557,712`
- Veredicto DD: `passed_with_warnings`

*Resultados condicionales a supuestos declarados; no es predicción de mercado.*

<!-- Lo defendible es la condición del número: consecuencia de un plan factible bajo tesis declarada, con veredicto explícito. Cambiar un supuesto regenera todo el análisis. Evidencia: outputs/executions/run_20260706-045427_28a63258/valuation_summary.json -->

---

# La UI es una capa de consulta: los artefactos son la fuente de verdad

**Demo:** seleccionar ejecución → informe ejecutivo → plan de crecimiento → valoración → DD → robustez → artefactos

- Gestión de instancias y ejecuciones desde Streamlit.
- Fuente de verdad: `outputs/executions/<run>/`, no widgets.
- Reporte HTML descargable por corrida.

Screenshot: `[PENDIENTE: capturar screenshot UI — sugerido docs/defense_audit/assets/ui_informe_ejecutivo.png]`

<!-- La UI consume artefactos generados: si borro la UI, los resultados siguen intactos y auditables en disco. Evidencia: app.py, streamlit_pages/ -->

---

# Validación: el sistema diagnostica, incluso cuando el caso es malo

Tests: `uv run pytest -q` → **186 passed, 3 skipped**

| Caso benchmark | VAN core | Ingresos Y3 | Veredicto DD |
|---|---:|---:|---|
| godemos | 942.635 | 1.038.995 | requires_minor_adjustment |
| entrena-en-casa | −69.622 | 304.266 | requires_major_adjustment |
| beloop | 1.973.394 | 2.618.430 | passed_with_warnings |
| kavacomex | −416.453 | 217.140 | requires_major_adjustment |

*Benchmark identifica brechas y soporta calibración; no es validación universal.*

<!-- Un sistema que solo produce buenas noticias no sirve para due diligence. Los 4 casos resuelven Optimal bajo commitment + envelope. Evidencia: docs/analysis/growth_commitment_benchmarks.md -->

---

# Aporte: una metodología experta convertida en pipeline defendible y auditable

| Contribuciones | Limitaciones | Roadmap |
|---|---|---|
| Pipeline reproducible YAML→artefactos | MVP local, no SaaS | API/SaaS, DB, jobs |
| DD como gate metodológico | DD financiero, no legal | Calibración con datos externos |
| Plan oficial determinista target-driven | Múltiplos de referencia | Recourse estocástico |
| Trazabilidad supuesto→resultado | Benchmark acotado (4 casos) | Más casos de calibración |

**Herramienta para mejor juicio experto, no sustituto.**

<!-- Cierre: cada resultado queda vinculado a un supuesto, una transformación y un artefacto verificable. La decisión final permanece bajo juicio humano. Gracias. -->

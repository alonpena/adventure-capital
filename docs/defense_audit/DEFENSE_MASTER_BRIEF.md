# DEFENSE MASTER BRIEF

## Qué Construí

Un MVP metodológico local para evaluación de startups: YAML -> modelo financiero mensual -> optimización MILP -> valorización DCF/EV -> due diligence -> artefactos/reportes/UI. La herramienta convierte un proceso antes ad hoc en un flujo reproducible y auditable técnicamente.

## Por Qué Importa

- Reduce dependencia de cálculos manuales dispersos.
- Explicita supuestos y evidencia.
- Permite iterar planes de crecimiento bajo restricciones operacionales.
- Separa cálculo, juicio DD y presentación.
- Deja trazabilidad para defensa, consultor y comité.

## Cómo Funciona

1. YAML define servicios, costos, adquisición base, canales, inversión, solver y tesis de crecimiento.
2. `instance.py` normaliza cohortes, churn, recurrencia, descuentos y restricciones target-driven.
3. `model.py` resuelve MILP con PuLP/CBC.
4. `valuation.py` y `unit_economics.py` calculan VAN, múltiplos y métricas cliente.
5. `due_diligence/` clasifica hallazgos y decide interpretación/gate de M4.
6. `standard_report/`, `simple_report.py` y Streamlit muestran artefactos, no reescriben la verdad del modelo.

## Resultados Que Tengo

- Tests: `186 passed, 3 skipped`.
- Benchmarks growth core: 4 casos `benchmark_v0` resueltos como Optimal bajo commitment + envelope; ver `docs/analysis/growth_commitment_benchmarks.md`.
- Ejecuciones históricas en `outputs/executions/` con reportes, DD y valorizaciones.
- Falta gold final: usar placeholders hasta definir `{{GOLD_RUN_PATH}}`.

## Evidencia Principal

| Claim | Evidencia |
|---|---|
| pipeline reproducible | `config.py`, `pipeline.py`, `outputs/*/config.yaml` |
| MILP implementado | `model.py`, `tests/test_phase2.py` |
| target-driven growth | ADR 0014, `tests/test_acquisition_envelope.py` |
| DD implementado | `docs/DUE_DILIGENCE.md`, `due_diligence/` |
| DCF/EV | `valuation.py`, `valuation_summary.json` |
| UI artifact-driven | `app.py`, `streamlit_pages/components.py` |
| M4 robustez | ADR 0015, `stochastic/` |

## Qué Debo Decir

- “MVP metodológico para estandarizar evaluación financiera de startups.”
- “El plan oficial es determinista y target-driven.”
- “M4 entrega robustez técnica bajo escenarios, no reemplaza el plan.”
- “Los artefactos hacen trazable el camino input-output.”
- “La decisión final permanece bajo juicio experto.”

## Qué No Debo Decir

- No “SaaS completo”.
- No “due diligence legal”.
- No “robust optimization” sin matiz.
- No “múltiplos calibrados al mercado”.
- No “automático/reemplaza consultor”.
- No usar benchmarks como gold final si no están designados.

## Placeholders Pendientes

`{{GOLD_RUN_PATH}}`, `{{GOLD_INSTANCE}}`, `{{VAN}}`, `{{REVENUE_Y3}}`, `{{DD_VERDICT}}`, `{{REPORT_HTML_PATH}}`, `{{SCREENSHOT_UI_PATH}}`.


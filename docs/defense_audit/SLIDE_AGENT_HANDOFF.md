# SLIDE AGENT HANDOFF

## Core Storyline

Adventure Capital transforma una evaluación financiera ad hoc de startups en un pipeline reproducible: supuestos YAML, modelo financiero mensual, optimización determinista target-driven, valorización DCF/EV, due diligence, análisis de robustez y reportes/UI basados en artefactos.

## 14-Slide Structure

| # | Título exacto | Bullets | Visual | Speaker notes | Evidencia |
|---|---|---|---|---|---|
| 1 | Adventure Capital: evaluación financiera reproducible para startups | Autor, carrera, mandante, fecha | portada limpia | Presentar tesis como MVP metodológico | `README.md` |
| 2 | Contexto: decisiones VC con información incompleta | startups, incertidumbre, supuestos dispersos | embudo VC | Problema de estandarización | `CONTEXT.md` |
| 3 | Mandante y método Alejandro | clientes->servicios->ingresos->costos->EV | cadena de valor | Conectar negocio y modelo | `docs/model.md` |
| 4 | Problema: notebook/Excel no bastaban | poca trazabilidad, difícil reproducir, reportes manuales | before/after | No criticar Excel; mostrar necesidad | `legacy/`, `PLAN.md` |
| 5 | Objetivo y alcance del MVP | pipeline local, DD, reportes, UI, no SaaS | scope box | Marcar límites | `END_TO_END_FLOW_CONTEXT.md` |
| 6 | Evolución: Colab -> CLI -> pipeline/UI | legacy, package, CLI, Streamlit | timeline | Evidencia de ingeniería | `legacy/`, `cli.py`, `app.py` |
| 7 | Metodología propuesta | YAML, instancia, MILP, DCF, DD | pipeline corto | Explicar módulos | `src/adventure_capital/` |
| 8 | Flujo end-to-end auditable | config->solve->artifacts->report | Mermaid pipeline | Cada output tiene fuente | `reporting.py` |
| 9 | Due diligence como capa de juicio | reglas, severidad, gates, recomendaciones | tabla verdict | No legal DD | `docs/DUE_DILIGENCE.md` |
| 10 | Valorización y Enterprise Value | DCF, terminal, unit economics, múltiplos ref | waterfall DCF | Cautela con múltiplos | `valuation.py` |
| 11 | Crecimiento target-driven | C36>=3*C12, envelope, no ceiling arbitrario | stock path | VAN consecuencia, no calibración | ADR 0014 |
| 12 | Riesgo y robustez | LHS, SAA, CVaR, ex-post, no plan oficial | distribución VAN | ADR 0015 framing | `stochastic/` |
| 13 | UI/demo y artefactos | report.html, CSV/JSON, Streamlit reads outputs | screenshot/report | UI no recalcula verdad | `app.py`, `outputs/` |
| 14 | Contribuciones, limitaciones y futuro | reproducibilidad, trazabilidad, límites, roadmap | 3-column close | Cierre honesto | `07_red_flags...` |

## Safe Claims

- Pipeline reproducible con YAML y artefactos.
- Plan oficial determinista target-driven.
- DD implementado como gate financiero/metodológico.
- M4 es robustez técnica, no plan oficial.
- UI local consume artefactos.

## Unsafe Claims To Avoid

- SaaS productivo.
- Due diligence legal.
- Market-calibrated multiples.
- Robust optimization formal.
- Automatización completa de decisión de inversión.

## Pending Placeholders

`{{GOLD_RUN_PATH}}`, `{{VAN}}`, `{{REVENUE_Y3}}`, `{{DD_VERDICT}}`, `{{SCREENSHOT_UI_PATH}}`.


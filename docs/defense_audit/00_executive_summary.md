# 00 Executive Summary

Estado auditado: rama `defense-slide-material`, creada desde `demo-integrated-growth-ui` porque esa es la rama más reciente y `demo-integrated-growth-ui` ya estaba abierta en otro worktree. No se modificó lógica de modelo.

## Tesis Técnica

Adventure Capital es un MVP metodológico para estandarizar evaluación de startups: toma supuestos en YAML, genera una instancia financiera mensual, optimiza un plan de crecimiento acelerado con MILP, calcula valorización/Unit Economics, aplica Due Diligence y emite artefactos auditables para informe/UI.

## Historia Central Para Defensa

- Antes: evaluación ad hoc en notebook/Excel, difícil de auditar y reproducir.
- Ahora: pipeline modular con contratos de entrada/salida, artefactos CSV/JSON, reportes HTML y UI Streamlit sobre resultados.
- Núcleo actual: plan determinista target-driven; el crecimiento se ancla en la tesis de inversión y el plan consensuado.
- Riesgo/M4: análisis de robustez y artefacto técnico; no reemplaza el plan determinista oficial del MVP.
- Decisión final sigue bajo juicio experto; la herramienta estructura evidencia y reduce ambigüedad.

## Estado de Evidencia

| Área | Estado | Evidencia |
|---|---|---|
| Arquitectura modular | implementado | `src/adventure_capital/`, `pyproject.toml`, `README.md` |
| YAML input | implementado | `configs/*.yaml`, `src/adventure_capital/config.py` |
| Optimización determinista MILP | implementado | `src/adventure_capital/model.py`, `tests/test_phase2.py` |
| Growth target-driven | implementado opt-in/core demo docs | `docs/adr/0014-growth-commitment-hiring-friction.md`, `tests/test_acquisition_envelope.py` |
| DD gates | implementado | `src/adventure_capital/due_diligence/`, `docs/DUE_DILIGENCE.md` |
| DCF/EV/unit economics | implementado | `src/adventure_capital/valuation.py`, `src/adventure_capital/unit_economics.py` |
| M4 stochastic | implementado como robustez técnica | `src/adventure_capital/stochastic/`, `docs/adr/0015-m4-mvp-robustness-diagnostic.md` |
| UI Streamlit | implementado local | `app.py`, `streamlit_pages/` |
| SaaS/API producción | futuro/no implementado | `docs/END_TO_END_FLOW_CONTEXT.md` |

## Métricas Pendientes

No existe carpeta `outputs/gold` ni corrida gold explícita encontrada. Usar placeholders hasta fijar corrida final:

- `{{GOLD_RUN_PATH}}`
- `{{GOLD_INSTANCE}}`
- `{{VAN}}`
- `{{REVENUE_Y3}}`
- `{{DD_VERDICT}}`
- `{{REPORT_HTML_PATH}}`
- `{{SCREENSHOT_UI_PATH}}`


# 16 Evolution And Version Differences

## Evolución

| Etapa | Evidencia | Estado |
|---|---|---|
| Colab notebook | `legacy/optimizacion_plan_crecimiento_acelerado_v3 (1).py` | legado |
| Paquete Python | `src/adventure_capital/`, `pyproject.toml` | implementado |
| CLI pipeline | `cli.py`, README | implementado |
| Reportes/artefactos | `reporting.py`, `standard_report/` | implementado |
| DD | `due_diligence/`, ADR 0005 | implementado |
| M4 stochastic | `stochastic/`, ADR 0015 | técnico/robustez |
| UI Streamlit | `app.py`, `streamlit_pages/` | local/demo |
| SaaS | docs futuro | no implementado |

## Version Differences

`entrega-tesis` queda como fallback estable. `demo-integrated-growth-ui` incorpora integración de growth core/UI más reciente. Este pack se creó en rama nueva desde latest branch para no tocar `entrega-tesis`.


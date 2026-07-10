# 17 Presentation Evidence Pack

## Checks Ejecutados

| Comando | Resultado | Nota |
|---|---|---|
| `uv run pytest -q` | `186 passed, 3 skipped` | requiere acceso a cache `~/.cache/uv`; warnings PuLP/pre-feasibility |
| `uv run ruff check app.py streamlit_pages src/adventure_capital` | falla | 9 lint issues preexistentes, no corregidos por docs-only |
| `git diff --check` | pasa | sin whitespace errors |

## Top Artifacts Para Mostrar

| Artefacto | Por qué mostrar |
|---|---|
| `optimized_results.csv` | plan mensual canónico |
| `valuation_summary.json` | VAN/EV |
| `due_diligence_report.md` | juicio y recomendaciones |
| `formula_trace.json` | trazabilidad |
| `report.html` | salida ejecutiva |
| `dashboard.png` | visual rápido |
| `growth_suggestions.json` | tesis crecimiento/growth diagnostics si existe |
| `artifacts_manifest.json` | mapa de outputs |
| `stochastic_summary.csv` | robustez, cauteloso |
| `config.yaml` | reproducibilidad |

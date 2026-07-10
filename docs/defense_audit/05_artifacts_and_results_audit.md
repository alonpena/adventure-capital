# 05 Artifacts And Results Audit

## Inventario De Artefactos

| Artefacto | Existe en runs/benchmarks | Preparado defensa | Nota |
|---|---:|---:|---|
| `optimized_results.csv` | sí | sí | plan mensual canónico |
| `fixed_cashflow.csv` | sí | sí | primeros 12 meses |
| `dcf_cashflow.csv` | sí | sí | DCF mensual |
| `dcf_annual_summary.csv` | sí | sí | agregación anual |
| `valuation_summary.json` | sí | sí | VAN/DCF |
| `unit_economics.csv` | sí | sí | CAC/LTV |
| `due_diligence_report.json/md` | sí | sí | veredicto/recomendaciones |
| `calibration_report.json/md` | sí | sí | checks técnicos |
| `formula_trace.json` | sí | muy fuerte | trazabilidad formulas |
| `mapvalue.json` | sí en varias ejecuciones | medio | insumo reporte |
| `report.html` | sí | fuerte para demo |
| `report.pdf` | no confirmado | placeholder | depende WeasyPrint |
| `stochastic_summary.csv` | sí en algunas ejecuciones | cauteloso | robustez, no plan oficial |
| `saa_solution.json` | sí en algunas ejecuciones | técnico | no mostrar como plan oficial |

## Runs Relevantes

| Run | Estado | VAN | DD | Uso sugerido |
|---|---|---:|---|---|
| `outputs/executions/run_20260701-115401_c54fa2f1` | failed por M4/report stage | 3,157,381 | passed_with_warnings | ejemplo UI/artifacts, no gold |
| `outputs/executions/run_20260701-115242_a8cf74ae` | blocked | -75,818 | requires_major_adjustment | ejemplo DD bloquea M4 |
| `outputs/executions/run_20260624-164936_c54fa2f1` | completed | 3,157,381 | passed_with_warnings | ejemplo completo antiguo |
| `benchmark_v1/*_det` | variados | ver archivos | variados | evidencia benchmark, no gold |

## Pendiente Gold Final

No se encontró `outputs/gold`. Completar manualmente:

| Campo | Placeholder |
|---|---|
| ruta | `{{GOLD_RUN_PATH}}` |
| instancia | `{{GOLD_INSTANCE}}` |
| VAN | `{{VAN}}` |
| ingresos año 3 | `{{REVENUE_Y3}}` |
| veredicto DD | `{{DD_VERDICT}}` |
| reporte | `{{REPORT_HTML_PATH}}` |


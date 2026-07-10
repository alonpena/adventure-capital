# 15 Input Output Traceability

| Input | Transformación | Output | Evidencia |
|---|---|---|---|
| `configs/*.yaml` | `load_config`, `validate_config` | config dict | `config.py` |
| `servicios[*].A_base` | fixed period | `fixed_cashflow.csv` | `financial_model.py` |
| service params | instance preprocessing | `model_instance.json` | `instance.py`, `reporting.py` |
| instance | MILP solve | `optimized_results.csv` | `model.py`, `results.py` |
| results | DCF | `dcf_cashflow.csv`, `valuation_summary.json` | `valuation.py` |
| results | Unit Economics | `unit_economics.csv` | `unit_economics.py` |
| artifacts | calibration/DD | `calibration_report.*`, `due_diligence_report.*` | `calibration/`, `due_diligence/` |
| artifacts + doc YAML | report package | `report_data.json`, `artifacts_manifest.json` | `standard_report/package.py` |
| report data | render | `report.html`, optional `report.pdf` | `standard_report/render.py` |

Traceability claim: técnica y reproducible. No afirmar auditoría legal/contable total.


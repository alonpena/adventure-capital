# Intermediate Artifacts Specification

Status: draft contract for artifact standardization.  
Scope: no implementation requirements beyond defining expected files, fields, purpose, owners, and consumers.

## 1. Artifact philosophy

Adventure Capital should preserve the operational readability of the original Excel/Colab workflow without rebuilding Excel as the primary system. The replacement is a structured artifact package: CSV for tabular inspection, JSON for machine-readable contracts, and HTML/PDF for business-facing delivery.

Two audiences must be separated:

| Audience | Needs | Artifact style |
|---|---|---|
| Entrepreneur / investor | Spanish summaries, clear valuation, growth plan, risks, charts | `report.html`, `report.pdf`, selected CSV extracts, dashboards |
| Technical / audit | reproducibility, traceability, solver status, formulas, intermediate variables, scenario distributions | YAML input, normalized instance JSON, full CSVs, manifest, report data package |

The canonical end-to-end flow is:

```text
startup.yaml
→ model_instance.json
→ deterministic optimization
→ accelerated growth plan artifacts
→ valuation + unit economics workbook
→ due diligence assessment
→ stochastic optimization if DD allows
→ Monte Carlo ex-post evaluation
→ HTML/PDF valuation report
→ future UI/form workflow
```

## 2. Folder layout

Suggested output layout per run:

```text
outputs/<run_id>/
├── inputs/
│   ├── startup.yaml                  # original user/model config copy
│   ├── report_document.yaml           # optional narrative/report YAML copy
│   └── model_instance.json            # normalized generated instance
├── deterministic/
│   ├── fixed_cashflow.csv
│   ├── optimized_results.csv
│   ├── growth_plan_summary.json
│   └── dashboard.png
├── valuation/
│   ├── dcf_cashflow.csv
│   ├── dcf_annual_summary.csv
│   ├── multiples_valuation.csv
│   ├── unit_economics.csv
│   ├── valuation_summary.json
│   └── formula_trace.json
├── due_diligence/
│   ├── due_diligence_report.json
│   ├── due_diligence_report.md
│   ├── calibration_report.json
│   ├── calibration_report.md
│   └── assessment_summary.json
├── stochastic/
│   ├── lhs_scenarios.csv
│   ├── saa_solution.json
│   ├── stochastic_scenarios.csv
│   ├── stochastic_summary.csv
│   ├── stochastic_breakeven.csv
│   └── stochastic_diagnostics.json
├── report/
│   ├── report_data.json
│   ├── artifacts_manifest.json
│   ├── figures/*.png
│   ├── report.html
│   └── report.pdf
└── ui/
    └── ui_payload.json                # future form/report explorer payload
```

Current implementation writes most files flat under `outputs/<run_id>/`. This spec defines the target contract. A compatibility layer may keep flat filenames while adding folders later.

## 3. Artifact catalog

### 3.1 Input and normalized instance

| File | User | Purpose | Source module | Downstream consumer |
|---|---|---|---|---|
| `startup.yaml` / `config.yaml` | technical/audit | preserve original run input | CLI/pipeline | all stages, UI rerun |
| `report_document.yaml` | report author | narrative/report-only inputs | CLI/report package | standard report |
| `model_instance.json` | technical/audit | normalized instance after preprocessing | `instance.generate_instance` | deterministic, stochastic, report trace |

Minimal `model_instance.json` fields:

| Field | Meaning |
|---|---|
| `schema_version` | artifact schema version |
| `created_at` | ISO timestamp |
| `source_config` | relative path or hash |
| `H`, `T`, `T_base`, `S` | horizon/month/service sets |
| `servicios` | service parameters used by model |
| `A_base` | fixed first-year acquisition by service/month |
| `phi`, `delta`, `alpha` | survival, repurchase-window, repurchase-rate parameters |
| `descuento`, `beta`, `beta_anual` | discount factors |
| `channels` | normalized commercial channel availability and coefficients |
| `log_ceiling`, `ceiling_slack` | acquisition ceiling, if enabled |
| `parametros_hash` | reproducibility hash of config |

### 3.2 Accelerated growth plan artifacts

| File | User | Purpose | Source module | Downstream consumer |
|---|---|---|---|---|
| `fixed_cashflow.csv` | entrepreneur + audit | first 12 months deterministic cashflow from `A_base` | `financial_model.py` | report, comparison, UI |
| `optimized_results.csv` | entrepreneur + audit | monthly optimized growth plan and financial trajectory | `results.py` | DCF, unit economics, DD, report, stochastic comparison |
| `growth_plan_summary.json` | entrepreneur | concise growth plan KPIs | `results.py` / pipeline | UI cards, report summary |
| `dashboard.png` | entrepreneur | quick visual check | `reporting.py` | basic report |

Minimal `optimized_results.csv` fields:

| Field group | Required fields |
|---|---|
| Period | `t`, `Año`, `Mes` |
| Commercial | `Vendedores`, `Lideres`, `Adq_clientes` |
| Service detail | `A_<service>`, `C_<service>`, `R_<service>`, `Q_<service>`, `I_<service>`, `Cost_op_<service>`, `m_op_<service>` |
| Channel detail, if enabled | `A_salesforce`, `A_advertising`, `A_third_party`, `advertising_investment`, `share_salesforce`, `share_advertising`, `share_third_party` |
| CAC trace | `CAC`, `salesforce_cac_cost`, `advertising_cac_cost`, `third_party_cost`, `total_acquisition_cost`, `period_cac_per_user`, `cumulative_cac_per_user` |
| Financials | `Ingresos`, `Costo_operacional`, `G_adm`, `RRHH`, `EBITDA`, `Caja` |
| Diagnostics | `EBITDA_acum`, `MoM_adq`, `MoM_ingresos`, `ARR_pct` |
| Working capital, if enabled | `working_capital_floor`, `floor_slack`, `floor_hit`, `diagnostic_financing_gap` |

Minimal `growth_plan_summary.json` fields:

```json
{
  "schema_version": "1.0",
  "solver_status": "Optimal",
  "objective_value": 0.0,
  "total_acquisition": 0.0,
  "total_revenue": 0.0,
  "total_ebitda": 0.0,
  "final_cash": 0.0,
  "minimum_cash": 0.0,
  "max_sellers": 0.0,
  "max_leaders": 0.0,
  "enabled_channels": ["salesforce"]
}
```

### 3.3 Valuation and unit economics workbook artifacts

| File | User | Purpose | Source module | Downstream consumer |
|---|---|---|---|---|
| `dcf_cashflow.csv` | entrepreneur + audit | monthly DCF flow | `valuation.py` | report, formula trace |
| `dcf_annual_summary.csv` | entrepreneur | annual aggregation for report | `valuation.py` | report tables |
| `multiples_valuation.csv` | entrepreneur + audit | revenue/EBITDA multiple reference | `valuation.py` | report, sensitivity |
| `unit_economics.csv` | entrepreneur | customer-level economics and operational ratios | `unit_economics.py` | DD, report, UI |
| `valuation_summary.json` / current `summary.json` | entrepreneur + audit | top-line valuation metrics | `reporting.py` | report hero, UI |
| `formula_trace.json` | audit | formulas, source columns, assumptions | target artifact | workbook/report trust layer |

Minimal `dcf_cashflow.csv` fields:

` t, Año, Ingresos, Costo_operacional, CAC, G_adm, RRHH, EBITDA, Impuesto, FC_neto, Factor_desc, FC_desc `

Minimal `dcf_annual_summary.csv` fields:

` Año, Ingresos, Costo_operacional, CAC, G_adm, RRHH, EBITDA, Impuesto, FC_neto, FC_desc `

Minimal `multiples_valuation.csv` fields:

` Método, Base, Múltiplo, Valorización `

Minimal `unit_economics.csv` fields:

` Unit Economic, Definición, Fórmula / Fuente, Valor, Unidad `

Minimal `valuation_summary.json` fields:

```json
{
  "schema_version": "1.0",
  "vc_invested": 0.0,
  "van": 0.0,
  "vp_flujos": 0.0,
  "valor_desecho_nominal": 0.0,
  "valor_desecho_vp": 0.0,
  "beta_anual": 0.0,
  "beta_mensual": 0.0,
  "ebitda_ultimo_mes": 0.0,
  "ebitda_anualizado": 0.0,
  "multiples": {
    "ingresos": 0.0,
    "ebitda": 0.0
  },
  "unit_economics": {
    "CAC": 0.0,
    "LTV": 0.0,
    "LTV/CAC": 0.0,
    "ARPU": 0.0,
    "ARR": 0.0,
    "Bootstrapping": 0.0
  }
}
```

### 3.4 Due diligence assessment artifacts

| File | User | Purpose | Source module | Downstream consumer |
|---|---|---|---|---|
| `due_diligence_report.json` | audit + UI | structured DD verdict and findings | `due_diligence/report.py` | stochastic gate, report, UI |
| `due_diligence_report.md` | entrepreneur | Spanish DD explanation | `due_diligence/report.py` | report appendix, review |
| `calibration_report.json` | audit | calibration checks consumed by DD | `calibration/report.py` | DD, UI |
| `calibration_report.md` | entrepreneur + audit | readable calibration summary | `calibration/report.py` | review |
| `assessment_summary.json` | audit + UI | run-level DD/stochastic linkage | `due_diligence/workflow.py` | report, UI status |

Minimal `due_diligence_report.json` fields:

| Field | Meaning |
|---|---|
| `schema_version` | DD report schema |
| `verdict` | `passed`, `passed_with_warnings`, `requires_minor_adjustment`, `requires_major_adjustment`, `rejected_for_stochastic` |
| `allows_stochastic` | whether stochastic stage may run |
| `valuation_mode` | `final`, `warning`, `diagnostic`, `none` |
| `adjustment_level` | `none`, `minor`, `major`, `structural` |
| `rerun_recommended` | boolean |
| `blocking_reasons` | structural blockers |
| `adjustment_recommendations` | recommended recalibrations |
| `calibration_verdict` | PASS/WARN/FAIL |
| `liquidity_diagnostic` | min cash, funding gap, breakeven, final cash |
| `findings[]` | per-rule details |

Feasibility policy: DD filters startup/VC feasibility before stochastic. Financing and liquidity diagnostics remain outside the stochastic objective unless future academic work explicitly chooses a risk-averse formulation.

### 3.5 Stochastic assessment artifacts

| File | User | Purpose | Source module | Downstream consumer |
|---|---|---|---|---|
| `lhs_scenarios.csv` | audit | SAA scenario sample generated by LHS | target `stochastic/scenarios.py` | SAA model |
| `saa_solution.json` | audit + UI | selected stochastic growth plan | target `stochastic/model.py` | Monte Carlo evaluator, UI |
| `stochastic_scenarios.csv` | audit | full out-of-sample scenario evaluation | `stochastic/evaluate.py` | stochastic summary, report |
| `stochastic_summary.csv` | entrepreneur + audit | distribution summary | `stochastic/results.py` | report, UI |
| `stochastic_breakeven.csv` | entrepreneur + audit | breakeven distribution | `stochastic/results.py` | report, UI |
| `stochastic_diagnostics.json` | audit + UI | DD-style probabilities and scenario-risk metrics | target artifact | report risk section |

Minimal `lhs_scenarios.csv` fields:

` scenario, probability, seed, sample_index, churn_multiplier_<service>, salesforce_productivity_multiplier, advertising_effectiveness_multiplier, third_party_productivity_multiplier, wacc_value, ticket_multiplier_<service>, op_cost_multiplier_<service>, recurrence_multiplier_<service>, vc_multiplier `

Only include channel-specific columns when channel is enabled in YAML.

Minimal `saa_solution.json` fields:

```json
{
  "schema_version": "1.0",
  "status": "Optimal",
  "objective": "expected_npv",
  "expected_objective": 0.0,
  "scenario_count": 100,
  "strategy": {
    "A": {},
    "A_salesforce": {},
    "A_advertising": {},
    "A_third_party": {},
    "advertising_investment": {},
    "V": {},
    "L": {}
  },
  "nonanticipativity": ["A", "A_salesforce", "A_advertising", "A_third_party", "advertising_investment", "V", "L"],
  "notes": ["Risk metrics are evaluation outputs, not objective penalties."]
}
```

Minimal `stochastic_scenarios.csv` fields:

` scenario, probability, VAN, total_ebitda, final_cash, funding_gap, breakeven_month, total_acquisition, final_clients, total_revenue, total_cac, cac_per_customer, ltv_cac, dd_verdict_proxy, vc_feasible_proxy, enabled_channels `

Minimal `stochastic_summary.csv` fields:

` n_scenarios, expected_van, van_p10, van_p50, van_p90, prob_van_negative, prob_funding_gap, expected_funding_gap, max_funding_gap, prob_dd_fail, prob_miss_vc_criteria, cac_p10, cac_p50, cac_p90, final_clients_p10, final_clients_p50, final_clients_p90, revenue_p10, revenue_p50, revenue_p90 `

### 3.6 Report/UI package artifacts

| File | User | Purpose | Source module | Downstream consumer |
|---|---|---|---|---|
| `report_data.json` | report renderer + UI | normalized report data package | `standard_report/package.py` | HTML/PDF, UI |
| `artifacts_manifest.json` | all users | artifact index, validation checks, source mapping | `standard_report/package.py` | UI, QA, reproducibility |
| `figures/*.png` | entrepreneur | report-ready figures | `standard_report/charts.py` | HTML/PDF |
| `report.html` | entrepreneur/investor | primary valuation report | `standard_report/render.py` | browser/UI |
| `report.pdf` | entrepreneur/investor | portable report | `standard_report/render.py` | delivery |
| `ui_payload.json` | future UI | form/report explorer payload | target artifact | web UI |

Minimal `artifacts_manifest.json` fields:

| Field | Meaning |
|---|---|
| `schema_version` | manifest schema |
| `created_at` | timestamp |
| `inputs` | config, document, schema, output dir |
| `artifacts` | file key to relative path |
| `checks.valid` | package validity |
| `checks.missing_core_artifacts` | missing required CSVs |
| `checks.missing_document_fields` | missing narrative inputs |
| `stage_status` | optional per-stage pass/skipped/failed |

Minimal `ui_payload.json` fields:

```json
{
  "schema_version": "1.0",
  "run_id": "demo-complex",
  "inputs": {},
  "stage_status": {},
  "kpis": {},
  "artifacts": {},
  "download_links": {},
  "warnings": [],
  "unsafe_claims": []
}
```

## 4. Required contract decisions before UI/report standardization

P0 artifact gaps:

1. Add `model_instance.json` to make preprocessing auditable.
2. Add `formula_trace.json` for DCF/unit economics traceability.
3. Add `growth_plan_summary.json` and `valuation_summary.json` rather than relying only on CSV parsing.
4. Standardize stochastic `lhs_scenarios.csv`, `saa_solution.json`, and diagnostics fields.
5. Extend `artifacts_manifest.json` with stage statuses and artifact audience tags.

P1 artifact gaps:

1. Keep flat-file compatibility during migration.
2. Add schema files for major JSON artifacts.
3. Add artifact-version tests.
4. Add UI payload only after core artifact contracts are stable.

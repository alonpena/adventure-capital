# End-to-End Flow Context

Status: system context for artifact, report, and future UI standardization.  
Scope: no code implementation. Defines how existing and target stages connect.

## 1. Intended full flow

```text
startup.yaml
  ↓
model_instance.json
  ↓
deterministic optimization
  ↓
accelerated growth plan artifacts
  ↓
valuation + unit economics workbook
  ↓
due diligence assessment
  ↓
stochastic optimization if DD allows
  ↓
Monte Carlo ex-post evaluation
  ↓
HTML/PDF valuation report
  ↓
future UI/form workflow
```

The deterministic model remains the baseline. Due diligence is the interpretation and eligibility layer. Stochastic optimization is not isolated; it is invoked only after DD decides the case is structurally valid and should be analyzed.

## 2. Stage responsibilities

| Stage | Input | Output | Responsibility | Not responsible for |
|---|---|---|---|---|
| YAML/form input | user form or `startup.yaml` | raw config | collect startup assumptions and report narrative | solving model |
| Instance preprocessing | `startup.yaml` | `model_instance.json` | normalize periods, cohorts, channels, discount factors | optimization decisions |
| Deterministic optimization | model instance | growth plan artifacts | find accelerated growth plan under base assumptions | uncertainty analysis |
| Valuation workbook | optimized results | DCF, unit economics, valuation summary | compute valuation and customer economics | DD verdict |
| Due diligence | YAML + deterministic outputs + calibration | DD verdict and recommendations | structural/startup/financing filter and interpretation | stochastic objective penalties |
| Stochastic optimization | YAML + DD approval + scenario sample | SAA-selected plan | optimize expected NPV under uncertainty | preset policy comparison |
| Monte Carlo evaluation | fixed SAA plan + independent scenarios | distribution/risk artifacts | evaluate downside and DD/VC risk metrics | re-solving each scenario |
| Report package | all artifacts + report document | `report_data.json`, manifest, figures | normalize for rendering/UI | core model logic |
| HTML/PDF render | report package | report | business-facing delivery | recomputing model |
| Future UI | manifests + payloads | forms, status, artifact explorer | make workflow usable by nontechnical user | hidden model mutation |

## 3. Deterministic → valuation → DD connection

Deterministic optimization produces `optimized_results.csv`, including monthly acquisition, clients, recurring sales, revenue, CAC, EBITDA, and cash. This feeds:

- DCF valuation (`dcf_cashflow.csv`, `dcf_annual_summary.csv`, `summary.json` / `valuation_summary.json`),
- unit economics (`unit_economics.csv`),
- due diligence rules and calibration,
- report charts and tables.

Due diligence then classifies the run:

| DD verdict | Stochastic? | Report interpretation |
|---|---:|---|
| `passed` | yes | final valuation mode |
| `passed_with_warnings` | yes | final valuation mode with warnings |
| `requires_minor_adjustment` | yes | warning/preliminary mode |
| `requires_major_adjustment` | no for canonical M4 | recalibrate YAML before stochastic PCA |
| `rejected_for_stochastic` | no | no stochastic valuation; fix structural blockers |

After ADR 0009, canonical channel-parity CVaR M4 runs only for `passed`, `passed_with_warnings`, or `requires_minor_adjustment`. Major venture-scale failures must return to YAML recalibration first. Liquidity, runway, funding gap, LTV/CAC, and revenue-growth issues remain evidence and interpretation fields, not capital-gap penalties inside the stochastic objective.

## 4. Commercial channels across stages

Commercial channels are YAML-defined. The UI/form must collect and pass them without inventing defaults beyond the model schema.

Supported channel concepts:

| Channel | YAML driver | Model meaning |
|---|---|---|
| Salesforce | `channels.salesforce.active`, `meta`, `sup`, `rem_v`, `rem_l`, `com_v`, `com_l` | sellers/leaders capacity and commissions |
| Advertising | `channels.advertising.active`, `I_min`, `I_max`, `A_min`, `A_max`, `A_ad_cap`, share bounds | continuous recta `A_ad = a + b I_ad`; spend equals CAC component |
| Third-party / B2B commission | `channels.third_party.active`, `commission`, share bounds | partner acquisition with commission cost |

Rules:

- Do not compare arbitrary conservative/aggressive policies as the stochastic core.
- Do optimize the best growth plan using available channels from YAML.
- Inactive channels must be absent or forced zero.
- Channel share bounds are parameter constraints, not decision-variable proportions.
- Stochastic model must eventually mirror deterministic channel mechanics.

## 5. What must exist before UI

Before building a real UI/form workflow, the artifact contract must be stable. Minimum prerequisites:

1. `model_instance.json` exists and captures normalized preprocessing.
2. `artifacts_manifest.json` lists every output and stage status.
3. `report_data.json` is stable enough for report and UI consumption.
4. `formula_trace.json` explains DCF and unit-economics formulas.
5. DD JSON has stable verdict and finding schema.
6. Stochastic artifacts distinguish SAA input scenarios, selected plan, and MC evaluation scenarios.
7. Commercial channel schema is form-ready and validated.
8. Report-only narrative fields are optional; core optimization runs without them.

## 6. What the YAML/form must collect

### 6.1 Core model fields

| Section | Required fields |
|---|---|
| Horizon/investment | `H`, `VC`, `beta`, `tax` |
| Services | `nombre`, `ticket`, `frecuencia`, `alpha`, `churn_anual`, `c_u`, `c_min`, `u_max`, `A_base` |
| Commercial team | `meta`, `sup`, `rem_v`, `rem_l`, `com_v`, `com_l`, `commercial_productivity_lag` |
| Fixed costs | `g_adm`, `RRHH_mensual`, `ciclo_op` |
| Liquidity policy | `liquidity_policy`, `working_capital` |
| Acquisition ceiling | `acquisition_ceiling.enabled`, `target_stock_multiplier`, `slack` |
| Solver | solver name, time limit, verbosity |

### 6.2 Channel fields

| Channel | Fields |
|---|---|
| Salesforce | `active`, `min_share`, `max_share` |
| Advertising | `active`, `I_min`, `I_max`, `A_min`, `A_max`, `A_ad_cap`, `min_share`, `max_share` |
| Third-party/B2B | `active`, `commission`, `min_share`, `max_share` |

UI TODO for Salesforce strategy block:

- Nest Salesforce commercial-strategy inputs under Salesforce channel toggle/expander, not as separate top-level form section.
- Order first inputs as `meta`, `sup`, `commercial_productivity_lag`.
- Then show remuneration/commission inputs: `rem_v`, `rem_l`, `com_v`, `com_l`.

### 6.3 DCF/report fields

| Section | Fields |
|---|---|
| DCF | residual value method, EBITDA multiple, Gordon growth, CAPM/WACC details if report uses them |
| Company narrative | company name, description, business model, market, team, investment use, cap table |
| Report metadata | author, date, confidentiality, scenario name |

Report narrative fields must not be required for core optimization.

### 6.4 Stochastic fields

| Section | Fields |
|---|---|
| Scenario generation | method (`lhs`), scenario count, seed |
| MC evaluation | number of scenarios, seed |
| Distributions | per-variable distribution type and parameters |
| Channel uncertainty | only for enabled channels |
| Risk reporting thresholds | DD/VC proxy thresholds for MC diagnostics |

## 7. What UI should display from `artifacts_manifest.json`

A future UI should treat `artifacts_manifest.json` as the run index.

Recommended UI sections:

| UI section | Manifest/report data fields |
|---|---|
| Run status | `stage_status`, `checks.valid`, solver status |
| Inputs | config path/hash, report document path, schema version |
| Deterministic KPIs | total acquisition, revenue, EBITDA, cash, VAN |
| DD status | verdict, allows stochastic, valuation mode, warnings/errors |
| Stochastic status | ran/skipped, status, scenario count, expected VAN, p10/p50/p90 |
| Downloads | CSVs, JSONs, report HTML/PDF |
| Traceability | formula trace, source artifacts, validation checks |
| Figures | figure IDs and paths |
| Unsafe claims | known limitations from claims/formula trace |

Suggested manifest extension:

```json
{
  "stage_status": {
    "instance": "passed",
    "deterministic": "passed",
    "valuation": "passed",
    "due_diligence": "passed_with_warnings",
    "stochastic_saa": "passed",
    "monte_carlo": "passed",
    "report": "passed"
  },
  "audience": {
    "optimized_results": "audit",
    "financial_report": "entrepreneur",
    "report_html": "entrepreneur",
    "formula_trace": "audit"
  }
}
```

## 8. What remains future SaaS work

Out of current scope:

- Multi-user accounts and authentication.
- Persistent run database.
- Background jobs and queueing.
- Editable web forms with validation UX.
- Scenario management UI.
- Versioned organization/client workspace.
- Cloud storage for reports and figures.
- Role-based access to confidential valuation outputs.
- Collaborative comments/approval workflow.
- Payment/subscription logic.
- Automated comparable-company multiple calibration.

These require stable artifact contracts first.

## 9. End-to-end acceptance criteria before UI/report standardization

P0 criteria:

1. A tracked YAML config can reproduce all deterministic and report artifacts.
2. `artifacts_manifest.json` validates no missing core artifacts.
3. `report_data.json` includes deterministic, valuation, DD, and stochastic references when present.
4. DD clearly indicates whether stochastic was allowed, skipped, or diagnostic.
5. Stochastic artifacts are not presented as complete parity until channel/ceiling parity is implemented.
6. Multiples are labeled as reference unless comparables are supplied.
7. Formula trace explains DCF and unit economics assumptions.

P1 criteria:

1. Add foldered artifact layout while preserving flat-file compatibility.
2. Add JSON schema tests for manifest, report data, DD, stochastic diagnostics, formula trace.
3. Add UI payload generator once schemas stabilize.
4. Add optional Excel export only after CSV/JSON workbook is canonical.

## 10. Safe report/UI claims

Safe:

- “El sistema genera un paquete trazable de artefactos intermedios para el plan de crecimiento, valorización, due diligence y reporte.”
- “La due diligence determina si la valorización estocástica se interpreta como final, preliminar, diagnóstica o bloqueada.”
- “La extensión estocástica objetivo se basa en LHS + SAA + Monte Carlo ex-post.”
- “Los múltiplos se usan como referencia metodológica salvo que se provea una base de comparables.”

Unsafe until implemented/evidenced:

- “La UI está lista.”
- “El stochastic tiene paridad completa con todos los canales comerciales.”
- “Los múltiplos están calibrados con mercado.”
- “La probabilidad de éxito VC está optimizada en la función objetivo.”
- “El modelo es robusto” if only risk-neutral SAA is implemented.

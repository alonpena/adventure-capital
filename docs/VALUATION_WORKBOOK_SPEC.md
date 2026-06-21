# Valuation and Unit Economics Workbook Specification

Status: draft artifact contract.  
Purpose: define the structured replacement for the operational Excel workbook while preserving formula readability and report traceability.

## 1. Workbook role in the pipeline

The valuation workbook is not a `.xlsx` dependency. It is a set of structured CSV/JSON artifacts that preserve the same operational readability:

```text
optimized_results.csv
→ dcf_cashflow.csv
→ dcf_annual_summary.csv
→ multiples_valuation.csv
→ unit_economics.csv
→ valuation_summary.json
→ formula_trace.json
→ report_data.json
→ report.html / report.pdf
```

The workbook must answer three questions:

1. What cashflows and valuation does the optimized plan produce?
2. What customer-level economics explain the plan?
3. Which formulas and assumptions connect the YAML input to the report figures?

## 2. DCF inputs

Primary sources:

| Input | Source | Notes |
|---|---|---|
| Monthly EBITDA | `optimized_results.csv.EBITDA` | produced by deterministic or stochastic evaluated plan |
| Monthly revenue | `optimized_results.csv.Ingresos` | service-level revenue aggregated |
| CAC | `optimized_results.csv.CAC` | alias for total acquisition cost |
| Operational cost | `optimized_results.csv.Costo_operacional` | floor/max operational-cost semantics |
| Admin cost | `optimized_results.csv.G_adm` | monthly fixed admin cost |
| HR cost | `optimized_results.csv.RRHH` | monthly HR cost by year |
| Tax rate | `startup.yaml.tax` | current implementation uses positive EBITDA tax only |
| Discount rate | `startup.yaml.beta` or report document DCF override | annual WACC converted to monthly |
| Initial working capital / investment | `startup.yaml.VC` | subtracted in DCF VAN |
| Horizon | `startup.yaml.H` | monthly horizon |
| Terminal value method | `valor_residual_metodo` / report DCF block | `none`, `ebitda_multiple`, `gordon` |
| EBITDA multiple | `ebitda_multiple` / `mult_vd_ebitda` | required if method uses EBITDA multiple |
| Gordon growth | `gordon_g` | required if Gordon method used; must satisfy WACC > g |

## 3. DCF outputs

### 3.1 `dcf_cashflow.csv`

Required fields:

| Field | Formula / source |
|---|---|
| `t` | month |
| `Año` | `(t - 1) // 12 + 1` |
| `Ingresos` | from optimized results |
| `Costo_operacional` | from optimized results |
| `CAC` | from optimized results |
| `G_adm` | from optimized results |
| `RRHH` | from optimized results |
| `EBITDA` | from optimized results |
| `Impuesto` | `max(EBITDA × tax, 0)` |
| `FC_neto` | `EBITDA - Impuesto` |
| `Factor_desc` | `1 / (1 + beta_mensual)^t` |
| `FC_desc` | `FC_neto × Factor_desc` |

### 3.2 `dcf_annual_summary.csv`

Required fields:

| Field | Formula / source |
|---|---|
| `Año` | annual period |
| `Ingresos` | sum monthly revenue |
| `Costo_operacional` | sum monthly operational cost |
| `CAC` | sum monthly CAC |
| `G_adm` | sum monthly admin cost |
| `RRHH` | sum monthly HR |
| `EBITDA` | sum monthly EBITDA |
| `Impuesto` | sum monthly taxes |
| `FC_neto` | sum monthly net FCF |
| `FC_desc` | sum monthly discounted FCF |

### 3.3 `valuation_summary.json`

Required fields:

```json
{
  "schema_version": "1.0",
  "method": "dcf",
  "vc_invested": 0.0,
  "vp_flujos": 0.0,
  "valor_desecho_nominal": 0.0,
  "valor_desecho_vp": 0.0,
  "van": 0.0,
  "beta_anual": 0.0,
  "beta_mensual": 0.0,
  "tax": 0.0,
  "terminal_value_method": "none",
  "ebitda_ultimo_mes": 0.0,
  "ebitda_anualizado": 0.0,
  "formula_refs": ["DCF-001", "DCF-002"]
}
```

Current implementation writes a subset as `summary.json`. Target naming may preserve `summary.json` for compatibility while adding `valuation_summary.json`.

## 4. Unit economics formulas and fields

Primary source: `unit_economics.csv`.

Required columns:

`Unit Economic, Definición, Fórmula / Fuente, Valor, Unidad`

Required metrics:

| Metric | Formula / source | Notes |
|---|---|---|
| `Adquisición` | `Σ optimized_results.Adq_clientes` | total new customers over horizon |
| `MoM Growth` | `(Σ Adq año 1 / base)^1/11 - 1` | current formula uses year-one acquisition and first month base |
| `CHURN` | average first-year `churn_anual` | current output is average; service-specific trace should be available in formula trace |
| `CAC` | `Σ CAC / Σ Adq_clientes` or cumulative CAC per user | current LTV/CAC uses cumulative CAC where available |
| `Ticket promedio` | average configured ticket | descriptive; not weighted unless later specified |
| `Recurrencia mensual` | `1 / frecuencia promedio` | descriptive; service-level trace needed |
| `ARR` | recurrent revenue proxy / total revenue | proxy from recurrent services |
| `Gross Profit (GP)` | `1 - Costo_operacional / Ingresos` | horizon-level gross margin |
| `ARPU` | `Ingresos / (clientes activos promedio × meses)` | current implementation |
| `Cash Burn Rate` | `Σ EBITDA negativo / 360` | operational burn proxy |
| `Bootstrapping` | `max(VC, CBR × ciclo_operacional)` | capital need proxy |
| `LTV` | `Σ_service(ticket × annual_frequency × gross_margin / annual_churn)` | annual, service-summed |
| `LTV(2)` | `VAN / Σ adquisición` | valuation-per-acquired-customer proxy |
| `LTV/CAC` | `LTV / cumulative CAC per user` | key capital efficiency metric |
| `Clientes monetizados` | `Adquisición × ARR` | proxy metric |

Supporting formula definitions:

```text
annual_frequency_s = 12 / frecuencia_s
gross_margin_s = 1 - c_u_s / ticket_s
annual_ltv = Σ_s ticket_s × annual_frequency_s × gross_margin_s / churn_anual_s[0]
annual_revenue_per_customer = Σ_s ticket_s × annual_frequency_s
annual_gross_profit_per_customer = Σ_s (ticket_s - c_u_s) × annual_frequency_s
cac_per_customer = Σ total_acquisition_cost / Σ new_customers
ltv_cac = annual_ltv / cac_per_customer
```

## 5. Formula trace requirements

`formula_trace.json` should make every report figure auditable without opening source code.

Minimal schema:

```json
{
  "schema_version": "1.0",
  "created_at": "ISO-8601",
  "formulas": [
    {
      "id": "DCF-001",
      "name": "FC_neto",
      "expression": "EBITDA - max(EBITDA * tax, 0)",
      "source_fields": ["optimized_results.EBITDA", "startup.yaml.tax"],
      "output_fields": ["dcf_cashflow.FC_neto"],
      "assumptions": ["Tax applies only when EBITDA is positive."],
      "limitations": []
    },
    {
      "id": "UE-001",
      "name": "Annual LTV",
      "expression": "sum_s(ticket_s * (12 / frecuencia_s) * (1 - c_u_s / ticket_s) / churn_anual_s[0])",
      "source_fields": ["startup.yaml.servicios"],
      "output_fields": ["unit_economics.LTV"],
      "assumptions": ["Annual, service-summed; first-year churn used."],
      "limitations": ["Not cohort-specific by acquisition month."]
    }
  ]
}
```

Formula trace must include:

- formula ID,
- Spanish business label,
- mathematical expression,
- source artifacts and columns,
- output artifact and field,
- assumptions,
- known limitations,
- whether the metric is implemented, derived proxy, or methodological reference.

## 6. Valuation summary fields for report/UI

`report_data.json.summary` should expose entrepreneur-facing valuation cards:

| Field | Source |
|---|---|
| `total_acquisition` | `optimized_results.Adq_clientes.sum()` |
| `total_revenue` | `optimized_results.Ingresos.sum()` |
| `total_ebitda` | `optimized_results.EBITDA.sum()` |
| `final_cash` | last `optimized_results.Caja` |
| `minimum_cash` | min `optimized_results.Caja` |
| `last_year_revenue` | last row/period of annual summary revenue |
| `last_year_ebitda` | last row/period of annual summary EBITDA |
| `last_month_ebitda` | last monthly EBITDA |
| `van` | `valuation_summary.van` |
| `valor_desecho_vp` | terminal value PV |
| `unit_economics` | parsed metric dictionary |
| `multiples` | parsed multiples reference values |

## 7. Feeding HTML/PDF report

Workbook artifacts feed the report package as follows:

| Report need | Artifact source |
|---|---|
| Hero valuation | `valuation_summary.json`, `report_data.json.summary` |
| Growth plan charts | `optimized_results.csv` |
| P&L table | `dcf_annual_summary.csv` |
| Monthly cash chart | `dcf_cashflow.csv`, `optimized_results.csv.Caja` |
| CAC composition | `optimized_results.csv` CAC component columns |
| Unit economics tiles | `unit_economics.csv` |
| Sensitivity heatmap | `sensitivity_wacc_multiple.csv` |
| DD status | `due_diligence_report.json`, `assessment_summary.json` |
| Stochastic risk section | `stochastic_summary.csv`, `stochastic_diagnostics.json` |
| Traceability appendix | `formula_trace.json`, `artifacts_manifest.json` |

The report renderer should not recompute valuation logic except for display formatting. Computation belongs to valuation/workbook artifacts.

## 8. Multiples: implemented vs methodological reference

Current implementation calculates two reference valuations:

- revenue multiple: `annual revenue of reference year × mult_ingresos`,
- EBITDA multiple: `max(annual EBITDA of reference year, 0) × mult_ebitda`.

This is valid as a simple reference output, but not a full market-comparable valuation method unless supported by a data set of comparable companies and justified multiples.

Safe wording:

> “La valorización por múltiplos se presenta como referencia metodológica y contraste simple frente al DCF. Los múltiplos utilizados son supuestos configurables; no constituyen una muestra de comparables de mercado calibrada.”

Avoid:

- “valor de mercado validado por comparables”,
- “múltiplos calibrados por mercado”,
- “fair market value” unless a comparable-company analysis exists.

Recommended artifact flag:

```json
{
  "multiples": {
    "status": "implemented_reference",
    "methodological_note": "Configurable multiples; not market-calibrated comparables unless evidence is supplied."
  }
}
```

## 9. P0 workbook gaps

1. Add `valuation_summary.json` as explicit contract; keep current `summary.json` compatibility.
2. Add `formula_trace.json` with DCF and unit economics formulas.
3. Add service-level unit economics trace to avoid averages hiding heterogeneity.
4. Add method flags: `implemented`, `proxy`, `methodological_reference`.
5. Ensure report package reads valuation summary rather than re-parsing all valuation logic.

## 10. P1 workbook gaps

1. Add optional Excel export only as a presentation/export layer, not source of truth.
2. Add validation tests for formula trace coverage.
3. Add stochastic workbook section once SAA/MC artifacts stabilize.

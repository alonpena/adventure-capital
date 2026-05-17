# Pipeline phases

The refactor builds the financial planning pipeline in phases: fixed-period financial modeling, accelerated growth optimization, valuation/unit economics, first report artifacts, and the standard valuation report generator. This separates deterministic cashflow logic from solver decisions, keeps valuation outside the MILP, and makes reporting a consumer of computed results rather than part of core model logic.

## Phase 1: Fixed-period financial model

Model the first 12 monthly periods from configured `A_base` acquisition.

Outputs:

- monthly customer acquisition
- service cohort survival
- active client pool
- new sales
- recurring sales
- total services sold
- revenue
- CAC
- operational cost
- EBITDA
- cash

This phase must not require solver feasibility.

## Phase 2: Accelerated growth optimization

Build and solve the full-horizon MILP initially.

Rules:

- months 1-12 fixed from `A_base`
- months 13-H optimized
- preserve current notebook behavior first
- keep interfaces open for future staged optimization starting from Phase 1 ending state

## Phase 3: Valuation and unit economics

Calculate investor and operating metrics from optimization results.

Outputs:

- DCF valuation
- multiples valuation
- unit economics table

Valuation remains post-processing for the first refactor; optimizer objective remains discounted EBITDA.

## Phase 4: Basic financial report generation

Generate first business-facing artifacts from prior phase outputs.

First artifacts:

- Markdown financial report
- dashboard PNG
- core CSV outputs

Reporting owns visualization. Core model modules must not depend on reporting.

## Phase 5: Standard valuation report generator

Generate the full Spanish valuation report defined in `docs/report-blueprint.md`.

Target artifacts:

- `report.html`
- `report.pdf` when PDF backend is available
- report-specific figures under `figures/`
- `sensitivity_wacc_multiple.csv`
- `sensitivity_variables.csv`
- `breakeven_variables.csv`
- `mapvalue.json`

Phase 5 extends YAML with report-only business narrative sections and adds a renderer based on templates. Core model calculations must continue to run without those narrative fields.

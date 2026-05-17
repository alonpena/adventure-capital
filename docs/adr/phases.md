# Pipeline phases

The refactor will build the financial planning pipeline in four phases: fixed-period financial modeling, accelerated growth optimization, valuation/unit economics, and financial report generation. This separates deterministic cashflow logic from solver decisions, keeps valuation outside the MILP, and makes reporting a consumer of computed results rather than part of core model logic.

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

## Phase 4: Financial report generation

Generate business-facing artifacts from prior phase outputs.

First artifacts:

- Markdown financial report
- dashboard PNG
- core CSV outputs

Reporting owns visualization. Core model modules must not depend on reporting.

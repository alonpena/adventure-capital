# Mathematical Model Plan

This document will hold the formal mathematical formulation for the accelerated growth planning model.

## Scope

The model operates on monthly planning periods and supports multiple services. The first twelve months are a fixed acquisition period; the remaining horizon is optimized.

## Core Flows

The model keeps separate but connected flows:

1. Client flow: acquisition, service cohort survival, active client pool.
2. Service flow: new sales, recurring sales, total services sold.
3. Revenue flow: total services sold multiplied by service price.
4. Cost and cashflow flow: operational cost, CAC, administration, HR, EBITDA, cash.
5. Valuation flow: DCF and unit economics after optimization.

## Decisions Reflected in the Formulation

- Periods are monthly only.
- Annual views are aggregations of monthly periods.
- Fixed acquisition period is exactly twelve months.
- Total horizon `H` is configurable and must be greater than the fixed period.
- Multi-service modeling is service-indexed.
- Repurchase timing is precomputed as a binary parameter, not a solver decision variable.
- Service churn is exogenous and applied through service cohort survival.
- Acquisition creates one new sale in the same service and monthly period.
- Service price is constant in the first refactor, with room for future period-specific pricing.
- Operational cost uses floor semantics: effective cost is the greater of variable usage cost and minimum capacity-step cost.
- Liquidity policy is configurable and defaults to no hard cash constraint in the first refactor.
- Optimization objective remains discounted EBITDA in the first refactor.

## Source

The initial formulation should be migrated from `optimizacion_plan_crecimiento_acelerado_v3 (1).py` and reconciled with `CONTEXT.md`, `PLAN.md`, and ADRs.

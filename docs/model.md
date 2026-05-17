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

## Phase 2 MILP formulation

Sets:

- `S`: service indexes.
- `T = {1, ..., H}`: monthly planning periods.
- `T_base = {1, ..., 12}`: fixed acquisition periods.

Main decision/state variables:

- `A[s,t]`: customer acquisition.
- `V[t]`: sellers.
- `L[t]`: commercial leaders.
- `C[s,t]`: active client pool.
- `R[s,t]`: recurring sales.
- `Q[s,t]`: total services sold.
- `I[s,t]`: revenue.
- `m_op[s,t]`: operational capacity steps.
- `Cost_op[s,t]`: operational cost.
- `CAC[t]`: customer acquisition cost.
- `EBITDA[t]`: monthly EBITDA.
- `Caja[t]`: accumulated cash.

Objective:

```text
max sum_t descuento[t] * EBITDA[t]
```

Core constraints:

```text
A[s,t] = A_base[s,t]                                           for t <= 12
A[s,13] <= (1 + g_max_suavizado) * max(A_base[s,12], avg(A_base[s,1:12]))
A[s,14] <= (1 + g_max_suavizado) * A[s,13]
A[s,t] <= ((1 + g_max_suavizado) / 3) * (A[s,t-1] + A[s,t-2] + A[s,t-3])  for t >= 15

C[s,t] = sum_tau<=t phi[s,tau,t] * A[s,tau]
R[s,t] = sum_tau<t delta[s,tau,t] * phi[s,tau,t] * alpha[s,t] * A[s,tau]
Q[s,t] = A[s,t] + R[s,t]
I[s,t] = ticket[s] * Q[s,t]

Q[s,t] <= u_max[s] * m_op[s,t]
Cost_op[s,t] >= c_u[s] * Q[s,t]
Cost_op[s,t] >= c_min[s] * m_op[s,t]

sum_s A[s,t] <= meta * V[t - lag]                              for t >= 13
V[t] <= sup * L[t]                                               for t >= 13
V[t] >= V[t-1], L[t] >= L[t-1]                                  for t >= 13

CAC[t] = rem_v * V[t] + rem_l * L[t] + sum_s (com_v + com_l) * ticket[s] * A[s,t]
EBITDA[t] = sum_s I[s,t] - sum_s Cost_op[s,t] - CAC[t] - g_adm - RRHH[t]
Caja[1] = VC + EBITDA[1]
Caja[t] = Caja[t-1] + EBITDA[t]                                 for t > 1
```

Liquidity policy defaults to `none`, adding no cash floor. Optional policies currently implemented: `nonnegative` and `minimum_cash`.

## Phase 3 post-processing

DCF valuation uses monthly optimization results after solver completion:

```text
Impuesto[t] = max(EBITDA[t] * tax, 0)
FC_neto[t] = EBITDA[t] - Impuesto[t]
FC_desc[t] = FC_neto[t] / (1 + beta_mensual)^t
Valor_desecho = max(EBITDA[H] * 12 * mult_vd_ebitda, 0)
VAN = -VC + sum_t FC_desc[t] + Valor_desecho / (1 + beta_mensual)^H
```

Multiples valuation uses last annual aggregation in the horizon:

```text
Valor_ingresos = Ingresos_ultimo_anio * mult_ingresos
Valor_ebitda = max(EBITDA_ultimo_anio, 0) * mult_ebitda
```

Unit economics are calculated from monthly result aggregates and optional DCF `VAN`; they are not optimizer constraints or objective terms.

## Source

Phase 2 formulation and Phase 3 valuation/unit-economics calculations were migrated from `optimizacion_plan_crecimiento_acelerado_v3 (1).py` and reconciled with `CONTEXT.md`, `PLAN.md`, and ADRs.

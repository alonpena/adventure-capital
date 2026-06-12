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

## Logarithmic acquisition ceiling (optional)

An optional upper bound on **total** acquisition across all services for `t >= 13`,
modeling market saturation. It is a conservative brake on Enterprise Value: it can
only lower or leave EV unchanged, never raise it. It is an **additional** constraint
layered on top of the existing smoothing constraints — it does not replace them.

Config block (disabled by default):

```yaml
acquisition_ceiling:
  enabled: true
  target_stock_multiplier: 2.0   # target cumulative acquisition stock vs. year-1 total
  slack: 0.15                    # tolerance above the ceiling (>= 0)
```

Preprocessing (in `instance.py`), where `S_0` is the total year-1 acquisition
(`sum_s sum_{t=1..12} A_base[s,t]`) and `H_post = H - 12`:

```text
S_target = S_0 * target_stock_multiplier
K        = (S_target - S_0) / ln(1 + H_post)
S(t)     = S_0 + K * ln(1 + (t - 12))        for t >= 13
ceiling[t] = S(t) - S(t-1)                   (S(12) = S_0)
```

`ceiling[t]` is the **marginal** per-period acquisition cap. Because the cumulative
stock `S(t)` follows a logarithm, its increments are monotonically decreasing, so the
ceiling tightens over time. Cumulative acquisition over `t = 13..H` reaches `S_target`
by construction.

Constraint added to the MILP:

```text
sum_s A[s,t] <= ceiling[t] * (1 + slack)      for t >= 13
```

`slack` provides tolerance above the formula ceiling. The optimizer may acquire
anywhere from 0 up to the cap. Diagnostic output columns `Log_ceiling[t]` and
`Log_ceiling_slack[t]` are emitted when the ceiling is active.

## Acquisition channels (optional, Phase 2)

Total per-service acquisition is split across channels while `A[s,t]` stays the
total used by cohorts, revenue, recurrence, smoothing, and the log ceiling:

```text
A[s,t] = A_sf[s,t] + A_ad[s,t] + A_tp[s,t]
```

Channel activation is exogenous (YAML `channels.<name>.active`), never a decision
variable. Salesforce variables always exist (mechanical refactor); advertising and
third-party variables exist only when active. With no `channels` block, behavior is
salesforce-only and identical to before (`A_sf = A`, no channel columns).

Salesforce capacity binds **salesforce** acquisition only:

```text
sum_s A_sf[s,t] <= meta * V[t - lag]      for t >= 13
```

When `salesforce.active = false`: `A_sf[s,t] = 0`, `V[t] = L[t] = 0`, no salary CAC.

Advertising is a continuous linear recta (see ADR-0006). With
`b = (A_max - A_min)/(I_max - I_min)` and `a = A_min - b*I_min`:

```text
A_ad_total[t] = sum_s A_ad[s,t] = a + b * I_ad[t]      for all t
A_ad_total[t] <= A_ad_cap
advertising_cac_cost[t] = I_ad[t]
I_min <= I_ad[t] <= I_max                              for t >= 13 only
```

The investment range binds only the optimized horizon; months 1-12 are the exogenous
Fixed Acquisition Period (the recta still holds there but `I_ad` is unconstrained).

Linear channel share bounds (parameters times the variable total; no bilinearities):

```text
A_ch_total[t] >= min_share_ch * A_total[t]     (added only when min_share > 0)
A_ch_total[t] <= max_share_ch * A_total[t]     (added only when max_share < 1)
```

CAC now reads salesforce acquisition for commissions and adds advertising spend:

```text
CAC[t] = rem_v*V[t] + rem_l*L[t]
       + sum_s (com_v + com_l) * ticket[s] * A_sf[s,t]
       + advertising_cac_cost[t]
```

Effective channel proportions (`share_*`) are post-solve diagnostics, not variables.

## Working-capital cash floor (Phase 4)

A hard working-capital floor indexed to the financing ticket. Cash may fall to `-VC`
(all financing consumed, the working-capital limit) but no further. This is **not**
`>= 0` — it enables breakeven modeling.

```text
Caja[1] = VC + EBITDA[1]
Caja[t] = Caja[t-1] + EBITDA[t]
Caja[t] >= -VC                 ∀t ∈ T        (when working_capital.enabled)
```

Config (disabled by default; supersedes `liquidity_policy` when enabled):

```yaml
working_capital:
  enabled: true
  floor_mode: ticket     # floor = -VC
```

The main objective stays pure discounted EBITDA — the floor is a hard constraint, never
a penalty term.

**Financing-gap diagnostic.** If the main model is infeasible, a *secondary* model is
built (`build_model(instance, elastic_floor=True)`): the floor is relaxed with
non-negative `cash_shortfall[t]` (`Caja[t] + shortfall[t] >= -VC`) and the objective is
replaced by `minimize Σ shortfall[t]`. This separate solve measures the financing gap
without ever mutating the main model. `solve_with_working_capital(instance)` returns:

- feasible: `{feasible: True, min_cash_balance, min_cash_month, financing_gap_usd: 0}`
- infeasible: `{feasible: False, financing_gap_usd (max shortfall), first_breach_month, total_gap}`

When the main solve is infeasible, the pipeline preserves the main `Infeasible` status,
uses the diagnostic solution only for safe downstream artifacts, and routes the structured
financing gap to Due Diligence as alert `DD11`: `Plan requires additional financing of $X
beyond the VC ticket, first breach in month Y.`

Calibration C04 uses `-VC` as its floor when working_capital is enabled (else the legacy
`minimum_cash`).

**Documented identity.** `Caja_final == VC + Σ EBITDA` holds because the model considers
only operational flows. If future extensions add CapEx, debt service, or other
non-operational cash flows, this identity must be updated accordingly.

## Unit economics and breakeven (Phase 5)

All unit-economics metrics are **annual** and **post-solve** (no MILP variables). Service
lines are **summed**, never averaged.

```text
annual_frequency_s          = 12 / frecuencia_s
gross_margin_s              = 1 - c_u_s / ticket_s
annual_churn_s              = churn_anual_s[0]

LTV   = Σ_s ticket_s * annual_frequency_s * gross_margin_s / annual_churn_s
CAC   = cumulative_cac_per_user = Σ total_acquisition_cost / Σ new_customers
LTV/CAC = LTV / CAC
```

A high `LTV/CAC` (calibration C08 band, default `> 20×`) is surfaced as a **known
artifact** of the model structure (annual churn denominator × high gross margin), never
silently corrected.

Breakeven / payback diagnostics (post-solve arithmetic):

```text
annual_gross_profit_per_customer = Σ_s (ticket_s - c_u_s) * annual_frequency_s
annual_contribution_per_customer = annual_gross_profit_per_customer - CAC
breakeven_customers = annual_fixed_costs / annual_contribution_per_customer
payback_customers   = VC / annual_contribution_per_customer
payback_month       = first t where Caja[t] >= VC   (original ticket recovered)
runway[t]           = Caja[t] / |EBITDA[t]|          (NaN when EBITDA[t] >= 0)
```

`annual_fixed_costs` is the year-1 sum of `G_adm + RRHH`. Enterprise Value only — no
Equity Value module.

## CAC cost components and traceability (Phase 3)

CAC is decomposed into linear **cost-component** decision variables. No CAC ratio is
ever a decision variable — all per-user ratios are computed post-solve.

```text
salesforce_cac_cost[t] = rem_v*V[t] + rem_l*L[t] + sum_s (com_v+com_l)*ticket[s]*A_sf[s,t]
third_party_cost[t]    = sum_s tp_commission * ticket[s] * A_tp[s,t]        (when third-party active)
total_acquisition_cost[t] = salesforce_cac_cost[t] + advertising_cac_cost[t] + third_party_cost[t]
CAC[t] = total_acquisition_cost[t]                                          (canonical alias)
```

`EBITDA[t]` still subtracts `CAC[t]`, so legacy configs are byte-identical
(`salesforce_cac_cost ≡` old CAC, other components 0).

Post-solve traceability columns (in `results.py`, never in the MILP):

```text
new_customers[t]            = total acquisition (Adq_clientes)
period_cac_per_user[t]      = total_acquisition_cost[t] / new_customers[t]          (NaN if 0)
cumulative_cac_per_user[t]  = Σ_{1..t} total_acquisition_cost / Σ_{1..t} new_customers (NaN if 0)
```

Third-party cost is a commission on ticket (`channels.third_party.commission`,
default 0.0), mirroring the salesforce commission.

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

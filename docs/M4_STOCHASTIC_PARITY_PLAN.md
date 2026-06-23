# M4 Stochastic Parity Plan

Status: implementation plan for replacing the current simplified stochastic prototype.  
Decision source: ADR 0009.

## Goal

Upgrade M4 so it solves the same commercial and financial problem as the deterministic PCA, but under uncertainty. M4 must produce a first-stage optimal growth plan using SAA + LHS and conservative CVaR objective, then evaluate the selected strategy with Monte Carlo to report the distribution of valuation, customers, breakeven, runway, and unit economics. The investment ticket `VC` remains fixed across scenarios; financing stress is measured through funding gap and runway, not by changing invested capital.

## Non-goals

- Do not refactor the whole codebase to OOP before M4 parity.
- Do not expose stochastic sampling/distribution settings in the UI form.
- Do not treat current simplified stochastic output as final PCA.
- Do not add scipy solely for triangular sampling.
- Do not rebuild the legacy report before M4 artifacts are correct.

## Backend-static defaults

M4 orchestration uses internal defaults. These are stable across user iterations and are not editable in the Streamlit instance form.

Recommended code location:

```text
src/adventure_capital/stochastic/defaults.py
```

Recommended default object:

```python
M4_DEFAULTS = {
    "objective": "cvar_van",
    "cvar_alpha": 0.05,
    "saa_scenario_count": 100,
    "evaluation_scenario_count": 1000,
    "seed_saa": 12345,
    "seed_eval": 999,
    "distributions": {
        "churn_multiplier": {"min": 0.8, "mode": 1.0, "max": 1.3},
        "salesforce_efficiency": {"min": 0.6, "mode": 1.0, "max": 1.2},
        "advertising_efficiency": {"min": 0.5, "mode": 1.0, "max": 1.3},
        "third_party_efficiency": {"min": 0.7, "mode": 1.0, "max": 1.2},
        "wacc_multiplier": {"min": 0.7, "mode": 1.0, "max": 1.5},
    },
    "milestones": {"client_counts": [500, 1000, 2000]},
    "third_party_defaults": {"commission_periods": 6},
}
```

If production later needs engineering overrides, accept an optional internal path/flag outside the user-facing startup form.

## Probability sampling

Implement LHS without scipy:

1. For each uncertain variable and `N` scenarios, create strata `(i + u_i) / N` where `u_i ~ U(0,1)`.
2. Shuffle strata independently per variable using seeded RNG.
3. Transform each stratum probability through triangular ICDF.

Triangular ICDF for `a=min`, `c=mode`, `b=max`:

```text
F_c = (c - a) / (b - a)
if p < F_c:
    x = a + sqrt(p * (b - a) * (c - a))
else:
    x = b - sqrt((1 - p) * (b - a) * (b - c))
```

Validation:

```text
a <= c <= b
b > a
0 < scenario_count
```

## First-stage strategy variables

Shared across all scenarios:

```text
V[t]
L[t]
I_ad[t]
A_sf_plan[s,t]
A_ad_plan[s,t]
A_tp_plan[s,t]
A_plan[s,t]
```

Months 1-12 stay fixed from `A_base` as the consensuated plan and are not perturbed by channel-efficiency scenarios. Channel plan variables and stochastic efficiency realization start in month 13. Limitation: this does not model first-year channel mix or first-year channel-efficiency uncertainty. Future work may require `A_base` by channel, but input/UI design must be evaluated before adding that requirement.

## Scenario-dependent variables

Commercial recourse is out of scope for this implementation. Scenarios do not adapt `V`, `L`, `I_ad`, or planned channel acquisition after efficiency is observed; CVaR penalizes plans that fail under downside realizations.

For each scenario `w`:

```text
A_sf[s,t,w]
A_ad[s,t,w]
A_tp[s,t,w]
A[s,t,w]
C[s,t,w]
R[s,t,w]
Q[s,t,w]
I[s,t,w]
Cost_op[s,t,w]
m_op[s,t,w]              # integer in canonical M4; preserves deterministic capacity-step parity
CAC_sf[t,w]
CAC_ad[t,w]
CAC_tp[t,w]
CAC[t,w]
EBITDA[t,w]
Tax[t,w]
FCF[t,w]
Caja[t,w]
FundingGap[t,w]
VAN[w]
```

Mandatory invariant:

```text
C[s,t,w] varies with A[s,c,w] and phi[s,c,t,w]. Fixed traction is prohibited.
```

## Channel equations

### Salesforce

```text
sum_s A_sf_plan[s,t] <= meta * V[capacity_period]
V[t] <= sup * L[t]
V[t] >= V[t-1]
L[t] >= L[t-1]
A_sf[s,t,w] = salesforce_eff[w] * A_sf_plan[s,t]
CAC_sf[t,w] = rem_v * V[t] + rem_l * L[t] + sum_s (com_v + com_l) * ticket[s] * A_sf[s,t,w]
```

### Advertising

Use ADR 0006 semantics:

```text
sum_s A_ad_plan[s,t] = a + b * I_ad[t]
I_min <= I_ad[t] <= I_max
sum_s A_ad_plan[s,t] <= A_ad_cap
A_ad[s,t,w] = advertising_eff[w] * A_ad_plan[s,t]
CAC_ad[t,w] = I_ad[t]
```

### Third-party

```text
A_tp[s,t,w] = third_party_eff[w] * A_tp_plan[s,t]
```

Commission is charged as `% revenue` over `commission_periods` months for third-party-origin cohorts. It applies only to revenue attributable to third-party-origin cohorts, including initial and recurring revenue inside the window. It must not apply to total company revenue.

```text
CAC_tp[t,w] = commission * sum_{s,c: 0 <= t-c < commission_periods} revenue_from_tp_cohort[s,c,t,w]
```

`commission_periods` is backend-static unless already part of the accepted user-facing deterministic schema. A future extension may add an initial-sale-only third-party commission policy, but current implementation uses the cohort revenue window.

### Channel share constraints

Apply to planned quantities:

```text
A_ch_plan_total[t] >= min_share_ch * A_plan_total[t]
A_ch_plan_total[t] <= max_share_ch * A_plan_total[t]
```

## Financial equations per scenario

```text
A[s,t,w] = A_sf[s,t,w] + A_ad[s,t,w] + A_tp[s,t,w]
C[s,t,w] = sum_c phi[s,c,t,w] * A[s,c,w]
R[s,t,w] = sum_c delta[s,c,t] * phi[s,c,t,w] * alpha[s,t] * A[s,c,w]
Q[s,t,w] = A[s,t,w] + R[s,t,w]
I[s,t,w] = ticket[s] * Q[s,t,w]
Q[s,t,w] <= u_max[s] * m_op[s,t,w]
Cost_op[s,t,w] >= c_u[s] * Q[s,t,w]
Cost_op[s,t,w] >= c_min[s] * m_op[s,t,w]

# m_op[s,t,w] is integer in canonical M4. A future performance fallback may relax
# m_op in SAA and repair with ceil() in out-of-sample LHS evaluation, but that is
# not the canonical implementation.
CAC[t,w] = CAC_sf[t,w] + CAC_ad[t,w] + CAC_tp[t,w]
EBITDA[t,w] = sum_s I[s,t,w] - sum_s Cost_op[s,t,w] - CAC[t,w] - g_adm - RRHH[t]
Tax[t,w] >= tax * EBITDA[t,w]
Tax[t,w] >= 0
FCF[t,w] = EBITDA[t,w] - Tax[t,w]
Caja[1,w] = VC[w] + EBITDA[1,w]
Caja[t,w] = Caja[t-1,w] + EBITDA[t,w]
FundingGap[t,w] >= floor[w] - Caja[t,w]
FundingGap[t,w] >= 0

# Current business floor defaults to ticket-indexed working-capital stress:
# floor[w] = -VC unless an explicit stricter liquidity policy is selected.
```

VAN:

```text
VAN[w] = -VC + sum_t discount[t,w] * FCF[t,w] + terminal_value[w]
terminal_value[w] = discount[H,w] * terminal_multiple * 12 * EBITDA[H,w]
```

Do not use `max(EBITDA, 0)`, binary truncation, or nonlinear terminal-value logic inside the MILP. M4 intentionally uses the linear expression above. Due Diligence should catch structurally weak cases before M4; post-processing/reporting may show a separate normalized DCF terminal-value interpretation, but it does not feed back into the optimization objective.

## CVaR objective

```text
z[w] >= eta - VAN[w]
z[w] >= 0
CVaR = eta - (1 / alpha) * sum_w p[w] * z[w]
maximize CVaR
```

Optional tie-break:

```text
maximize CVaR + 1e-6 * sum_w p[w] * VAN[w]
```

## Monte Carlo ex-post evaluation

Fix first-stage strategy:

```text
V, L, I_ad, A_sf_plan, A_ad_plan, A_tp_plan
```

Evaluate 1000+ out-of-sample LHS scenarios without reoptimization. SAA and ex-post evaluation both use LHS; the second sample uses a separate seed and larger sample size for more stable percentiles and CVaR estimates. Compute per-scenario:

- realized acquisition by channel
- active clients and final active clients, where milestone probabilities use `final_active_clients = sum_s C[s,H,w]` rather than cumulative acquisition
- revenue, CAC components, EBITDA, cash
- VAN and terminal value
- breakeven month
- runway month, defined as first month where `Caja[t,w] < floor[w]`; current default floor is `-VC[w]`, not zero cash
- funding gap
- CAC per customer
- ARPU, ARR
- LTV/CAC proxy consistent with `unit_economics.py`

## Required artifacts

```text
saa_solution.json
stochastic_scenarios.csv
stochastic_summary.csv
stochastic_diagnostics.json
stochastic_unit_economics.csv
```

Minimum `saa_solution.json` fields:

```json
{
  "schema_version": "2.0",
  "status": "Optimal",
  "objective": "cvar_van",
  "cvar_alpha": 0.05,
  "cvar_van": 0.0,
  "expected_van": 0.0,
  "scenario_count": 100,
  "strategy": {
    "V": {},
    "L": {},
    "I_ad": {},
    "A_sf_plan": {},
    "A_ad_plan": {},
    "A_tp_plan": {}
  }
}
```

Minimum `stochastic_summary.csv` fields:

```text
n_scenarios, expected_van, van_p5, van_p10, van_p50, van_p90, cvar_5,
prob_van_negative, final_active_clients_p10, final_active_clients_p50, final_active_clients_p90,
prob_hit_final_active_clients_500, prob_hit_final_active_clients_1000, prob_hit_final_active_clients_2000,
breakeven_month_p50, prob_no_breakeven, runway_month_p50,
prob_cash_below_floor, expected_funding_gap, max_funding_gap,
cac_p50, ltv_cac_p50, arpu_p50, arr_p50
```

## Implementation sequence

1. Add `stochastic/defaults.py` with backend-static M4 defaults.
2. Replace scenario sampling with LHS + native triangular ICDF.
3. Replace `stochastic/model.py` simplified SAA with channel-parity SAA + CVaR.
4. Update `stochastic/evaluate.py` for fixed-strategy MC evaluation with 3 channel realized acquisition.
5. Update `stochastic/results.py` for new artifacts and metrics.
6. Update DD workflow to call new M4 runner only when DD allows stochastic.
7. Add tests:
   - LHS reproducible and stratified.
   - triangular ICDF validates bounds/mode.
   - SAA model builds with 3 channels active.
   - active clients vary by scenario under efficiency multipliers.
   - CVaR finite and present in solution.
   - third-party commission trail respects `commission_periods`.
   - MC artifacts include valuation, clients, breakeven, runway, and UE metrics.

## Acceptance criteria

- M4 can no longer ignore active advertising or third-party channels.
- `C[s,t,w]` is scenario-indexed and varies with realized acquisition.
- UI cannot edit M4 distributions or CVaR settings.
- M4 outputs support probability distribution reporting for value, customers, breakeven, runway, and unit economics.
- Report/UI wording can claim “stochastic PCA” only after this implementation is complete.

# Stochasticity via two-stage stochastic program, staged on top of deterministic model

The target methodology is a two-stage stochastic program: choose one here-and-now growth plan that maximizes expected NPV across scenarios of uncertain parameters, with scenario-dependent outcomes (clients, revenue, EBITDA, cash, valuation, funding gap) as recourse. This replaces the earlier idea of a post-hoc Monte Carlo layer: the optimizer itself must be uncertainty-aware, not just measured after the fact.

The deterministic MILP is NOT removed. It stays as the baseline and due-diligence gate: a case is first evaluated ex ante with the deterministic model to produce the first report / due-diligence assessment. Only if the case passes (or is accepted as worth analyzing) does the stochastic extension run.

## Status

accepted

## Considered options

- **Two-stage expected NPV (chosen).** `max E_ω[NPV(ω)]`. First-stage acquisition/resource plan committed before uncertainty; cash/EBITDA/clients/valuation indexed by scenario.
- **Monte Carlo on a fixed deterministic plan (rejected).** Only measures risk of an already-chosen plan; the optimizer never trades off against uncertainty. Insufficient — we want the plan itself to account for uncertainty. Still useful conceptually as the recourse-evaluation step inside the stochastic model.
- **Chance-constrained — future extension only.** Add `P(cash_t >= floor) >= α`. Documented for later, not built today.
- **Robust / worst-case — not planned.** `max min_ω NPV(ω)`. Too conservative for the present goal.

## Uncertain parameters (first cut)

- Churn / retention behavior (per service).
- Sales strategy efficiency / commercial productivity.
- Available financing / initial funding capacity.
- Discount rate / WACC.

## Staging / constraints

- Do not replace the deterministic pipeline; do not break `model.py`.
- Preserve deterministic run + due diligence + report as today's shippable deliverable.
- Design first-stage vs recourse split and scenario structure now; do not overbuild recourse logic.
- Do not implement robust worst-case. Chance constraints documented as future extension only.

## Objective progression

1. `max E_ω[NPV(ω)]` (expected enterprise value).
2. Then analyze full distribution of the chosen strategy: p10/p50/p90 valuation, P(cash < 0), expected funding gap, downside risk, P(EBITDA < 0).

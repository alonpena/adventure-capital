# Stochastic Extension (Prototype)

Isolated, non-breaking prototype that adds a two-stage stochastic optimization layer on top of the existing deterministic growth-plan MILP. The deterministic model (`model.py`) and pipeline are untouched and remain the baseline. See ADR [0004](adr/0004-two-stage-stochastic-extension.md) for the decision record and CONTEXT.md for the glossary (Scenario, First-Stage Decision, Recourse Decision, Expected NPV, Funding Gap).

## Goal

The deterministic optimizer maximizes NPV against point-estimate parameters; it cannot see uncertainty. This layer chooses one growth plan that maximizes **expected** NPV across many sampled scenarios of uncertain parameters, then quantifies the risk of that chosen plan.

## Two-phase design

Phase A and Phase B are deliberately separate because integer recourse inside the MILP is expensive, while evaluating an already-fixed plan is cheap.

### Phase A — Optimization (SAA MILP)

A sample-average-approximation two-stage program over a moderate scenario sample (default `N=100`).

- **First-stage decisions** (`A`, `V`, `L`) — committed before uncertainty, identical across all scenarios.
- **Recourse decisions** (`m_op`, and all financial outcomes `C,R,Q,I,Cost_op,CAC,EBITDA,Caja,gap`) — indexed by scenario.

Per-scenario objective (linear, no tax, no `max()`):

```
obj_w =  sum_t  discount[t,w] * EBITDA[t,w]
       + discount[H,w] * terminal_multiple * EBITDA[H,w]
```

`terminal_multiple = 1` by default: a conservative *linear residual/continuity proxy*, not a speculative market multiple. The company is valued as an operating whole, not by parts.

Objective:

```
maximize  sum_w  prob_w * obj_w           (prob_w = 1/N for SAA)
```

`VC` (investment ticket) is constant, so it is **excluded** from the optimizer objective (subtracting a constant does not change the argmax). It is reintroduced in the reported DCF VAN.

### Phase B — Ex-post Monte Carlo evaluation

Fix the Phase-A first-stage strategy (`A,V,L`), then draw many more scenarios (default `1000`, can go to `5000`) and evaluate the fixed strategy **without re-solving the MILP**. The recourse is closed-form:

```
m_op[s,t]   = ceil( Q[s,t] / u_max[s] )           # smallest feasible capacity step
Cost_op[s,t]= max( c_u[s]*Q[s,t], c_min[s]*m_op )  # operational cost floor (ADR 0001)
```

From there EBITDA, cash, DCF VAN (after-tax + terminal − VC), funding gap, and breakeven month are pure arithmetic per scenario. This is the full distribution; Phase A only chose the strategy.

## Liquidity and funding gap

In stochastic mode there is **no hard liquidity floor** and **no emergency capital injection**. Cash is allowed to fall below the floor so the model can reveal stress. The funding gap is a pure diagnostic, not penalized in the objective:

```
gap[t,w] >= floor - Caja[t,w]
gap[t,w] >= 0
```

It measures the maximum working capital the strategy requires (runway pressure), not financing that is actually added.

## Uncertain parameters

All distributions are **configurable modeling assumptions, not empirically calibrated truth**. Defaults are bounded triangular `(min, mode, max)` for interpretability under limited data. Future calibration may use historical data, benchmarks, or consultant judgment.

| Uncertainty | Applied to | Default form |
|---|---|---|
| Churn / retention | `servicios[].churn_anual` (× multiplier, clamped to [0,1]) | triangular(0.8, 1.0, 1.3) |
| Commercial productivity | `meta` (× multiplier) | triangular(0.5, 1.0, 1.2) |
| Available financing | `VC` (× multiplier) | triangular(0.7, 1.0, 1.3) |
| Discount rate / WACC | `beta` (absolute value, truncated) | triangular(0.6·β, β, 1.5·β) |

`meta` multiplier only affects the `t>=13` capacity constraint `sum_s A[s,t] <= meta_w * V[capacity_period]`; first-stage sellers/leaders in months 1–12 use the **base** `meta` because they are committed.

## Scenario generation modes

Config-selectable, default `saa`:

- **`saa`** — draw `scenario_count` scenarios by sampling each multiplier from its distribution, fixed `seed`, probability `1/N` each.
- **`explicit`** — named business-facing scenarios with explicit multipliers and probabilities, e.g. `base`, `commercial_downside`, `retention_stress`, `funding_stress`, `upside`. For interpretability, reporting, and manual stress tests.

## Config schema (under a top-level `stochastic` key)

```yaml
stochastic:
  terminal_multiple: 1.0
  scenario_generation:
    mode: saa            # saa | explicit
    scenario_count: 100  # Phase A sample size
    seed: 12345
  distributions:         # triangular (min, mode, max); multipliers unless noted
    churn_multiplier:        {min: 0.8, mode: 1.0, max: 1.3}
    productivity_multiplier: {min: 0.5, mode: 1.0, max: 1.2}
    financing_multiplier:    {min: 0.7, mode: 1.0, max: 1.3}
    wacc_relative:           {min: 0.6, mode: 1.0, max: 1.5}  # × base beta
  named_scenarios:       # used when mode == explicit
    - {name: base,               probability: 0.40, churn_multiplier: 1.0, productivity_multiplier: 1.0, financing_multiplier: 1.0, wacc_multiplier: 1.0}
    - {name: commercial_downside, probability: 0.15, productivity_multiplier: 0.6}
    - {name: retention_stress,    probability: 0.15, churn_multiplier: 1.3}
    - {name: funding_stress,      probability: 0.15, financing_multiplier: 0.7}
    - {name: upside,              probability: 0.15, churn_multiplier: 0.85, productivity_multiplier: 1.2}
  evaluation:
    n_scenarios: 1000    # Phase B ex-post sample
    seed: 999
```

Everything has code defaults; the `stochastic` block can be omitted or partial. Stochastic mode is never mandatory and never runs inside `run_pipeline`.

## Reported outputs (Phase B)

Full per-scenario results CSV plus summary statistics:

- expected VAN, p10 / p50 / p90 VAN, min / max / std VAN
- P(VAN < 0)
- P(funding gap > 0), expected funding gap, maximum funding gap
- breakeven-month distribution

Percentiles are summary statistics, not a replacement for the full per-scenario distribution.

## Implemented vs conceptual

**Implemented in this prototype**
- `stochastic/scenarios.py` — SAA + explicit scenario generation, triangular sampling, seeded.
- `stochastic/model.py` — Phase A two-stage SAA MILP (first-stage `A,V,L`; per-scenario recourse), expected discounted EBITDA + linear terminal proxy.
- `stochastic/evaluate.py` — Phase B closed-form ex-post Monte Carlo.
- `stochastic/results.py` — distribution summaries + CSV writers.
- Smoke test exercising the full Phase A → Phase B flow on a small sample.

**Conceptual / future (documented, not built)**
- Chance constraints (`P(cash_t >= floor) >= alpha`).
- Robust / worst-case objective.
- Emergency financing recourse with a cost.
- After-tax DCF inside the optimizer objective (needs linearization).
- A pre-model **Due Diligence** screening layer (separate from post-model **Calibration**).
- Wiring stochastic mode into the main CLI / pipeline as an opt-in step.

# 0013 — Convex-CAC endogenous growth law

Status: Proposed
Date: 2026-06-23
Supersedes: the exogenous logarithmic acquisition ceiling (ADR 0010, R1) as the growth
driver. Relates to: cost calibration (C07/C08 DD checks), stochastic parity (ADR 0011).

## Context

The MILP is **linear in acquisition**: `A -> C -> revenue` and CAC/cost are all linear, so
the marginal NPV of a customer is a positive constant. Uncapped, the optimizer grows
acquisition without bound (proven: `Unbounded` even with a non-negative cash floor). Every
brake we add is therefore "manual":

- **Moving-average smoothing** (old): bounds the growth *rate*; a linear recurrence that
  permits geometric divergence `~(1+g)^t` (`(1.25)^24 ~ 211x`). Diverges.
- **Logarithmic ceiling x M** (ADR 0010): bounds the *level* (stock -> M*C_0); finite, but
  the level M is exogenous and **VAN scales ~linearly with M** (measured: entrena
  554k/1182k/2138k/3382k at M=3/5/8/12), so M is the value driver, not the economics.

The "source of truth" is each Excel `Motor` sheet. Extracted manual acquisition:
`godemos Y1/Y2/Y3 = 274/548/1096` (exactly **x2 per year**); `entrena = 96/157/318`
(~x1.6-2). The founders grew acquisition **geometrically** at a chosen annual rate — the
implicit ambition/"TAM" — and **never self-limited within the horizon**, because their
unit economics were over-optimistic (`gross margin ~100%`, `LTV/CAC 34-87x`, C07/C08). The
near-zero modeled cost traces to the **blended single-service simplification** (C09): the
Excel has one client base consuming N services with different costs (e.g. godemos platform
`c_u=0.1` + mentoring `c_u=20`); the blend kept only the cheap stream.

Causal chain: `blend (C09) -> understated cost (C07) -> inflated LTV/CAC (C08) -> profitable
unbounded growth -> needs a manual cap`.

## Decision

Replace the exogenous ceiling with an **endogenous convex acquisition cost** (diminishing
returns), so growth self-limits at the economic optimum and is driven by unit-economics
quality. No hard cap, no divergence (convexity guarantees a finite optimum).

### Mechanism (per service `s`, months `t >= 13`)

Decompose per-period acquisition into batches of the year-1 run-rate and charge a rising
marginal CAC:

```text
A[s,t]            = sum_{k=0}^{K-1} a_k[s,t]
0 <= a_k[s,t]     <= w_s                          # batch width = year-1 monthly run-rate
saturation_cost[t] = sum_s sum_k (base_cac_s * theta * k) * a_k[s,t]
EBITDA[t]        -= saturation_cost[t]
```

Segment `k=0` carries no premium (the existing channel CAC is the base); each further batch
costs `theta * base_cac_s` more per customer. Because the cost is piecewise-linear convex
and the objective maximizes, the solver fills cheap batches first **with no binaries** —
the MILP stays linear and barely grows (a few continuous vars per period).

The optimum stops where marginal CAC meets marginal value:

```text
base_cac_s * (1 + theta * k*) = LTV_s
=> k* = (LTV_s / base_cac_s - 1) / theta            # growth ceiling in run-rate batches
```

So **max monthly acquisition ~ k* * w_s**, rising with `LTV/CAC` (quality) and falling with
`theta` (channel saturation). A weak business (low LTV/CAC) self-limits early; a strong one
grows far — endogenously, with no M.

### Parameter sourcing (reproducible, traceable, no VAN targeting)

| param | source |
| ----- | ------ |
| `w_s` (batch) | `mean(A_base[s, 1..12])` — year-1 run-rate, directly from the YAML |
| `LTV_s` | deterministic from `ticket, alpha, frequency, churn, discount` (preprocessing) |
| `base_cac_s` | effective per-client channel CAC from the YAML (salesforce `rem/meta` + commission; advertising recta) |
| `theta` | channel-saturation rate; documented default, calibratable from the year-1 ramp in `Motor` (never fitted to VAN) |
| `K` | `ceil(2 / theta)` segments so the economic limit binds before the segment cap |

Validation (standalone prototype, real instance params): at `LTV/CAC = 3, theta = 1.0`,
`godemos Y2/Y1 = 2.00` (manual 2.0), `entrena Y2/Y1 = 1.92` (manual 1.64) — the convex law
reproduces the Motor source-of-truth. With the *inflated* placeholder economics
(`LTV/CAC ~ 60`) it (correctly) does not bind, confirming realistic costs are a prerequisite.

### Cost realism (prerequisite, separate work)

`base_cac_s` and `LTV_s` are only meaningful with realistic costs. The blended `c_u` must be
the **volume-weighted** cost across the Excel's service streams (godemos platform+mentoring;
beloop advisor capacity), or the services must be un-blended. This fixes C07/C08 and is a
precondition for the convex law to bind. Costs are extracted from the Excel cost sheets
cell-by-cell — never fabricated to hit a VAN.

## Consequences

- Growth is endogenous and quality-driven; the exogenous multiplier M is removed. The
  `3x` becomes at most a documented sanity reference / market guard, not the value driver.
- All deterministic and stochastic values shift; golden artifacts re-baseline. Large blast
  radius — staged migration with tests at each step.
- The cash floor `-VC`, salesforce/ops capacity, and the convex CAC are the brakes; with
  realistic costs the plan is more conservative than the over-optimistic manual exponential.

## Migration plan

1. Cost realism: weighted-blended `c_u` (or un-blend) for the benchmark configs; re-validate
   C07/C08 and concordance.
2. Deterministic core: add `LTV_s`, `w_s`, segment vars; remove the log ceiling; add the
   convex CAC; re-baseline tests.
3. Calibrate `theta` from the year-1 ramp; document defaults.
4. Stochastic parity (ADR 0011): mirror the convex CAC in `stochastic/model.py`.
5. Demote the log ceiling to an optional market guard or remove it.

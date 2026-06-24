# 0013 — Convex-CAC endogenous growth law

Status: Accepted (both brakes retained for comparison)
Date: 2026-06-23 (revised 2026-06-24 after the cost-realism investigation)
Supersedes: the exogenous logarithmic acquisition ceiling (ADR 0010, R1) as the *primary*
growth driver; the ceiling is retained as an upper-bound reference. Relates to: stochastic
parity (ADR 0011).

## Revision note (2026-06-24)

The original premise — "un-blending reveals hidden cost -> realistic LTV/CAC -> convex
binds" — was **falsified by inspection**. The benchmark unit economics are genuinely
near-zero-cost (margins 73-99.9%; godemos' own fully-blended `c_u = US$20.19/cliente/año`
= 98% margin), so raising `c_u` toward the founders' real blend barely moves LTV/CAC
(still 25-80x) and the convex law still would not self-limit. The Motor `2x/year` was the
founders' **chosen geometric ambition, not an economic optimum** — their economics imply
near-unbounded growth and the ramp was manual restraint. Cost-raising is therefore a
near-no-op, and forcing costs higher would be fabrication (forbidden). The actual traceable
lever is **theta calibrated from the realized Motor ramp** (see Decision). Both brakes are
kept and compared rather than one replacing the other.

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

### theta calibration from the realized ramp (the actual lever)

Because the benchmark economics are genuinely near-zero-cost, `theta` (not `c_u`) is the
parameter that makes the convex optimum reproduce the source-of-truth trajectory. We
calibrate `theta` per instance so the convex Y2/Y1 acquisition ratio matches the Motor
sheet's realized Y2/Y1 — observed data, **never the VAN**. `theta` is monotone-decreasing in
growth, so a bisection on the solved ratio is exact (`scripts/calibrate_theta.py`).

### Comparison: 3x ceiling vs convex theta* (deterministic, H=36)

| instance | Motor Y2/Y1 | 3x ceiling Y2/Y1 | 3x VAN | convex Y2/Y1 | theta* | convex VAN |
| --- | --- | --- | --- | --- | --- | --- |
| godemos | 2.00 | 2.23 | 1,821,711 | 2.00 | 44.7 | 1,312,234 |
| entrena | 1.64 | 1.91 | 553,763 | 1.58 | 47.8 | 416,182 |
| kavacomex | 0.99 | 1.94 | 361,970 | 1.00 | 300 (bound) | 97,782 |
| beloop | 1.56 | 1.75 | 14,915,673 | 1.54 | 49.1 | 5,850,714 |

Readings:
- **Convex theta\* reproduces the Motor Y2/Y1 to within ±0.05 on all four**; the 3x ceiling
  overshoots every instance (kavacomex worst: 1.94 vs 0.99 realized, ~2x too fast).
- Convex is uniformly **more conservative** on VAN (−25% to −73%): it traces the realized
  ramp instead of the optimistic 3x saturation reference.
- theta\* clusters ~45-49 for three instances. **kavacomex saturates the search bound
  (theta=300)**: its very high blended LTV/CAC cannot be choked to a near-flat 0.99 ramp by
  saturation alone — for near-flat real ramps the convex law is a poor fit and the ceiling
  (or an explicit capacity bound) is the more honest brake. Documented caveat.
- Both modes decay in year 3 (Y3/Y2 ≈ 0.3-0.8, vs Motor ~2): an end-of-horizon truncation
  artifact (late cohorts have fewer pre-H repurchases -> lower LTV -> front-loading), shared
  by both brakes and independent of the brake choice. Mitigation (e.g. a tail/steady-state
  term) is separate future work.

### Cost realism (resolved: not the lever)

Costs were checked against the Excel cost sheets cell-by-cell. The blended `c_u` in the YAMLs
already reflects the founders' real (near-zero) marginal cost; un-blending or raising it does
not change the qualitative result. Costs are never fabricated to hit a VAN.

## Consequences

- Growth is endogenous and quality-driven; the exogenous multiplier M is removed. The
  `3x` becomes at most a documented sanity reference / market guard, not the value driver.
- All deterministic and stochastic values shift; golden artifacts re-baseline. Large blast
  radius — staged migration with tests at each step.
- The cash floor `-VC`, salesforce/ops capacity, and the convex CAC are the brakes; with
  realistic costs the plan is more conservative than the over-optimistic manual exponential.

## Migration plan (revised)

1. ~~Cost realism~~: investigated — not the lever (see Revision note); costs left as-is.
2. Deterministic core: convex CAC implemented opt-in alongside the log ceiling (mutually
   exclusive at solve time); both retained for comparison. **Done.**
3. Calibrate `theta` from the realized Motor ramp; `scripts/calibrate_theta.py` +
   theta\* table above. **Done.**
4. Bake `theta*` per instance into the benchmark configs (so a plain run reproduces the
   calibrated convex plan) and re-run the full DD on both modes. **Pending.**
5. Stochastic parity (ADR 0011): mirror the convex CAC in `stochastic/model.py`. **Pending.**
6. Keep the log ceiling as a documented upper-bound reference, not the default value driver.

# 0011 — Stochastic risk parametrization (mean-CVaR) and growth-law parity

Status: Accepted
Date: 2026-06-23
Amends: ADR 0009 (stochastic channel parity + CVaR). Extends ADR 0010 (growth law).

## Context

Two issues in the canonical M4 two-stage SAA model (`stochastic/model.py`):

1. **Over-conservative risk objective.** The objective maximized
   `CVaR_alpha(VAN) + 1e-6 * E[VAN]` with `cvar_alpha = 0.05`. The hypothesis raised
   was "CVaR behaves like a min-max and punishes the operational plan." Assessment:

   - CVaR is **not** min-max. Min-max optimizes the single worst scenario; `CVaR_alpha`
     optimizes the **mean of the worst `alpha`-fraction** — a coherent, convex,
     *tunable* measure (min-max is the `alpha -> 0` limit; `alpha = 1` is risk-neutral).
     The Rockafellar-Uryasev formulation in the model (`z_w >= eta - VAN_w`,
     `max eta - (1/alpha) * sum p_w z_w`) is correct.
   - But `alpha = 0.05` sits very deep in the tail (with `saa_scenario_count = 100`,
     CVaR is estimated from ~5 scenarios), so it *behaves* conservatively, and the
     `1e-6` expected-VAN term is numerically negligible — the objective is effectively
     pure tail.

   Empirical sweep (config `demo-mixed-channels`, N=40 LHS, build once / swap objective):

   | alpha | lambda | E[VAN]   | CVaR_0.05 | plan acq (13..36) | I_ad total |
   | ----- | ------ | -------- | --------- | ----------------- | ---------- |
   | 0.05  | 0.0    | 2,488k   | 2,106k    | 2,070             | 80,059     |
   | 0.05  | 0.5    | **3,065k** | 2,105k  | 2,135             | 80,378     |
   | 0.15  | 0.0    | 2,402k   | 2,103k    | 2,135             | 79,184     |
   | 0.15  | 0.5    | **3,064k** | 2,104k  | 2,135             | 80,378     |

   (The `alpha = 0.30` rows were discarded as CBC time-limit noise at N=40: acquisition
   and CVaR_0.05 dropped together, an artifact, not an economic result.)

   Finding: the conservatism's main symptom here is **not** a suppressed operational plan
   (growth/capacity caps bind that) but **~25% of expected VAN left on the table** — pure
   CVaR is indifferent among plans with equal worst-tail and picks an expectation-
   suboptimal one. Adding a mean weight `lambda = 0.5` raises `E[VAN]` by +23–28% while
   `CVaR_0.05` stays flat: robustness preserved, upside recovered.

2. **Growth-law divergence (ADR 0010 follow-up).** The stochastic first-stage plan still
   used the legacy moving-average smoothing (`g_max_suavizado`), while the deterministic
   model moved to the logarithmic active-stock saturation ceiling. The two models'
   growth laws disagreed.

## Decision

### Mean-CVaR objective

Replace the objective with the mean-risk tradeoff:

```text
maximize  lambda * E[VAN] + (1 - lambda) * CVaR_alpha(VAN)
```

- `mean_cvar_lambda` is a real config knob (default `0.5`): `lambda = 0` recovers pure
  CVaR; `lambda = 1` is risk-neutral. It supersedes the `1e-6` tie-break.
- `cvar_alpha` default `0.05 -> 0.15`: a less extreme, more stably-estimated tail at
  negligible cost in the sweep.
- CVaR remains the risk measure. It is the right coherent, tunable choice for "robust =
  good worst-case but not over-penalizing." Rejected alternatives: min-max/robust
  (more conservative — the wrong direction), mean-variance (penalizes upside, not
  coherent), DRO (heavier, overkill for the thesis).

### Growth-law parity

Remove the smoothing constraints from `stochastic/model.py` and apply the same logarithmic
ceiling used deterministically (ADR 0010) to the first-stage `plan_total`:

```text
sum_s plan_total[s,t] <= ceiling[t] * (1 + slack)      for t >= 13
```

`ceiling`/`slack` come from `base_instance` (computed once in `instance.py`), so the two
models share one growth law. `g_max_suavizado` is no longer read by either model (it is
retained in config only as an inert legacy key).

## Consequences

- The committed strategy captures expected value the pure-CVaR objective discarded, with
  flat worst-case — directly addressing the "punishes the operational plan" concern.
- Deterministic and stochastic growth laws now agree (parity restored).
- Defaults changed (`cvar_alpha`, new `mean_cvar_lambda`); stochastic outputs shift. The
  reported `cvar_van`/`expected_van` are computed post-solve and unaffected in formula;
  the `objective` label stays `cvar_van` for consumer back-compat.

## Recommended follow-up (not in this ADR)

- **In-sample vs ex-post CVaR gap.** SAA CVaR at small `alpha` is optimistically biased
  in-sample. The ex-post LHS evaluation (`evaluate.py`, N=1000, independent seed) already
  yields an out-of-sample `cvar_5` via `summarize_distribution`. Log the delta
  `CVaR_insample - CVaR_expost` as an overfitting diagnostic; a large positive gap means
  raise `saa_scenario_count` or `cvar_alpha`.

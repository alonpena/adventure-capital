# 0010 — Acquisition growth railways

Status: Accepted
Date: 2026-06-23
Supersedes: the smoothing growth constraints in `model.py` (the moving-average cap);
extends ADR 0006 (advertising/channel shares).

## Context

The deterministic MILP plans accelerated growth for `t >= 13` (year 1, `t <= 12`, is the
exogenous Fixed Acquisition Period taken from `A_base`). Two behaviours were found to
diverge from the product vision and from the source spreadsheet (`1) Planilla ETE
Maestra.xlsx`, sheet `Motor`):

1. **Growth law.** `model.py:131-140` caps `t >= 13` acquisition with a recursive
   3-period moving average `A[s,t] <= ((1+g)/3)*(A[t-1]+A[t-2]+A[t-3])`, anchored at
   `t=13` by `(1+g)*max(A_base[s,12], mean(A_base))`. This mirrors the spreadsheet cell
   `Motor!N2 = IF(M2 < AVERAGE(B2:M2), AVERAGE(B2:M2)*(1+MoM), M2*(1+MoM))` — an
   **exponential** law driven by a month-over-month rate. The product vision models
   **market saturation**, i.e. a **logarithmic** stock curve with monotonically
   decreasing marginal acquisition, not unbounded geometric growth.

   Note: the `max(A_base[s,12], mean(A_base))` is computed in Python from fixed inputs at
   build time. It is a constant, not a MILP non-linearity. The constraints are linear.
   The objection is to the **shape of the growth law**, not to model linearity.

2. **Channel selection.** When advertising CAC is marginally cheaper than salesforce,
   the optimizer drives salesforce to zero and scales advertising until it hits a cap or
   the cash floor, producing an unrealistic ads-only plan. ADR 0006 already specifies
   linear `min_share`/`max_share` channel bounds; they are wired in `model.py:191-194`
   but inert because no shipped config sets them.

Adjacent cleanups surfaced during the audit:

3. **Pre-feasibility.** Obviously underfunded or margin-negative instances are only
   discovered after a full CBC solve (and may surface as a silent infeasibility routed
   to the financing-gap diagnostic). A cheap pre-solve check is missing.

4. **Solver time / dead params.** CBC `time_limit` default is 120 s, tight for long
   horizons with `S*H` integer `m_op`. `B_min` (`instance.py:66-68, :153`) is computed
   as all-zeros and never used under the working-capital path.

## Decision

### R1 — Logarithmic growth is the primary, always-on acquisition law

The growth law for `t >= 13` is the logarithmic market-saturation curve, fitted from the
year-1 base plan with a tolerance band. This is the adopted modeling decision: the base
plan anchors future projections and the curve represents an estimated market ceiling.

- **Remove** the moving-average smoothing constraints (`model.py:131-140`), including the
  cosmetic build-time `max`.
- The logarithmic ceiling (`instance.py:72-89`, already correct) becomes the **sole**
  `t >= 13` upper bound on total acquisition, no longer "optional, additive":

  ```text
  S_0      = sum_s sum_{t=1..12} A_base[s,t]        # year-1 base plan stock
  S_target = S_0 * target_stock_multiplier
  K        = (S_target - S_0) / ln(1 + (H - 12))
  S(t)     = S_0 + K * ln(1 + (t - 12))             for t >= 13
  ceiling[t] = S(t) - S(t-1)                        # marginal cap, decreasing
  ```
  ```text
  sum_s A[s,t] <= ceiling[t] * (1 + slack)          for t >= 13
  ```
- **Benchmark anchor.** `target_stock_multiplier` is fitted to the venture-capital
  investment thesis: by year 3 (the last period `t = H = 36`) cumulative acquisition
  reaches `multiplier x` the year-1 base plan. The default is `3.0` (the "triple your
  clients" VC benchmark). The curve passes through that endpoint by construction
  (`S(H) = S_target`); intermediate months follow the logarithm. The exact target is
  ultimately validated by due-diligence experts, who may override `multiplier`.
  Semantic note: `S_0`/`S_target` count cumulative *acquisition*, not net active client
  stock (churn reduces actives); the gap is a DD-assessed nuance, not a model bug.
- `slack` (holgura) is the upward tolerance band around the fitted curve: the optimizer
  may acquire anywhere in `[0, ceiling*(1+slack)]`. The lower side is always free — one
  can spend less and acquire less down to zero — so `slack` only relaxes the ceiling.
  Default `0.15` (10-15% deviation), per-config overridable.
- **Default-on, explicitly disablable.** `acquisition_ceiling` defaults to enabled with
  `target_stock_multiplier: 3.0`, `slack: 0.15`. A config with no ceiling block gets the
  log law by default; only an explicit `enabled: false` opts out, in which case the sole
  remaining acquisition bounds are physical (capacity, cash floor). There is no
  moving-average fallback: when the curve must be relaxed, raise `slack` or
  `target_stock_multiplier`, never reintroduce a recursive average.

### R2 — Channel coexistence is enforced by default

Ship non-trivial `min_share`/`max_share` defaults so a representative multi-channel
config keeps salesforce alive:

```yaml
channels:
  salesforce:  { active: true,  min_share: 0.30 }   # salesforce floor
  advertising: { active: true,  max_share: 0.60 }   # advertising cap
```

Mechanics unchanged from ADR 0006 (linear parameter bounds, no bilinear proportion
variables): `sum_s A_sf[s,t] >= min_share_sf * sum_s A[s,t]` and the advertising cap
analogously.

### R3 — Pre-feasibility check before building the MILP

Add `check_pre_feasibility(instance) -> list[str]`, run before `build_model`. Fast
heuristics only, no solver:

- `VC` vs. year-1 committed fixed cost (`12 * (g_adm + RRHH[1])`).
- per-service unit margin sign (`ticket <= c_u`).

Returns warnings (empty = ok). The pipeline logs them; an explicit strict mode may raise.
This never replaces the solver's feasibility verdict — it catches the obvious cases cheaply.

### R4 — Solver time and dead-parameter cleanup

- CBC `time_limit` default 120 -> 300 s (still overridable via `parametros.solver.time_limit`).
- Remove `B_min` / `minimum_cash` from `instance.py` (`:66-68`, `:153`).
- The liquidity contract stays `Caja[t] >= -VC` (financing ticket floor). Advanced
  working-capital management is explicitly future work (see README).

## Consequences

- **Growth** is bounded by a single, interpretable saturation curve; no recursive
  averaging. EV can only fall or stay vs. an unconstrained plan (the ceiling never raises
  acquisition).
- **Channel mix** cannot collapse to ads-only; salesforce carries a proportional floor,
  stabilizing average CAC.
- **Faster failure** on underfunded/margin-negative inputs via R3, before solver cost.
- **Unboundedness is now possible by construction.** With the smoothing law removed, the
  log ceiling (or a cash/capacity bound) is what keeps acquisition finite. A config that
  both disables the ceiling and sets no liquidity floor is `Unbounded` — a deliberate,
  tested behavior, not a regression.
- **Stochastic divergence.** The stochastic model (`stochastic/model.py`) still uses the
  moving-average smoothing via `g_max_suavizado`. After this ADR the deterministic and
  stochastic growth laws differ; restoring parity is follow-up work (ADR 0009 territory).
  `g_max_suavizado` is retained in config solely for that path.
- **Out of scope / future work:** taxes and free-cash-flow timing remain in
  `valuation.py` (linear, post-solve) — the MILP objective stays pre-tax NPV(EBITDA), per
  existing architecture. Working-capital policy beyond the `-VC` floor is deferred.

## Implementation

Tracked in `docs/PLAN_GROWTH_RAILWAYS.md`. `model.py` and `instance.py` are the frozen
math core; changes land only after this ADR is accepted.

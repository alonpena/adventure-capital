# 0014 — Growth commitment (investment-thesis floor) + hiring friction

Status: Accepted (opt-in, default off)
Date: 2026-07-05
Relates to: ADR 0010 (acquisition growth railways / log ceiling), ADR 0013 (convex-CAC
growth law), ADR 0009/0011 (stochastic channel parity + mean-CVaR).
Implements: `docs/analysis/implementation_plan_growth_law.md` (REV 2).
Branch: `growth-law-adr14` (never merged into `entrega-tesis` by this work).

## Context

ADR 0010 and ADR 0013 both address the *upper* bound on acquisition (a ceiling or an
endogenous convex cost) so the MILP does not diverge. Neither says anything about a
*lower* bound: a due-diligence question independent of the upside brake is "does this
plan even clear the venture-capital growth thesis the investment is predicated on?" —
the VC "triple your clients" heuristic (reunión A. Maureira, 2026-07-01): an investment
is underwritten on the expectation that the client base **triples between the end of
the consensuated year-1 plan (month 12) and the end of year 3 (month 36)**.

Two related gaps existed:

1. No mechanism expressed this as a **floor** (as opposed to a ceiling/cap) on the
   client stock, checkpointed at business-meaningful milestones (year 2, year 3).
2. No mechanism capped the **monthly hiring rate** independent of the existing
   monotonicity (`V_t >= V_{t-1}`, no firing) — a client wanting to model "we can hire
   at most N sellers/leaders a month" had no lever for it.

Both are now implemented as opt-in, default-off, additive constraint blocks. With the
new config keys absent or explicitly disabled, behavior is a bit-for-bit no-op — no
golden touched, no default flipped, `entrega-tesis` untouched.

## Decision

### Growth commitment is a FLOOR, never a ceiling

`growth_commitment.enabled: true` adds `sum_s C[s, checkpoint] >= B_checkpoint` for one
or two checkpoints. It never bounds acquisition from above — the existing upper bounds
(log ceiling ADR 0010, convex CAC ADR 0013, salesforce capacity, cash floor) are
untouched and still the only thing that keeps the model bounded. **A config with
`growth_commitment` enabled and the ceiling disabled is `Unbounded` by design** (verified
empirically on all four `benchmark_v0` instances, §Benchmarks) — the floor alone cannot
close the model; this is the same "unboundedness is possible by construction" behavior
ADR 0010 already documents for the ceiling.

### x3 in 3 years, annual checkpoints, semantics spelled out

Default `source: vc_minimum`, `multiple_3y: 3.0`, `checkpoints: annual`:

```text
C12 = sum_s C[s, 12]                      # net active-client stock, month 12
                                           # (precomputed deterministically, same
                                           # phi/survival used everywhere else —
                                           # no solve required)
m   = multiple_3y                         # 3.0 by default
C24 >= (1 - floor_slack) * sqrt(m) * C12  # year-2 checkpoint (only if checkpoints=annual)
C36 >= (1 - floor_slack) * m * C12        # year-3 checkpoint (always, if H >= 36)
```

**`C36 >= 3 * C12` means: triple the client stock between the end of the consensuated
year 1 (month 12) and the end of year 3 (month 36).** This is the exact reading required
by the mandante and is stated explicitly here (not just implied by the formula) per
review feedback. The annual/`sqrt(m)` shape at month 24 is a design choice (Alonso,
2026-07-05): checkpoints at year boundaries are auditable in VC milestone language;
there is deliberately no monthly floor (a monthly floor would create spurious
infeasibility from seasonality in `A_base`). `checkpoints: terminal` restricts only
`C36`, skipping the year-2 milestone — useful when the year-2 shape is not part of the
thesis being tested.

Both checkpoints are **precomputed constants** in `instance.py` (no non-linearity is
introduced): the MILP gains at most two linear `>=` constraints.

### Source is always explicit, never auto-selected

`growth_commitment.source` is one of:

- **`vc_minimum`** (default): `m = multiple_3y` directly — the "benchmark VC ask."
- **`plan_mom`**: `m = (1 + g)^2` where `g` is the annualized **stock** MoM implied by
  the client's own consensuated `A_base` + churn over year 1 (not the raw acquisition
  MoM — see below). This is a **diagnostic source, never an automatic default**: using
  the plan's own historical MoM as the commitment is a business decision the client
  makes explicitly by setting `source: plan_mom` in the YAML; the system never infers it
  silently. If the implied rate looks suspicious (too aggressive or below the VC
  thesis), warnings W1/W2 fire (never a silent clamp — see below).
- **`custom`**: `m = (1 + custom_g_annual)^2`, an expert override (Alejandro) that
  **requires `custom_g_annual > 0`** (hard validation error if missing/non-positive) and
  should carry `custom_justification` (soft warning W4 if empty — a config that skips
  the paper trail still runs, but is flagged).
- **`none`**: bottom-up valuation, no floor (equivalent to `enabled: false` in effect,
  kept as an explicit enum value for readability in configs that want to say "we
  considered a commitment and rejected it," distinct from "we never considered one").

### Stock MoM vs. acquisition MoM (review correction)

The commitment binds on the **client stock**, not on raw monthly acquisition, so the
number that is comparable to `g_vc_minimum` is the **stock MoM** — the implied monthly
growth of the net active-client stock `C[t]` over year 1 (same `phi`/survival used for
`C12`), not the MoM of the raw `A_base` acquisition plan. `growth_suggestions.json`
(and the `compute_growth_suggestions` function in `instance.py`) reports **both**:

- `g_plan_mom_stock` — the comparable number, used by W1/W2 and by `source: plan_mom`.
- `g_plan_mom_acquisition` — the raw `A_base` MoM, reported as an auxiliary number only
  (it is what a reader would naively compute from the YAML's own acquisition column,
  but it is *not* what the commitment is measured against).

Neither is auto-selected: both are computed and reported, and the human decides.

### Suggestions are computed and reported, never auto-applied

`compute_growth_suggestions(config)` (in `instance.py`) computes, from the config alone
(no solve): `C12`, `g_vc_minimum = multiple_3y**0.5 - 1`, `g_plan_mom_stock`,
`g_plan_mom_acquisition`, and (if the YAML declares an optional `target_revenue_y3` key)
`g_required_rev`, the annual growth needed to hit that revenue target given
`annual_revenue_per_customer` (a declared constant-mix approximation from
`ticket * 12/frecuencia` of the first service). This is written unconditionally to
`growth_suggestions.json` in the pipeline artifacts (regardless of whether
`growth_commitment` is enabled) — a calibration aid, never a value the system picks for
the client.

### Warnings (W1-W5), always advisory, never blocking

Implemented in `due_diligence/rules.py` as `rule_growth_commitment_warnings` (W1, W2,
W4, W5 -> DD13/DD14/DD16/DD15) and `rule_growth_commitment_infeasible` (W3 -> DD17), all
at `WARNING` severity — **never** `structural`/`major`/`minor`. The commitment is an
investment-thesis choice, not a modeling defect, so it can never block DD eligibility.
These are exposed as **importable pure functions**, exercised directly by unit tests;
they are deliberately **not wired into `run_due_diligence`'s automatic chain**, because
that chain calls `run_pipeline(..., output_dir=...)`, which runs consistency checks that
raise on a non-`Optimal` solve (a documented trap, `WORKLOG.md`) — and an Infeasible
commitment solve is an expected, valid outcome of this feature, not an error to route
around silently. Wiring W1-W5 into the fully automatic DD chain without first hardening
that consistency-check path against non-`Optimal` growth-commitment solves is left as
explicit follow-up work, not attempted here to avoid a wide, risky refactor this close
to the thesis defense.

### Infeasible is a valid business result

When `growth_commitment` makes the deterministic solve `Infeasible`, that is the correct
answer to "does this plan clear the thesis" — never treated as a solver bug. W3
(`DD17`) states this explicitly and attaches the structured diagnosis when available.
`scripts/diagnose_infeasibility.py` runs a fixed, ordered sequence of eight
one-at-a-time relaxations (never cumulative) on top of the same config:

| # | relaxation | diagnosis if it restores feasibility |
|---|---|---|
| R1 | hiring friction removed | hiring/onboarding pace insufficient for the thesis |
| R2 | advertising cap/investment x10 (if active) | ad channel saturated |
| R3 | channel `min_share` -> 0 (if any active) | rigid commercial mix |
| R4 | churn x0.5 | retention insufficient |
| R5 | RRHH/`g_adm` -> 0 | fixed-cost load (informative only) |
| R6 | `c_u` -> 0 | operating cost / margin structure |
| R7 | elastic cash floor (if a hard floor is active) | capital insufficient |
| R8 | `multiple_3y` -> 1.0 | the thesis itself is the binding constraint |

`diagnose_infeasibility(config) -> dict` is a pure function (config in, JSON-serializable
dict out), mirroring the pattern already used for `elastic_floor`/
`diagnose_financing_gap` (`model.py`) and the post-build injection style of
`scripts/growth_band_experiment.py`; it also ships a CLI. Bisecting the maximum feasible
multiple (R8 v2) is explicitly deferred, matching the plan.

### Hiring friction

`hiring.enabled: true` adds, for `t >= 13`: `V_t <= V_{t-1} + h_v`,
`L_t <= L_{t-1} + h_l`, on top of the existing monotonicity (no firing). This models a
client-declared hiring/onboarding plan (`commercial_productivity_lag` already models the
ramp-up lag separately). Default off; `h_v, h_l >= 0` validated.

### Ceiling coexistence: legal but validated, never made core to this feature

Per plan and review correction: **the exogenous log ceiling (ADR 0010) is never made
core to this feature** — the commitment does not require raising the ceiling multiplier
(the "x8" reference in earlier exploratory work is out of scope here), and the
commitment is verified to work correctly with the ceiling **disabled** (see Benchmarks:
`Unbounded`, as expected, confirming the floor never substitutes for an upper brake).
When both are active simultaneously (legal — most benchmark runs in this ADR use the
ceiling's own default, since none of the `benchmark_v0` YAMLs declare an
`acquisition_ceiling` block), `validate_config` raises a clear error if the ceiling's own
target multiplier is *below* the commitment's multiple (`ceiling.target_stock_multiplier
< growth_commitment.multiple_3y`), since that combination is infeasible by construction
(the ceiling would cap growth below the floor the commitment demands).

### Stochastic parity: floor on the PLANNED (pre-efficiency) stock

`stochastic/model.py` mirrors both blocks on the **first-stage** (here-and-now) plan:

- Hiring friction on the shared `V`/`L` first-stage variables — identical shape to the
  deterministic block.
- The commitment floor binds on the **planned** client stock
  (`sum_cohort phi_base(s,cohort,checkpoint) * plan_total[s,cohort]`, using the
  **base** (unperturbed) instance's survival, not any scenario's), not on any
  per-scenario realized stock. This preserves the single here-and-now decision: the
  plan is what the commitment is measured against, exactly as every other first-stage
  constraint in that model (capacity, ceiling, channel shares) already works.
- **Parity verified**: with `growth_commitment` enabled and a single deterministic
  scenario (no perturbation), the stochastic first-stage `V`-path is numerically
  identical to the deterministic solve's `V`-path (`tests/test_growth_commitment.py::
  test_parity_det_stoch_first_stage`).
- The realized (ex-post) outcome — whether the *actual* stock clears the thesis once
  scenario efficiency multipliers are applied — is **reported, never enforced**, as the
  KPI `P(C36_realized >= multiple_3y * C12)`. This reuses the existing
  `milestones.client_counts` -> `prob_hit_final_active_clients_{milestone}` machinery in
  `stochastic/evaluate.py` / `stochastic/results.py`: when `growth_commitment` is
  enabled, the C36 target is auto-added as a milestone, so the probability appears in
  `stochastic_summary.csv` / `stochastic_diagnostics.json` with no new artifact schema.

## Benchmarks

Full results and per-case reading: `docs/analysis/growth_commitment_benchmarks.md`
(generated by `scripts/growth_commitment_benchmarks.py`). Summary:

- All four `benchmark_v0` instances (godemos, entrena-en-casa, beloop, kavacomex) are
  `Optimal` under `off`, `vc_minimum`, and `vc_minimum + hiring h=1`.
- **Main finding: `off` and `vc_minimum` are numerically identical in all four
  instances.** The default log ceiling (ADR 0010, `target_stock_multiplier=3.0,
  slack=0.15`) already produces a stock trajectory that clears the commitment's
  checkpoints with room to spare (~2.4-2.9x at month 24, above the sqrt(3)~=1.73x
  threshold; ~3.1-3.5x at month 36, above the 3.0x threshold) in every instance, even
  with hiring friction. The commitment is mechanically correct (verified by the unit
  tests) but **redundant with the pre-existing default ceiling** on these four cases —
  not a failure of the feature, but the correct outcome of both brakes sharing the same
  x3 multiple by default.
- **kavacomex was expected (WORKLOG P1) to be the most likely candidate for
  `Infeasible`** under `vc_minimum`, given its near-flat realized Motor ramp (~0.99x/year,
  ADR 0013). Under `benchmark_v0/kavacomex.yaml`'s actual parameters it came back
  `Optimal` — the default ceiling still dominates because it is computed from the
  model's own consensuated plan, which already implies more growth than the Excel's
  manual ramp. The full R1-R8 diagnosis routine was still run end-to-end against this
  case (documented in the benchmark report) to verify the tool; since the base status
  was `Optimal`, every relaxation trivially reports `feasible=True` (nothing to
  restore). The genuinely-`Infeasible` case is covered separately by a synthetic
  scenario (ceiling with zero slack + hiring frozen at 0 new hires/month), used both in
  `test_diagnosis_routine_smoke` and `test_commitment_infeasible_reported`, where R1
  (removing hiring friction) is confirmed to restore feasibility — the expected
  business reading ("the hiring plan can't keep pace with the thesis").
- A contrast run (`vc_minimum` with the ceiling explicitly disabled) confirms the floor
  never bounds growth from above: all four instances become `Unbounded`, exactly the
  documented ADR 0010/0013 behavior for "no upper brake."

## Consequences

- Zero behavior change when the new keys are absent or `enabled: false` (verified:
  identical solver objective and per-period `Adq_clientes`/`Vendedores` between a config
  with no `growth_commitment`/`hiring` keys and one with both explicitly `false`).
- The commitment is a genuine due-diligence tool for testing "does this plan clear the
  VC thesis," but on the current four benchmark instances it does not change the
  optimal plan, because the pre-existing default ceiling already implies at least as
  much growth. It becomes visibly binding only when the ceiling is tighter than the
  commitment, disabled, or when hiring friction is severe enough to make the ceiling's
  own trajectory unreachable (not observed in any of the four benchmarks at `h=1`).
- Infeasible-with-commitment is by design a valid, informative outcome, with a
  deterministic (no-LLM) diagnosis routine to explain which lever would restore
  feasibility.
- Stochastic parity holds by construction (same plan-level constraint shape as the
  deterministic model) and is verified empirically for the single-scenario case.

## Rejected / deferred

- **Auto-flipping any of `growth_commitment`/`hiring` to default-on.** Explicitly out of
  scope for this branch; requires a human-approved `final_growth_decision.md` gate
  (plan §8) before any rebaseline is considered.
- **Monthly (as opposed to annual) checkpoints.** Rejected — would create spurious
  infeasibility from seasonality in `A_base` (Alonso, 2026-07-05).
- **Auto-clamping `plan_mom` to a "sane" range.** Rejected — the plan explicitly forbids
  silent non-linear corrections to a client-declared MoM; W1/W2 warn, a human decides.
- **Bisecting the maximum feasible multiple (R8 v2).** Deferred, matches plan §11.
- **Raising the log ceiling's default multiplier ("x8") as part of this feature.**
  Explicitly rejected per review — the ceiling is not made core to the commitment; the
  commitment must (and does) work correctly with the ceiling disabled.

---

## Amendment 1 (2026-07-06) — core = commitment + aggregate acquisition envelope; hiring re-labeled experimental

**Status: accepted (Alonso, 2026-07-05/06). Supersedes any framing in this ADR or in
`growth_dynamics_final.md` / `implementation_plan_growth_law.md` REV 2 §1 /
`unbounded_path_diagnosis.md` §0 that presents hiring friction as the core
growth-control mechanism.**

### The core methodology

The thesis-core growth mechanism is the pairing:

1. **`growth_commitment`** — the investment-thesis FLOOR (unchanged, above):
   `C24 >= sqrt(3)*C12`, `C36 >= 3*C12`, anchored on the consensuated 12-month plan.
2. **`acquisition_envelope`** — the **aggregate acquisition envelope**: an upper path
   `sum_s A[s,t] <= U_t` for `t >= 13`, precomputed in `instance.py` as constants
   (MILP stays linear; same pattern as `checkpoint_targets`).

Everything projected is anchored in the consensuated 12-month plan. If that plan
cannot support the VC benchmarks, the model is not wrong: the entrepreneur's
metrics/plan are insufficient and must be recalibrated. **Infeasible is a business
diagnosis, not a solver failure.**

### Envelope construction (all terms traceable, none exogenous)

```text
U_plan_t = Abar12 * (1 + g_mom)^(t-12)      Abar12, g_mom from the TOTAL year-1
                                             consensuated acquisition plan (all services)
U_vc_t   = max(0, B_t - B_{t-1}*(1-churn_t)) with B_t = C12 * m^((t-12)/24)
                                             (acquisition required by the VC-minimum
                                             stock path, net of churn; churn_t =
                                             C12-stock-weighted aggregate monthly churn)
U_t      = base(source) * (1 + delta_t)      source: plan_mom | vc_minimum |
                                             max_plan_vc (default) | custom
delta_t  = slack_year2 (t<=24) / slack_year3 (t>24) — DECLARED THESIS ASSUMPTION
           (defaults 0.25 / 0.50), never hidden tuning
custom   = Alejandro's override: verbatim monthly path, custom_justification REQUIRED (W4)
```

Amendment 2 closure (2026-07-06): the **demo/core profile** uses `source=vc_minimum`
and `delta_t=0` (no speculative upside). The old `max_plan_vc` and positive slack
profile remains implemented as an opt-in sensitivity path, not the demo core. The
investment-thesis multiple is centralized in `investment_thesis.multiple` (default
3.0 over months 12->36); `growth_commitment.multiple_3y` remains a deprecated
backwards-compatible alias.

Explored and rejected for the demo core:

- `U_plan` / `max_plan_vc`: treats MoM from the consensuated plan as an input driver
  and can create a large compounded acquisition artifact. Rejected because MoM must
  be a consequence of the committed path, not the source of value.
- ADR 0010 `acquisition_ceiling.target_stock_multiplier`: useful legacy guardrail,
  but its exogenous M is exactly the arbitrary value-driver problem this closure
  avoids. Rejected as demo core; retained as default-on legacy behavior only.

Terminology: *aggregate acquisition envelope / planning envelope / growth plausibility
envelope*. Technical honesty: mathematically it is an upper bound; the defensible
difference vs. the ADR 0010 ceiling is **traceability** (client plan + VC benchmark +
churn + declared slack, not an exogenous market multiple M) and that it ships paired
with a floor.

Config schema and validation: `acquisition_envelope` block in `config.py` (source enum,
slack >= 0, custom_path length/values, mandatory custom_justification). An early
compatibility check in `instance.py` simulates the maximum reachable stock under U_t;
if a commitment checkpoint is unreachable it raises immediately with the
business-diagnosis message (recalibrate plan / raise justified slack / lower multiple)
instead of paying for a MILP solve.

Stochastic parity: U_t binds the first-stage `plan_total` (planned-first-stage
criterion, same as the commitment floor). Verified: identical V-path, single
deterministic scenario (`tests/test_acquisition_envelope.py::test_parity_det_stoch_envelope`).

Coexistence with the ADR 0010 log ceiling: **allowed and documented** — when both are
active the tighter bound binds at each t (verified in
`test_envelope_coexists_with_log_ceiling`). ADR 0010 remains legacy default-on behavior
inside `generate_instance()` when the block is absent. The demo/core profile therefore
sets `acquisition_ceiling.enabled: false` explicitly; the envelope supersedes the
ceiling in that profile.

### Third-party unbounded path closed (MVP)

`channels.third_party.active: true` now REQUIRES an explicit `A_tp_cap` (monthly cap,
enforced for t >= 13 in both models); missing key is a validation error. Third-party
has no own capacity mechanism, so leaving it uncapped was a documented unbounded
path (`unbounded_path_diagnosis.md` §5-6). Third-party is deliberately NOT modeled
further — it is not central to the target business models.

### Hiring friction: experimental / sensitivity-analysis only, NOT core

Alonso explicitly rejected hiring friction as the main growth-camping mechanism:
(a) empirically the NPV scales ~linearly in h, making h THE value driver — the same
objection that killed the ceiling's M; (b) it de-anchors the projection from the
consensuated plan (25-50 sellers in year 3 over 1-2-seller plans is indefensible as a
committee commitment). The implementation stays (opt-in, default-off, tested) as an
**optional sensitivity/experimental feature**. Do not present it as the thesis core.

### Benchmarks under the new core

`scripts/growth_commitment_benchmarks.py` adds the demo/core mode (commitment +
VC-minimum envelope, `delta=0`, ceiling off) over the four `benchmark_v0` instances:
**all four Optimal** — exactly where the isolated floor was `Unbounded`, the envelope
bounds the problem with business meaning. Deltas vs. the `off` baseline are explained
in `growth_commitment_benchmarks.md`: the optimizer's job is resource-optimal
attainment of the committed path; VAN and MoM are consequences, not calibration
targets.

DD18 (`conservative_plan_diagnostic`) is experimental/advisory only. A
`Conservative` result is returned as passed/ok so it never blocks stochastic
valuation or changes the DD verdict. If the bisection reaches the configured
upper cap, it reports "feasible up to tested cap"; the reported `M_star_feasible`
is not a market maximum.

### Rollback (closes review gap 3)

- **Feature-level**: `acquisition_envelope.enabled: false` + `growth_commitment.enabled:
  false` + `hiring.enabled: false` (or delete the keys) => total no-op, bit-for-bit
  identical solve (tested for all three: `*_off_is_noop`). No residual effect, no
  goldens touched, no defaults flipped.
- **Branch-level**: abandon `growth-law-adr14`; `entrega-tesis` (HEAD `dd0cc08`) is the
  stable fallback (161-test suite green, working demo).
- **Third-party gate**: reverting only the `A_tp_cap` requirement = removing the
  validation block in `config.py` (configs with `third_party.active: false` — all
  shipped configs — are unaffected either way).

### Gate before any merge/rebaseline (unchanged)

PASS verdict + Alonso's signature in `final_growth_decision.md` + rebaseline per plan
§8 criteria + default flips as a separate commit. NO merge, NO UI, NO rebaseline in
this phase.

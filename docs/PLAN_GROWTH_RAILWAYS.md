# Implementation plan — acquisition growth railways (ADR 0010)

Status: **Implemented** (branch `adr/0010-acquisition-growth-railways`). Suite green
(143 passed, 3 skipped). Steps 1-4 done; benchmark anchor set to `multiplier=3.0`.

Sequenced, test-gated. Each step ends green before the next. Math core
(`model.py`, `instance.py`) touched only after ADR 0010 is accepted.

## Step 0 — Baseline (no code change)
- Run full suite, record green baseline: `uv run pytest -q`.
- Snapshot one reference solve (e.g. `configs/base.yaml`) acquisition + EV for before/after diff.

## Step 1 — R4 cleanup (lowest risk, no behavior change)
- `instance.py`: delete `minimum_cash` loop (`:66-68`) and `"B_min"` key (`:153`).
- `model.py:337` and `solve_growth_plan` default `time_limit` 120 -> 300; keep
  `parametros.solver.time_limit` override.
- README: add "Future work" bullet — working-capital management deferred; liquidity
  contract is `Caja[t] >= -VC`.
- Grep for `B_min` / `minimum_cash` usages across `src/`, `tests/`, `streamlit_pages/`;
  fix or remove dependents.
- Gate: `uv run pytest -q` green.

## Step 2 — R3 pre-feasibility (additive, no model change)
- New `check_pre_feasibility(instance) -> list[str]` (likely `instance.py` or a small
  `feasibility.py`). Heuristics: VC vs `12*(g_adm + RRHH[1])`; per-service `ticket <= c_u`.
- Wire into the solve entry path (`solve_with_working_capital` / CLI) as a logged warning;
  optional strict flag raises.
- Tests: underfunded instance -> warning; healthy instance -> empty list.
- Gate: new tests + suite green.

## Step 3 — R2 channel defaults (config + docs, model already wired)
- Add `min_share`/`max_share` to representative multi-channel configs
  (`configs/demo-mixed-channels.yaml`, base templates as appropriate).
- Confirm `model.py:191-194` enforces the bounds (already present; add a regression test
  asserting `sum A_sf >= min_share * sum A` on a solved mixed-channel instance).
- Gate: regression test proves salesforce floor holds; suite green.

## Step 4 — R1 logarithmic growth law (core change, highest sensitivity)
- `instance.py`: make `acquisition_ceiling` default-enabled with documented
  `target_stock_multiplier` + `slack`; keep the existing log preprocessing (`:72-89`).
- `model.py`: remove smoothing block (`:131-140`); the log-ceiling constraint
  (`:142-149`) becomes the sole `t >= 13` acquisition bound.
- Update `docs/model.md` §"Logarithmic acquisition ceiling": drop "optional/additive",
  state it is the primary growth law; update §smoothing references.
- Validator (`config.py`): require ceiling params when enabled; reject leftover
  `g_max_suavizado`-only growth configs or map them to a migration warning.
- Migration: audit `configs/*.yaml`, `benchmark_v*/`, `outputs/*/config.yaml` for configs
  relying on smoothing; add ceiling blocks.
- Tests: update/replace smoothing tests with saturation-curve tests (monotonic decreasing
  marginal cap; cumulative reaches `S_target`; slack tolerance honored). Re-baseline EV
  snapshots from Step 0 with documented expected deltas.
- Gate: full suite green; before/after EV diff explained in PR.

## Step 5 — Wrap
- Update `CONTEXT.md` / `docs/END_TO_END_FLOW_CONTEXT.md` growth narrative.
- PR referencing ADR 0010; summarize behavior deltas (growth shape, channel floor,
  pre-feasibility, solver time) and EV impact.

## Risk notes
- Step 4 changes optimizer feasible region -> EV and acquisition trajectories shift by
  design. Largest blast radius: re-baseline all golden/regression artifacts.
- Removing smoothing may make some previously-bounded configs grow to the ceiling; verify
  cash floor `-VC` still binds where expected (the "surfing -VC" dynamic from ADR 0010).
- `m_op` integer count unchanged; Step 4 does not add integers, so solver size is stable.

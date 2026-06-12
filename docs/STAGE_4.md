# Stage 4 Handoff — Working-Capital Cash Floor with DD Financing-Gap Diagnostic

## Scope implemented

Phase 4 of `docs/PLAN_DETERMINISTIC_ACQUISITION_CAC_CASH.md`: a hard working-capital
cash floor indexed to the financing ticket (`Caja[t] >= -VC`), plus a secondary
diagnostic solve that quantifies the financing gap when the main model is infeasible.
The main objective stays pure discounted EBITDA — the floor is a hard constraint, never a
penalty.

### Main model (hard floor)

```text
Caja[1] = VC + EBITDA[1]
Caja[t] = Caja[t-1] + EBITDA[t]
Caja[t] >= -VC                 ∀t        (when working_capital.enabled)
```

Cash may go negative down to `-VC` (this is **not** `>= 0`; it enables breakeven modeling).

### Diagnostic (only on infeasibility)

`build_model(instance, elastic_floor=True)` builds a *fresh* model: relax the floor with
`Caja[t] + cash_shortfall[t] >= -VC`, `cash_shortfall >= 0`, and replace the objective
with `minimize Σ cash_shortfall`. The main model is never mutated.

`solve_with_working_capital(instance)` returns:
- feasible → `{feasible: True, min_cash_balance, min_cash_month, financing_gap_usd: 0}`
- infeasible → `{feasible: False, financing_gap_usd, first_breach_month, total_gap}`

### Config (disabled by default; supersedes liquidity_policy when enabled)

```yaml
working_capital:
  enabled: true
  floor_mode: ticket
```

## Files changed

| File | Change |
|---|---|
| `src/adventure_capital/config.py` | `working_capital` default (disabled); validation of `floor_mode`. |
| `src/adventure_capital/model.py` | `build_model(..., elastic_floor=False)`; hard floor `Caja[t] >= -VC` when enabled (supersedes `liquidity_policy`); `cash_shortfall` vars + min-shortfall objective in elastic mode; `diagnose_financing_gap`, `solve_with_working_capital`, `_shortfall_value`. |
| `src/adventure_capital/calibration/checks.py` | C04 floor source = `-VC` when working_capital enabled (handles both generated-instance and raw-config shapes). |
| `docs/model.md` | New "Working-capital cash floor (Phase 4)" section. |
| `configs/demo-working-capital.yaml` | New demo config (demo-complex + working_capital). |
| `tests/test_cash_floor.py` | New: 6 Phase 4 tests. |
| `docs/STAGE_4.md` | This handoff. |

## Key design decisions

1. **Hard floor via an `elastic_floor` flag on `build_model`.** Diagnostic path builds a
   separate model (`elastic_floor=True`) with shortfall vars and a min-shortfall
   objective. The main EBITDA model object is never modified
   (`test_diagnostic_does_not_modify_main_model`).
2. **Floor supersedes `liquidity_policy` only when `working_capital.enabled`.** No block
   ⇒ untouched legacy path (regression-safe). `floor = -VC` (ticket mode); `fixed` mode
   reserved for future.
3. **Feasibility is governed by the fixed period.** Months 1-12 acquisition is fixed
   (`A_base`), so the fixed cumulative-EBITDA trough (month 9 for demo-complex,
   `≈ -107380`) sets the minimum fundable `VC`: feasible needs `VC >= ~53690`. Test
   configs are tuned around this trough (feasible 110k, binding 53.7k, infeasible 40k).
4. **Diagnostic outputs:** `financing_gap_usd` = max monthly shortfall (peak additional
   financing needed beyond the ticket); `first_breach_month` = first month with shortfall;
   `total_gap` = Σ shortfall.
5. **Pipeline scope:** feasible configs flow through the normal `all` pipeline
   (`solve_growth_plan` builds the floor). The infeasible→diagnostic route is exercised by
   `solve_with_working_capital` and the unit tests; full DD-report gap wiring is left to a
   later integration step (see open debt).

## Invariants verified

- `Caja[t] >= -VC` for every period on feasible runs (`test_cash_floor_feasible`, demo).
- Floor binds at `-VC` for a tightly-funded config (`test_cash_floor_binding`).
- Infeasible config ⇒ diagnostic returns positive `financing_gap_usd`, a `first_breach_month`, positive `total_gap` (`test_cash_floor_infeasible_diagnostic`).
- `Caja_final == VC + Σ EBITDA` (rel residual ~1e-8; demo + `test_cash_identity`).
- Legacy config without `working_capital` ⇒ no `cash_shortfall` vars, Phase 3 behavior unchanged (`test_legacy_no_working_capital`).
- Diagnostic build/solve does not modify the main model (`test_diagnostic_does_not_modify_main_model`).
- Main objective contains only discounted EBITDA (floor is a constraint).
- C04 uses `-VC` floor when working_capital enabled (verified at unit level for both instance shapes).
- Untouched: unit economics (Phase 5), report narrative, PDF, UI, stochastic model.

## Test results

```
uv run pytest
# 90 passed, 3 skipped   (84 Phase 3 baseline + 6 new cash-floor tests)

uv run pytest tests/test_cash_floor.py
# 6 passed
```

## Demo output

```
configs/demo-working-capital.yaml -> outputs/demo-wc-stage-4
```

Solver **Optimal**; `min_cash = 2620 >= -VC (-110000)` (floor not binding for this VC);
`Caja_final == VC + Σ EBITDA` (rel ~1e-8); consistency `all_passed = True`; report.html
rendered. C04 floor source confirmed `-VC` against the saved output.

Output path gitignored.

## Open debt

- **Pipeline infeasible path not fully wired into the DD report.** `solve_with_working_capital`
  returns the structured gap, but the `all` pipeline (`run_assessment`) still calls
  `solve_growth_plan` and would error on an infeasible main solve. Routing the diagnostic
  gap into the DD report narrative/alert is a follow-up (no shipped demo config is
  infeasible, so this is not hit in practice yet).
- **DD `rules.py` (`compute_liquidity_diagnostic`, `_rule_funding_gap`)** still read
  `optimized["Caja"]` (feasible-run trough). They were not changed to consume the
  secondary diagnostic gap on infeasibility.
- **`floor_mode: fixed`** reserved but not implemented.
- **Stochastic parity / cash-init divergence** (`evaluate.py` starts cash at `0.0` vs
  deterministic `VC + EBITDA[1]`) remains flagged, out of scope.

## Re-audit checklist (for Codex)

1. Confirm the floor is `Caja[t] >= -VC` (not `>= 0`) and applies only when `working_capital.enabled`.
2. Confirm no working_capital block ⇒ legacy `liquidity_policy` path, no `cash_shortfall` vars.
3. Confirm the main objective has no shortfall/penalty term; floor is a hard constraint.
4. Confirm the diagnostic builds a *separate* model (`elastic_floor=True`) and never mutates the main model.
5. Confirm diagnostic dict fields: `financing_gap_usd`, `first_breach_month`, `total_gap`.
6. Confirm `Caja_final == VC + Σ EBITDA` and the documented operational-flows assumption.
7. Confirm C04 floor = `-VC` when enabled (both instance/config shapes).
8. Run `uv run pytest` → expect 90 passed, 3 skipped.

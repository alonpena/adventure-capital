# Stage 1 Handoff — Logarithmic Acquisition Ceiling

## Scope implemented

Phase 1 of `docs/PLAN_DETERMINISTIC_ACQUISITION_CAC_CASH.md`: an optional
logarithmic acquisition ceiling with slack. A conservative, monotonically
decreasing per-period brake on **total** acquisition for `t >= 13`, modeling
market saturation. It is an **additional** upper bound layered on top of the
existing smoothing constraints — it never replaces them. Disabled by default,
so all existing configs are unaffected.

### Formula (`instance.py`)

```text
S_0      = sum_s sum_{t=1..12} A_base[s,t]     # total year-1 acquisition
S_target = S_0 * target_stock_multiplier
H_post   = H - 12
K        = (S_target - S_0) / ln(1 + H_post)
S(t)     = S_0 + K * ln(1 + (t - 12))          for t >= 13   (S(12) = S_0)
ceiling[t] = S(t) - S(t-1)
```

### Constraint (`model.py`)

```text
sum_s A[s,t] <= ceiling[t] * (1 + slack)        for t >= 13
```

### Config block (disabled by default)

```yaml
acquisition_ceiling:
  enabled: false
  target_stock_multiplier: 2.0
  slack: 0.15
```

## Files changed

| File | Change |
|---|---|
| `src/adventure_capital/config.py` | Added `acquisition_ceiling` to `_DEFAULT_CONFIG`; validation (when enabled) requires `target_stock_multiplier > 1.0`, `slack >= 0`. |
| `src/adventure_capital/instance.py` | Compute `log_ceiling` dict (t≥13) and `ceiling_slack` when enabled; added to instance dict. `import math`. |
| `src/adventure_capital/model.py` | One constraint family: `sum_s A[s,t] <= ceiling[t]*(1+slack)` for t≥13, only when `log_ceiling` present. |
| `src/adventure_capital/results.py` | Diagnostic columns `Log_ceiling`, `Log_ceiling_slack` when ceiling active (NaN for t≤12). |
| `docs/model.md` | New "Logarithmic acquisition ceiling (optional)" section. |
| `configs/demo-complex-ceiling.yaml` | New: demo-complex + ceiling (2.0x, slack 0.15). |
| `configs/demo-ceiling-tight.yaml` | New stress: ceiling 1.2x, slack 0.0. |
| `configs/legacy/*.yaml` | New: frozen regression baseline (demo-complex/good/bad). Never modify. |
| `tests/test_ceiling.py` | New: 7 Phase 1 tests. |
| `docs/STAGE_1.md` | This handoff. |

## Invariants verified

- Year 1 (months 1-12) acquisition stays exactly `A_base` with ceiling active — `test_year1_immutable_with_ceiling`.
- Existing 3-period moving-average smoothing untouched (model.py:73-82 unchanged); ceiling is additive only.
- `A[s,t]` remains per-service total acquisition; cap binds `sum_s A[s,t]`.
- Ceiling never breached: `sum_s A[s,t] <= ceiling[t]*(1+slack)` for t≥13 — `test_ceiling_binds`.
- Ceiling cannot raise EV — `test_ceiling_lowers_ev` (tight ≤ open).
- Disabled ceiling = no diagnostic columns, no constraint, baseline behavior — `test_ceiling_disabled_regression`.
- Marginal ceiling monotonically decreasing; cumulative reaches `S_target - S_0` — `test_ceiling_formula_monotonic`.
- All existing CSV columns preserved (`CAC`, `Adq_clientes`, `Ingresos`, `EBITDA`, `Caja`, service-prefixed).
- Untouched: valuation, unit_economics, stochastic, report narrative, UI, PDF.

## Test results

```
uv run pytest
# 68 passed, 3 skipped   (61 baseline + 7 new ceiling tests)

uv run pytest tests/test_ceiling.py
# 7 passed
```

## Demo output

```
uv run adventure-capital all \
  --config configs/demo-complex-ceiling.yaml \
  --output outputs/demo-complex-stage-1 \
  --document reports/valuation-ev.template.yaml \
  --schema reports/schema/valuation-ev.schema.yaml
```

- Solver status: **Optimal**
- `Log_ceiling` / `Log_ceiling_slack` columns present in `optimized_results.csv`
- Months 1-12: ceiling columns NaN (year 1 immutable)
- Months 13+: `Adq_clientes <= Log_ceiling_slack` for every period (no breach)
- Cap binds in early post-year-1 months (e.g. t=14 acquisition equals slack ceiling)

Output path: `outputs/demo-complex-stage-1/` (gitignored).

## Open debt

- **Stochastic SAA does not yet mirror the ceiling.** `stochastic/model.py::build_saa_model`
  must replicate `sum_s A[s,t] <= ceiling[t]*(1+slack)` before stochastic parity, or the
  stochastic plan can exceed the deterministic cap and report optimistic plans.
- **Explicit / per-service ceiling mode not implemented.** MVP uses formula mode only
  (single total cap). Per-service override and `mode: explicit` from the plan are deferred;
  not needed for MVP.
- Pre-existing known issue (unrelated to this stage): stochastic `evaluate.py` initializes
  cash as `0.0` vs deterministic `VC + EBITDA[1]`. Still flagged, out of scope.

## Re-audit checklist (for Codex)

1. Confirm `model.py` ceiling block is an **additional** constraint — smoothing constraints
   (lines ~73-82) are byte-for-byte unchanged.
2. Confirm ceiling only applies for `t >= 13`; year-1 `A_base` equality constraint untouched.
3. Confirm `instance.py` formula: `S_0` = total year-1 acquisition across all services;
   `H_post = H - 12`; marginal `ceiling[t] = S(t) - S(t-1)`.
4. Confirm validation only triggers when `enabled: true`; disabled config needs no extra fields.
5. Confirm no diagnostic columns / no constraint when ceiling disabled (regression test).
6. Confirm legacy configs in `configs/legacy/` are untouched and `demo-complex.yaml`,
   `demo-good.yaml`, `demo-bad.yaml` have **no** ceiling block.
7. Run `uv run pytest` → expect 68 passed, 3 skipped.

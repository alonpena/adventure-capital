# Stage 5 Handoff — Unit Economics, LTV/CAC Consistency, Breakeven Analysis

## Scope implemented

Phase 5 of `docs/PLAN_DETERMINISTIC_ACQUISITION_CAC_CASH.md`: rework unit economics so
every metric is **annual** and **summed over service lines** (never averaged), fix LTV
and LTV/CAC, and add post-solve breakeven / payback / runway diagnostics. Everything is
post-solve arithmetic — no MILP variables. DCF/valuation untouched; Enterprise Value
only.

### Corrected formulas

```text
annual_frequency_s = 12 / frecuencia_s
gross_margin_s     = 1 - c_u_s / ticket_s
annual_churn_s     = churn_anual_s[0]

LTV   = Σ_s ticket_s * annual_frequency_s * gross_margin_s / annual_churn_s   (summed)
CAC   = cumulative_cac_per_user = Σ total_acquisition_cost / Σ new_customers
LTV/CAC = LTV / CAC

annual_gross_profit_per_customer = Σ_s (ticket_s - c_u_s) * annual_frequency_s
annual_contribution_per_customer = annual_gross_profit_per_customer - CAC
breakeven_customers = annual_fixed_costs / annual_contribution_per_customer
payback_customers   = VC / annual_contribution_per_customer
payback_month       = first t where Caja[t] >= VC
runway[t]           = Caja[t] / |EBITDA[t]|   (NaN when EBITDA[t] >= 0)
```

`annual_fixed_costs` = year-1 sum of `G_adm + RRHH`.

## Files changed

| File | Change |
|---|---|
| `src/adventure_capital/unit_economics.py` | New pure functions: `annual_revenue_per_customer`, `annual_gross_profit_per_customer`, `annual_ltv`, `compute_runway`, `compute_unit_economics_metrics`. Fixed the 15-row table's `LTV` (annual, summed) and `LTV/CAC` (cumulative CAC); updated the LTV row label. |
| `docs/model.md` | New "Unit economics and breakeven (Phase 5)" section. |
| `tests/test_unit_economics.py` | New: 9 Phase 5 tests. |
| `docs/STAGE_5.md` | This handoff. |

## Key design decisions

1. **Kept the 15-row `unit_economics.csv` table; corrected only `LTV`/`LTV/CAC` values.**
   The table contract (labels + `Valor`, read by the report, C08, and sensitivity) is
   preserved, so `len == 15` and downstream consumers are unaffected. The old LTV used
   `average_ticket × first-service GP / monthly churn` — replaced by the annual,
   service-summed LTV.
2. **Breakeven / payback / runway live in a separate metrics dict**
   (`compute_unit_economics_metrics`), not as new table rows — avoids breaking the table
   contract and `test_phase3`'s `len == 15`. Exposed as pure functions and unit-tested
   directly.
3. **CAC value is unchanged.** `cumulative_cac_per_user` (Phase 3) equals the old
   `ΣCAC / Σacquisition`, so only LTV drives the corrected ratio.
4. **High LTV/CAC is a documented artifact.** With the corrected annual LTV the demo
   ratio is ~21.8× (> the C08 band of 20×), so C08 fires as a warning flagging the
   structural artifact (annual churn denominator × high gross margin). It is **not**
   silently corrected.
5. **No `results.py` / `pipeline.py` edits.** Phase 5 is contained in `unit_economics.py`
   (which the pipeline already calls) plus tests/docs, to keep the change isolated.

## Invariants verified

- LTV uses annual frequency and annual churn (not monthly) — `test_ltv_uses_annual_metrics`.
- LTV sums service lines, not averages — `test_ltv_sums_services_not_averages`.
- LTV/CAC uses `cumulative_cac_per_user` — `test_cac_uses_cumulative`.
- C08 fires (artifact message) when ratio > band — `test_ltv_cac_alert_c08`.
- Breakeven and payback customer counts match manual formulas.
- `payback_month` = first month `Caja >= VC`.
- `runway` is NaN where `EBITDA >= 0`.
- Legacy regression: computing metrics does not change EV / EBITDA / Caja (post-solve only).
- `unit_economics.csv` still has 15 rows; report renders; consistency `all_passed = True`.
- DCF / `valuation.py` untouched; no Equity Value.

## Test results

```
uv run pytest
# 101 passed, 3 skipped   (92 Phase 4 baseline + 9 new unit-economics tests)

uv run pytest tests/test_unit_economics.py
# 9 passed
```

## Demo output

```
configs/demo-complex.yaml -> outputs/demo-complex-stage-5
```

`unit_economics.csv`: 15 rows; LTV = 17,622 (annual, summed); CAC = 807;
LTV/CAC = 21.8×. Consistency `all_passed = True`; report.html rendered. Calibration C08
fires as a warning: *"LTV/CAC 21.8× fuera de banda [1.0, 20.0]. Artefacto de fórmula …"* —
the intended documented-artifact behavior.

Output path gitignored.

## Open debt

- **Breakeven/payback/runway metrics are not yet persisted/rendered** in the report. They
  are computed by `compute_unit_economics_metrics` and unit-tested, but no pipeline/report
  wiring writes them to disk (left out to avoid touching the dirty `pipeline.py`/`results.py`
  during the concurrent Phase 4 follow-up work).
- **C08 band / artifact** is surfaced but the report narrative still suggests
  "ARPU ponderado y margen por servicio" as the fix; the LTV is now per-service summed, so
  that suggestion text could be refreshed.
- **Stochastic parity** (ceiling, channels, CAC, cash floor) remains flagged.

## Re-audit checklist (for Codex)

1. Confirm LTV = `Σ_s ticket_s·(12/frecuencia_s)·gm_s / annual_churn_s` (annual, summed).
2. Confirm CAC = `cumulative_cac_per_user`; LTV/CAC uses it.
3. Confirm the unit-economics table still has 15 rows with unchanged labels.
4. Confirm no MILP variables added; EV/EBITDA/Caja unchanged (post-solve only).
5. Confirm C08 fires on high ratio and flags it as an artifact (not corrected).
6. Confirm breakeven/payback formulas and `runway` NaN-when-profitable.
7. Run `uv run pytest` → expect 101 passed, 3 skipped.

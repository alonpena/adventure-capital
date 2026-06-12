# Stage 3 Handoff — CAC Cost-Component Aggregation and Traceability

## Scope implemented

Phase 3 of `docs/PLAN_DETERMINISTIC_ACQUISITION_CAC_CASH.md`: decompose CAC into
linear cost-component MILP variables, wire the previously-missing third-party cost, and
add post-solve per-user CAC traceability. **No CAC ratio enters the MILP** — all
per-user ratios are computed arithmetically in `results.py`.

### MILP cost components (linear)

```text
salesforce_cac_cost[t] = rem_v*V + rem_l*L + sum_s (com_v+com_l)*ticket[s]*A_sf[s,t]
third_party_cost[t]    = sum_s tp_commission*ticket[s]*A_tp[s,t]     (when third-party active)
total_acquisition_cost[t] = salesforce_cac_cost + advertising_cac_cost + third_party_cost
CAC[t] = total_acquisition_cost[t]                                   (canonical alias)
```

`EBITDA[t]` still subtracts `CAC[t]`; legacy configs stay byte-identical.

### Post-solve traceability (results.py only)

```text
new_customers[t]           = Adq_clientes[t]
period_cac_per_user[t]     = total_acquisition_cost[t] / new_customers[t]            (NaN if 0)
cumulative_cac_per_user[t] = cumsum(total_acquisition_cost) / cumsum(new_customers)  (NaN if 0)
```

## Files changed

| File | Change |
|---|---|
| `src/adventure_capital/config.py` | `channels.third_party.commission` default `0.0`; validation `commission >= 0` when third-party active. |
| `src/adventure_capital/instance.py` | Store `third_party.commission` in normalized channels. |
| `src/adventure_capital/model.py` | MILP vars `salesforce_cac_cost`, `third_party_cost` (when tp active), `total_acquisition_cost`; `cac[t] == total_acquisition_cost[t]`; third-party commission cost wired. |
| `src/adventure_capital/results.py` | `_safe_div` helper; component columns + `new_customers`, `period_cac_per_user`, `cumulative_cac_per_user` (post-solve). |
| `src/adventure_capital/financial_model.py` | Mirror component + ratio columns for months 1-12. |
| `docs/model.md` | New "CAC cost components and traceability (Phase 3)" section. |
| `tests/test_cac_aggregation.py` | New: 8 Phase 3 tests. |
| `docs/STAGE_3.md` | This handoff. |

## Key design decisions

1. **Cost components are MILP variables; `cac[t] == total_acquisition_cost[t]`.** This
   yields an exact component-sum identity and keeps EBITDA/CAC byte-identical for legacy
   (`salesforce_cac_cost ≡` old CAC, other components 0). The old inline `cac[t] == ...`
   expression became the `salesforce_cac_cost[t]` definition.
2. **Third-party cost = commission on ticket** (`tp_commission * ticket * A_tp`),
   mirroring the salesforce commission. New `channels.third_party.commission` param
   (default 0.0). Dormant — no demo config activates third-party — but tested via an
   inline config that forces `A_tp > 0` through `min_share`.
3. **All ratios post-solve** with a shared `_safe_div` (NaN when denominator is 0).
   `new_customers` = total acquisition (`Adq_clientes`).
4. **Component-sum identity tolerance.** CBC reports the component variables within its
   feasibility tolerance (~6e-4 observed), so identity tests use `abs <= 1e-2`. The
   `CAC == total_acquisition_cost` equality is exact (same variable), checked at 1e-9.

## Invariants verified

- `salesforce_cac_cost + advertising_cac_cost + third_party_cost ≈ total_acquisition_cost == CAC` (legacy and mixed).
- `total_acquisition_cost == CAC` exactly.
- `period_cac_per_user == total_acquisition_cost / new_customers`; `cumulative_cac_per_user == cumsum/cumsum`.
- `_safe_div` returns NaN on zero denominator (not an exception).
- Existing columns preserved (`CAC`, `Adq_clientes`, `Ingresos`, `EBITDA`, `Caja`); new columns additive.
- No CAC ratio variable in the MILP (`period_/cumulative_cac_per_user` absent from solution variables).
- Third-party cost wired: `third_party_cost == commission*ticket*A_tp`, non-zero when forced.
- EBITDA identity and `Caja = VC + ΣEBITDA` hold (demo consistency `all_passed=True`).
- Untouched: cash floor, unit economics, report narrative, PDF, UI, stochastic model.

## Test results

```
uv run pytest
# 84 passed, 3 skipped   (76 Phase 2 baseline + 8 new CAC-aggregation tests)

uv run pytest tests/test_cac_aggregation.py
# 8 passed
```

## Demo output

```
configs/demo-mixed-channels.yaml -> outputs/demo-mixed-stage-3
```

Solver **Optimal**; all component + ratio columns present; `total_acquisition_cost == CAC`;
consistency `all_passed = True`; report.html rendered. Sample (t=14):
`salesforce_cac_cost=15551.4, advertising_cac_cost=1021.3, total=16572.7,
period_cac_per_user=811.4, cumulative_cac_per_user=786.3`.

Output path gitignored.

## Open debt

- **Third-party channel still has no demo config / no recta.** Cost is wired and tested
  via an inline forced config; no shipped YAML activates third-party.
- **Standard-report CAC table/chart** (`standard_report/tables.py::build_cac_table`,
  `charts.py::_plot_cac_components`) were not changed to *prefer* the new component
  columns. The report still renders (legacy decomposition path); preferring component
  columns is deferred — not required for green and not in this stage's minimal scope.
- **Stochastic parity gap** (channels, ceiling, CAC components) remains flagged.

## Re-audit checklist (for Codex)

1. Confirm `cac[t] == total_acquisition_cost[t]` and `salesforce_cac_cost` reproduces the
   old inline CAC expression exactly (legacy byte-identical EBITDA/CAC).
2. Confirm no ratio is a MILP variable; `period_/cumulative_cac_per_user` are computed in
   `results.py` only.
3. Confirm `_safe_div` NaN-guards both period and cumulative ratios.
4. Confirm component-sum identity within solver tolerance and `total == CAC` exact.
5. Confirm third-party cost = `commission*ticket*A_tp`; inactive ⇒ `third_party_cost = 0`.
6. Confirm new columns are additive; existing CSV columns preserved.
7. Confirm `financial_model.py` (months 1-12) exposes the same component/ratio columns.
8. Run `uv run pytest` → expect 84 passed, 3 skipped.

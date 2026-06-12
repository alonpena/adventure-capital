# Stage 2 Handoff — Acquisition Channel Split, Advertising Recta, Share Bounds

## Scope implemented

Phase 2 of `docs/PLAN_DETERMINISTIC_ACQUISITION_CAC_CASH.md`: split total
acquisition into salesforce / advertising / third-party channels, add a continuous
linear advertising recta, and add linear channel-share bounds. Channel activation is
exogenous (YAML), never a decision variable. Fully backward-compatible: a config with
no `channels` block stays salesforce-only and produces identical output with no channel
columns.

### Channel identity (per service-period)

```text
A[s,t] = A_sf[s,t] + A_ad[s,t] + A_tp[s,t]
```

`A[s,t]` remains the total per-service acquisition used by cohorts, revenue,
recurrence, smoothing, and the Phase 1 log ceiling — all unchanged.

### Advertising recta (continuous, ADR-0006)

```text
b = (A_max - A_min) / (I_max - I_min)
a = A_min - b * I_min
A_ad_total[t] = sum_s A_ad[s,t] = a + b * I_ad[t]      (all t)
A_ad_total[t] <= A_ad_cap
advertising_cac_cost[t] = I_ad[t]
I_min <= I_ad[t] <= I_max                              (t >= 13 only)
```

### Salesforce capacity binds salesforce only

```text
sum_s A_sf[s,t] <= meta * V[t - lag]      (t >= 13)
salesforce inactive -> A_sf = 0, V = L = 0, no salary CAC
```

### Linear share bounds (no bilinearities)

```text
A_ch_total[t] >= min_share * A_total[t]   (added only when min_share > 0)
A_ch_total[t] <= max_share * A_total[t]   (added only when max_share < 1)
```

### CAC

```text
CAC[t] = rem_v*V + rem_l*L + sum_s (com_v+com_l)*ticket[s]*A_sf[s,t] + advertising_cac_cost[t]
```

## Files changed

| File | Change |
|---|---|
| `src/adventure_capital/config.py` | `channels` block in `_DEFAULT_CONFIG`; validation: per-channel `0<=min<=max<=1`, sum of active `max_share >= 1.0`, advertising `I_max>I_min`, `A_max>A_min`, slope `b>0`, `A_ad_cap>=0`. |
| `src/adventure_capital/instance.py` | Normalize `channels` (active flags, shares, `any_split`); preprocess advertising `a`, `b`. |
| `src/adventure_capital/model.py` | Per-service `A_sf`/`A_ad`/`A_tp` vars; channel identity; advertising recta + cap + cost; share bounds; capacity binds `A_sf`; CAC uses `A_sf` + advertising cost; salesforce-inactive forcing. |
| `src/adventure_capital/results.py` | Channel diagnostic columns (only when `any_split`): `A_salesforce`, `A_advertising`, `A_third_party`, `advertising_cac_cost`, `advertising_investment`, `share_*`. |
| `src/adventure_capital/financial_model.py` | Fixed period: salesforce-inactive ⇒ 0 sellers/leaders/salary; advertising-only ⇒ year-1 `advertising_cac_cost` via recta. |
| `docs/model.md` | New "Acquisition channels (optional, Phase 2)" section. |
| `docs/adr/0006-advertising-efficiency-semantics.md` | New ADR. |
| `configs/demo-advertising-only.yaml`, `demo-mixed-channels.yaml` | New demo configs. |
| `tests/test_channels.py` | New: 8 Phase 2 tests. |
| `docs/STAGE_2.md` | This handoff. |

## Key design decisions

1. **Per-service advertising variables `A_ad[s,t]`** (sum = `A_ad_total[t]`), not
   company-level proration. This keeps cohort/revenue math on `A[s,t]` untouched and
   avoids the bilinear product that proration (`A_ad * A_sf[s]/sum`) would introduce.
   `A[s,t]` is still the per-service total acquisition.

2. **`A_ad` → `A[s,t]` mapping:** advertising acquisition is allocated by the optimizer
   across services via `A_ad[s,t]`, each tied to its service through the channel
   identity. No arbitrary "first service" attribution.

3. **Recta applies for all `t`; `I_ad` range only for `t >= 13`.** Year 1 is the
   exogenous Fixed Acquisition Period: its acquisition equals `A_base`, flowing through
   the active channel (advertising for advertising-only). The recta still defines the
   implied year-1 investment, but `I_min/I_max` do not constrain it. **Consequence:** a
   mixed config carries a small forced year-1 advertising minimum (`A_ad_total >= a`).

4. **Column named `advertising_investment`, not `I_ad`.** The consistency check
   `revenue_decomposition_by_service` sums every `I_`-prefixed column as service revenue;
   an `I_ad` column would be miscounted. (This bug was caught and fixed during the demo.)

5. **Config feasibility tension (documented):** an advertising `I_min > 0` forces
   `A_ad_total >= A_min` every month `t >= 13`, which conflicts with the late, small Phase 1
   log-ceiling marginal. The demo configs set `I_min = A_min = 0` (advertising scalable
   from zero) so the two features compose. Configs that set `I_min > 0` must keep the
   ceiling loose enough that `ceiling[t]*(1+slack) >= A_min` for all `t`.

## Invariants verified

- Year 1 `A[s,t] == A_base` preserved (legacy regression + advertising-only solve).
- Existing smoothing + Phase 1 log ceiling still bind `A[s,t]` (`test_ceiling_still_binds_with_channels`).
- Legacy config (no `channels`) ⇒ `any_split=False`, no channel columns, salesforce-only behavior (`test_legacy_no_channels_regression`).
- Advertising-only solves with `A_sf = 0` for all `t`, positive `A_ad`, `advertising_cac_cost == advertising_investment`.
- Advertising recta identity `A_ad_total = a + b*I_ad` for all `t`.
- Saturation `A_ad_total <= A_ad_cap`.
- Share bounds hold for active channels with non-trivial bounds.
- Salesforce capacity binds only `A_sf`; advertising acquisition is not limited by salesforce capacity.
- Validator rejects active-`max_share` sum < 1.0, `A_max<=A_min`, `I_max<=I_min`, slope `<= 0`.
- EBITDA identity and `Caja = VC + ΣEBITDA` hold (consistency `all_passed=True`, rel residual ~8e-9).
- Untouched: cash floor / liquidity policy, unit economics, report narrative, PDF, UI, stochastic model.

## Test results

```
uv run pytest
# 76 passed, 3 skipped   (68 Phase 1 baseline + 8 new channel tests)

uv run pytest tests/test_channels.py
# 8 passed
```

## Demo output

```
configs/demo-mixed-channels.yaml      -> outputs/demo-mixed-stage-2
configs/demo-advertising-only.yaml    -> outputs/demo-adonly-stage-2
```

Both: solver **Optimal**, channel columns present, advertising recta holds,
`advertising_cac_cost == advertising_investment`, log ceiling not breached (t>=13),
share bounds respected (mixed: advertising share max = 0.4, salesforce share >= 0.3),
consistency `all_passed = True`, report.html rendered.

`configs/demo-complex.yaml` (no channels): solves Optimal, `any_split=False`, no
channel columns — perfect regression (verified by `test_legacy_no_channels_regression`).

Output paths gitignored.

## Open debt

- **Third-party channel cost not wired.** `A_tp[s,t]` variables exist and obey the
  identity/share bounds, but third-party cost components land in Phase 3. No demo config
  activates third-party yet.
- **Stochastic parity gap.** `stochastic/model.py::build_saa_model` does not mirror the
  channel split, advertising recta, or share bounds. A stochastic plan could ignore them.
  Out of scope for this stage; flagged for stochastic parity work (alongside the Phase 1
  ceiling parity gap and the known cash-init divergence).
- **Per-service share bounds not implemented.** Share bounds apply to channel totals only.
- **Mixed year-1 forced advertising minimum** (`A_ad_total >= a`) is a small artifact of
  the "recta-all-t" decision; acceptable for the fixed period, documented in decision 3.
- **Fixed-period model vs main model for advertising-only year-1:** `financial_model.py`
  reconstructs year-1 advertising cost from the recta; for mixed configs it attributes
  year-1 to salesforce. `fixed_cashflow.csv` is a reference artifact and is not
  consistency-checked (consistency runs on `optimized_results.csv`).

## Re-audit checklist (for Codex)

1. Confirm legacy path: config with no `channels` block ⇒ `instance["channels"]["any_split"]
   is False, no `A_sf`/`A_ad`/share columns, byte-identical solve to Phase 1.
2. Confirm channel identity `A[s,t] == A_sf + A_ad + A_tp` added for every `(s,t)`.
3. Confirm salesforce capacity uses `sum_s A_sf`, not `sum_s A` (model.py).
4. Confirm advertising vars are continuous (no `cat="Integer"`/binary); recta `A_ad_total = a + b*I_ad`.
5. Confirm `I_min<=I_ad<=I_max` applied only for `t >= 13`; recta + cap + cost for all `t`.
6. Confirm share constraints are linear (`share * A_total`), added only for non-trivial bounds.
7. Confirm CAC uses `A_sf` for commissions and adds `advertising_cac_cost`; EBITDA identity holds.
8. Confirm no `I_`-prefixed advertising column leaks into revenue decomposition (`advertising_investment`).
9. Confirm Phase 1 ceiling + year-1 immutability still hold with channels active.
10. Run `uv run pytest` → expect 76 passed, 3 skipped.

# Deterministic Core Audit and Staged Plan: Acquisition Ceilings, Channel CAC, Cash Floor

Status: planning/audit only. No code implementation in this document.

Baseline checked during audit:

```bash
uv run pytest
# 61 passed, 3 skipped
```

## Scope guard

In scope:

- PuLP/CBC deterministic MILP core.
- YAML/config preprocessing.
- Monthly output metrics and CSV/report data contracts.
- Compatibility hooks for valuation, Due Diligence, stochastic SAA/Monte Carlo, and HTML report layers.

Out of scope:

- UI changes.
- PDF export work.
- Report narrative block rewrites.
- Stochastic dominance analysis.
- Equity Value/cap-table module.

## Current architecture map

| Layer | Files / functions |
|---|---|
| Config / validation | `src/adventure_capital/config.py`: `default_config`, `load_config`, `validate_config`; YAMLs under `configs/` |
| Instance preprocessing | `src/adventure_capital/instance.py`: `generate_instance` |
| Fixed 12-month cashflow | `src/adventure_capital/financial_model.py`: `build_fixed_period_financial_model`, `build_financial_model` |
| Deterministic MILP | `src/adventure_capital/model.py`: `build_model`, `solve_model`, `solve_growth_plan` |
| Result extraction | `src/adventure_capital/results.py`: `extract_results`, `summarize_results` |
| Valuation | `src/adventure_capital/valuation.py`: `calculate_dcf`, `calculate_multiples_valuation`, `calcular_valor_residual` |
| Unit economics | `src/adventure_capital/unit_economics.py`: `calculate_unit_economics` |
| Basic artifacts | `src/adventure_capital/reporting.py`: `write_core_csv_outputs`, `generate_dashboard`, `generate_markdown_report`, `generate_report` |
| Standard report package | `src/adventure_capital/standard_report/package.py`, `tables.py`, `charts.py`, `sensitivity.py`, `consistency.py` |
| Calibration / DD | `src/adventure_capital/calibration/checks.py`; `src/adventure_capital/due_diligence/rules.py`, `workflow.py`, `report.py` |
| Stochastic compatibility | `src/adventure_capital/stochastic/model.py`, `evaluate.py`, `results.py`, `scenarios.py` |
| CLI | `src/adventure_capital/cli.py` |

## Audit findings

### Cross-cutting findings

- Existing deterministic MILP uses one acquisition variable `A[s,t]`. That variable currently means total service acquisition, not channel-specific acquisition.
- Existing acquisition dynamics are smoothing-only: year 1 fixed, month 13 transition cap, month 14 growth cap, months 15+ three-period moving average cap with `g_max_suavizado`.
- Existing CAC is one aggregate variable `CAC[t]`: seller salary + leader salary + seller/leader commission on new sales. No explicit advertising component exists in current deterministic code.
- Current source does not expose explicit third-party channel variables or channel activation flags in `model.py`. If those exist in business spec, implementation must preserve them as exogenous config parameters, not decision variables.
- Existing `unit_economics.py` averages ticket/frequency across services and computes LTV from monthly churn. This conflicts with confirmed annual/summed-service rule and must be fixed in Phase 5.
- Existing stochastic Phase B (`stochastic/evaluate.py`) initializes cash from `0.0`, not `VC`. Deterministic `model.py` initializes cash as `VC + EBITDA[1]`. This is a known stochastic parity issue, out of scope for this deterministic refinement plan but explicitly retained in the compatibility contract.

## A) Rule-by-rule audit

### 1. Logarithmic acquisition ceiling

| Item | Audit |
|---|---|
| Files/functions involved | `config.py::validate_config`; `instance.py::generate_instance`; `model.py::build_model`; `financial_model.py::build_fixed_period_financial_model`; `results.py::extract_results`; `docs/model.md`; scenario parity later in `stochastic/model.py::build_saa_model` |
| Preserved | First 12 months fixed from `A_base`; existing 3-period moving-average/slack acquisition dynamics; multi-service index `s`; acquisition remains one new sale in same service/period; optimizer chooses below bounds. |
| Modified | Add optional YAML block for formula-based logarithmic ceiling, auto-calibrated from the consensual year-1 plan and target stock multiplier. Preprocess total monthly marginal ceiling for `t >= 13`; add upper-bound constraint on total acquisition: `sum_s A[s,t] <= ceiling[t] * (1 + slack)`. Keep explicit ceiling list only as secondary override for edge cases. |
| Output connections | EV/DCF and multiples read lower or equal revenue/EBITDA through unchanged `optimized_results.csv`; DD/calibration reads acquisition, growth, solver status; report pages 19/21/23 and `mapvalue.json` read acquisition/revenue; stochastic SAA must mirror ceiling to avoid optimistic stochastic plans. |
| Main audit note | Cap must constrain total acquisition across all commercial channels once channel variables exist. Before Phase 2, `A[s,t]` already means total acquisition, so Phase 1 can bind directly to `A`. |

### 2. Advertising channel

| Item | Audit |
|---|---|
| Files/functions involved | `config.py`; `instance.py`; `model.py`; `financial_model.py`; `results.py`; `reporting.py`; `standard_report/tables.py::build_cac_table`; `standard_report/charts.py::_plot_cac_components`; `calibration/checks.py`; `due_diligence/rules.py`; compatibility mirror later in `stochastic/model.py` and `stochastic/evaluate.py`; new ADR under `docs/adr/` planned. |
| Preserved | Salesforce CAC formulas when no channel block is configured; flat operational cost logic (`Cost_op = max(c_u Q, c_min m_op)`); channel activation flags exogenous from YAML; no activation decision variable; no economies of scale. |
| Modified | Split acquisition by channel while keeping `A[s,t]` as total acquisition. Add continuous advertising investment/acquisition variables with a native linear recta: `A_ad[t] = a + b * I_ad[t]`, bounded by the advertising saturation cap. Add advertising CAC component as `advertising_cac_cost[t] = I_ad[t]`. |
| Output connections | EV changes through CAC and total acquisition; DD consumes CAC, funding gap, runway, LTV/CAC; report CAC table/chart needs component columns; stochastic SAA/MC must either mirror channel mechanics or explicitly declare deterministic-only support until parity. |
| Main audit note | Current salesforce capacity constraint applies to total `A`. Advertising-only business models require channel split so salesforce capacity binds only salesforce acquisition, not advertising acquisition. |

### 3. CAC aggregation and traceability

| Item | Audit |
|---|---|
| Files/functions involved | `model.py::build_model`; `financial_model.py::build_fixed_period_financial_model`; `results.py::extract_results`; `reporting.py::write_core_csv_outputs`; `unit_economics.py::calculate_unit_economics`; `standard_report/tables.py::build_cac_table`, `build_unit_economics_table`; `standard_report/charts.py::_plot_cac_components`; `standard_report/package.py::_build_summary`; `standard_report/sensitivity.py`; `calibration/checks.py::check_ltv_cac`; `docs/report-blueprint.md` page 23. |
| Preserved | Existing `CAC` column remains as backward-compatible alias for total acquisition cost; Spanish business labels remain; `valuation.calculate_dcf` keeps reading `CAC`. |
| Modified | Add MILP cost components: `salesforce_cac_cost[t]`, `advertising_cac_cost[t]`, `third_party_cost[t]`, `total_acquisition_cost[t]`. Add post-solve output columns: `new_customers[t]`, `period_cac_per_user[t]`, `cumulative_cac_per_user[t]`. Guard divide-by-zero with `NaN`/`None` in `results.py`. |
| Output connections | DCF/EV reads `CAC` alias; DD/calibration use CAC and LTV/CAC; report CAC chart/table consume component columns; standard report data package and sensitivity keep raw CSV compatibility; stochastic output schema should use same component names where available. |
| Main audit note | Only CAC cost components enter the MILP. All CAC ratios are post-solve arithmetic in `results.py`; ratios must not be MILP variables. |

### 4. Working-capital cash floor

| Item | Audit |
|---|---|
| Files/functions involved | `config.py::validate_config`; `instance.py::generate_instance`; `model.py::build_model`; `results.py::extract_results`, `summarize_results`; `reporting.py`; `standard_report/consistency.py::check_consistency`; `calibration/checks.py::check_cash_floor`; `due_diligence/rules.py::compute_liquidity_diagnostic`, `_rule_runway`, `_rule_funding_gap`; compatibility in `stochastic/model.py::_liquidity_floor`, `evaluate.py::_liquidity_floor` and cash initialization. |
| Preserved | Deterministic cash equation: `Caja[1] = VC + EBITDA[1]`; `Caja[t] = Caja[t-1] + EBITDA[t]`; cash variable may be negative. |
| Modified | Add a hard ticket-indexed working-capital floor to the main deterministic MILP: `Caja[t] >= -VC` for all periods. If the main model is infeasible, run a secondary diagnostic solve with elastic shortfall only to quantify the financing gap and first breach month. Do not relax the main model and keep the main objective as pure discounted EBITDA. |
| Output connections | Main objective remains pure discounted EBITDA maximization; DCF remains EV/DCF output, not Equity Value. Feasible runs continue normal flow. Infeasible runs route secondary diagnostic financing-gap amount to DD and reports. Report pages 27/28 show cash/funding gap. Stochastic funding-gap fields must be reconciled in future parity work. |
| Main audit note | `liquidity_policy.type: none/nonnegative/minimum_cash` exists now. New policy must be backward-compatible but business target is a hard working-capital floor indexed to the financing ticket (`-VC`). Base regression remains unchanged if `min(Caja) >= -VC`. |

### 5. Unit economics and LTV/CAC consistency

| Item | Audit |
|---|---|
| Files/functions involved | `unit_economics.py::calculate_unit_economics`; `results.py::extract_results`; `valuation.py::calculate_dcf`; `calibration/checks.py::check_ltv_cac`; `standard_report/tables.py::build_unit_economics_table`; `standard_report/package.py::_read_unit_economics`; `docs/calibration-blueprint.md`; `docs/report-blueprint.md` pages 23, 33, 41, 46. |
| Preserved | Business-facing `unit_economics.csv`; C08 calibration alert; DCF remains Enterprise Value output; no Equity Value module. |
| Modified | Annualize all unit-economics metrics; stop arithmetic average ticket/frequency across services; calculate service-line unit gross margin and LTV per service, then sum service lines; use annual churn with annual numerator; preserve high LTV/CAC as documented alert, not silent correction. |
| Output connections | DD/calibration C08 reads `LTV/CAC`; report pages 23/33/41/46 read unit economics; sensitivity may include LTV/CAC reference; EV remains from DCF/multiples, not unit economics. |
| Main audit note | Current unit economics conflict with confirmed rules; Phase 5 is required, not optional cleanup. |

## B) Staged plan

### Phase 1 — Logarithmic acquisition ceiling with slack

#### Scope

- Add formula mode as the primary/recommended config path:

```yaml
acquisition_ceiling:
  enabled: true
  mode: formula
  slack: 0.15
  target_stock_multiplier: 2.0   # e.g., 2x clients by year 3
  preserve_year_1: true
```

- Keep `mode: explicit` as a secondary/override option for edge cases, not the default path.
- Formula preprocessing in `instance.py`:

```text
S_0 = sum(A_base[s, 1..12])
S_target = S_0 * target_stock_multiplier
H_post = months in years 2+3
K = (S_target - S_0) / ln(1 + H_post)

S(t) = S_0 + K * ln(1 + (t - 12))     for t >= 13
ceiling[t] = S(t) - S(t-1)             for t >= 13
```

- `ceiling[t]` is the marginal per-period acquisition ceiling, monotonically decreasing by construction.
- `preserve_year_1: true` means first 12 months remain immutable from `A_base`; ceiling applies from year 2.
- `model.build_model` adds the total ceiling constraint for `t >= 13`:

```text
sum_s A[s,t] <= ceiling[t] * (1 + slack)
```

- Keep existing smoothing constraints. Log ceiling is an additional upper bound, not a replacement.
- Add optional result columns for audit: `Log_ceiling_total`, `Log_ceiling_total_with_slack`, and optionally service allocation diagnostics if explicit/service-level override is used.

#### Invariants to preserve

- Year 1 immutable from `A_base`.
- Existing three-period moving-average/slack dynamics remain active.
- `A[s,t]` remains service-level acquisition; `sum_s A[s,t]` remains total acquisition.
- No channel activation decisions introduced.
- DCF, multiples, and report APIs keep working with existing CSV columns.

#### Minimum modular change

1. `config.py`: validate ceiling block only when enabled; `mode: formula` requires `target_stock_multiplier > 1`, `slack >= 0`, and `preserve_year_1: true` for this phase.
2. `instance.py`: build formula-derived total `log_ceiling[t]` dict for `t >= 13`; support explicit override as secondary path.
3. `model.py`: add total-acquisition upper-bound family.
4. `results.py`: expose ceiling diagnostics only if available.
5. `docs/model.md`: document formula and constraint.

#### New tests

- `validate_config` accepts valid `mode: formula` block and rejects `target_stock_multiplier <= 1`, negative slack, or unsupported mode.
- Formula preprocessing produces monotonically decreasing `ceiling[t]` for `t >= 13`.
- Cumulative formula reaches `S_target` by end of the calibrated post-year-1 window within tolerance.
- Year 1 acquisition remains exactly `A_base`.
- Low formula-derived ceiling binds total acquisition while optimizer can choose below ceiling.
- With ceiling disabled, baseline metrics match current regression tolerance.
- Multi-service configs obey total ceiling: `sum_s A[s,t] <= ceiling[t]*(1+slack)`.
- Explicit list mode is tested only as override/edge-case path.
- Stochastic parity test placeholder: SAA plan cannot exceed deterministic ceiling once stochastic parity work starts.

#### Regression tests that must stay green

- `tests/test_phase1.py`
- `tests/test_phase2.py`
- `tests/test_phase3.py`
- `tests/test_phase4.py`
- `tests/test_consistency.py`
- `tests/test_multi_config_smoke.py`

---

### Phase 2 — Advertising bounded-efficiency channel as a continuous linear recta

#### Scope

- Introduce channel split while preserving downstream total acquisition:

```text
sum_s A[s,t] = sum_s A_salesforce[s,t] + A_ad[t] + A_third_party[t]
```

- Keep `A[s,t]` as total acquisition used by cohorts, revenue, recurrence, log ceiling, and existing outputs.
- Channel activation flags are YAML parameters, never decision variables.
- Salesforce capacity binds only salesforce acquisition.
- Advertising acquisition can support advertising-only configs with `salesforce.active: false`.
- Add advertising config, off by default. All parameters below are instance-specific judgments from the mandante. No hardcoded defaults should exist in code.

```yaml
channels:
  salesforce:
    active: true
    min_share: 0.0
    max_share: 1.0
  advertising:
    active: false
    min_share: 0.0
    max_share: 0.4
    I_min: null       # USD, from instance YAML
    I_max: null       # USD, from instance YAML
    A_min: null       # customers at I_min, from instance YAML
    A_max: null       # customers at I_max, from instance YAML
    A_ad_cap: []      # saturation cap per period; length H or scalar expansion
  third_party:
    active: false
    min_share: 0.0
    max_share: 0.3
```

- Validator requirements:
  - For every active channel, `0 <= min_share <= max_share <= 1`.
  - Sum of `max_share` across active channels must be `>= 1.0`, otherwise the mix is infeasible by construction.
  - Inactive channel implies `min_share = max_share = 0` operationally.
  - When advertising is active: `A_max > A_min`.
  - When advertising is active: `I_max > I_min`.
  - When advertising is active: implied slope `b = (A_max - A_min) / (I_max - I_min)` is positive.
  - When advertising is active: `A_ad_cap[t] >= 0` for all modeled periods.
- Create/update ADR in implementation phase: `docs/adr/0006-advertising-efficiency-semantics.md`.
  - State there is one formulation: continuous linear advertising recta.
  - Do not include alternative-formulation language; this recta is the only planned formulation.
  - State more investment produces more customers (`b > 0`).
  - State implied USD/customer improves with more investment (volume discount) by business assumption.
  - State activation is exogenous from YAML; no channel activation variable.

#### Linear modeling path

Advertising is natively linear and uses only continuous variables for the advertising channel.

Given YAML parameters:

```text
I_min, I_max    : investment range (USD)
A_min, A_max    : customers acquirable at min/max investment
A_ad_cap[t]     : saturation cap per period
```

Preprocess scalar coefficients:

```text
b = (A_max - A_min) / (I_max - I_min)
a = A_min - b * I_min
```

MILP variables, all continuous:

```text
I_ad[t]   advertising investment
A_ad[t]   advertising-acquired customers
```

Constraints when advertising is active:

```text
I_min <= I_ad[t] <= I_max
A_ad[t] = a + b * I_ad[t]
A_ad[t] <= A_ad_cap[t]
advertising_cac_cost[t] = I_ad[t]
```

Constraints when advertising is inactive:

```text
I_ad[t] = 0
A_ad[t] = 0
advertising_cac_cost[t] = 0
```

Total acquisition remains bounded by Phase 1 logarithmic ceiling across all channels:

```text
A_total[t] = sum_s A[s,t]
A_sf[t] + A_ad[t] + A_tp[t] = A_total[t]
A_total[t] <= log_ceiling_total[t] * (1 + slack)
```

Optional channel mix bounds from YAML constrain the implicitly optimized mix without introducing proportion decision variables:

```text
A_channel[t] >= min_share_channel * A_total[t]   for each active channel
A_channel[t] <= max_share_channel * A_total[t]   for each active channel
```

Usage modes:

- Fixed mix: `min_share == max_share` (mandante fixes proportion).
- Optimized with bands: `min_share < max_share` (model chooses within bounds).
- Inactive channel: `active: false` implies channel acquisition and share are zero.

Effective channel proportions are post-solve diagnostics in `results.py`, not MILP decision variables. This avoids bilinear products entirely.

If advertising allocation by service is required, `A_ad_total[t]` should be allocated through service-level continuous variables whose sum equals `A_ad[t]`; the period-level advertising cap and channel-share bounds still apply to total advertising acquisition.

#### Invariants to preserve

- Flat operational unit cost logic unchanged.
- Existing salesforce-only configs produce same `A`, `CAC`, `EBITDA`, `Caja` when channel block absent.
- Third-party channel, where implemented/configured, remains exogenous quota/commission, not a decision variable.
- Advertising activation flag not optimized.
- Advertising channel uses only continuous variables.
- Channel mix is constrained only through linear min/max share bands; effective proportions are post-solve diagnostics, not decision variables.

#### Minimum modular change

1. Mechanical refactor first: introduce channel variables but set legacy mode to `salesforce = A`, advertising/third-party = 0.
2. Add advertising recta coefficient preprocessing in `instance.py`.
3. Add continuous advertising constraints/costs in `model.py`.
4. Add fixed-period channel cost logic in `financial_model.py`.
5. Add outputs in `results.py`.
6. Add ADR and update `docs/model.md`.

#### New tests

- Legacy config without `channels` matches current regression metrics.
- Advertising-only config solves with `salesforce.active=false`, `Vendedores=0`, `Lideres=0`, positive ad acquisition allowed.
- `A_ad[t] <= A_ad_cap[t]` always.
- Total `A[s,t]` obeys log ceiling across salesforce + advertising + third-party.
- Validator rejects `A_max <= A_min`, `I_max <= I_min`, or non-positive slope.
- Validator rejects active-channel `max_share` sums below `1.0`.
- Active advertising equation holds: `A_ad[t] = a + b * I_ad[t]`.
- Inactive advertising sets `I_ad[t] = 0`, `A_ad[t] = 0`, `advertising_cac_cost[t] = 0`.
- Share-band constraints hold for every active channel.
- Fixed-mix mode (`min_share == max_share`) fixes channel proportion within tolerance.
- Band mode (`min_share < max_share`) lets optimizer choose effective mix within bounds.
- Advertising variables in the built PuLP model are continuous; effective proportions are only post-solve diagnostics.

#### Regression tests that must stay green

- All Phase 1 regressions.
- `tests/test_stochastic.py` stays green or has explicit deterministic-channel parity test added before stochastic parity merge.
- `tests/test_phase5b.py` and `tests/test_phase5c.py` stay green after CAC chart/table updates.

---

### Phase 3 — Per-channel + aggregated CAC outputs

#### Scope

- Add only cost components to the MILP:

```text
salesforce_cac_cost[t]       # MILP, from existing salesforce salary/commission formulas
advertising_cac_cost[t]      # MILP, equals I_ad[t]
third_party_cost[t]          # MILP, from third-party commission/quota logic
total_acquisition_cost[t]    # MILP, equals sum of active-channel costs
```

- Keep `CAC[t]` variable/column as backward-compatible alias of `total_acquisition_cost[t]`.
- Keep all CAC ratios strictly post-solve arithmetic in `results.py`, not MILP variables:

```text
new_customers[t]
period_cac_per_user[t]
cumulative_cac_per_user[t]
any CAC ratio
```

- Guard divide-by-zero in `results.py`:
  - `new_customers[t] == 0` -> `period_cac_per_user[t] = NaN`/`None`.
  - cumulative denominator zero -> `cumulative_cac_per_user[t] = NaN`/`None`.
- Update fixed-period financial model and optimized results consistently.
- Update standard report CAC table/chart to prefer component columns when present and fall back to legacy decomposition.

#### Invariants to preserve

- DCF reads `CAC` and remains compatible.
- Unit economics reads total CAC but can optionally expose component CACs.
- Spanish output labels may remain, but English API keys avoid `adquisition`.
- No ratio enters MILP.

#### Minimum modular change

1. `model.py`: define only component CAC cost vars and total alias.
2. `results.py`: extract component columns and calculate all ratios post-solve.
3. `financial_model.py`: same component/ratio output for months 1-12.
4. `reporting.py`: write unchanged CSV filenames.
5. `standard_report/tables.py` and `charts.py`: consume components.
6. `unit_economics.py`: read `total_acquisition_cost` if available, else `CAC`.

#### New tests

- Component sum identity: `salesforce_cac_cost + advertising_cac_cost + third_party_cost == total_acquisition_cost == CAC`.
- `period_cac_per_user` and `cumulative_cac_per_user` return `NaN`, not exception, with zero acquisition.
- Existing `optimized_results.csv` columns still include `CAC`, `Adq_clientes`, `Ingresos`, `EBITDA`, `Caja`.
- CAC report chart/table includes advertising and third-party components when nonzero.
- Fixed-period `fixed_cashflow.csv` exposes same component columns.

#### Regression tests that must stay green

- `tests/test_phase3.py`
- `tests/test_phase4.py`
- `tests/test_phase5a.py` through `tests/test_phase5d.py`
- `tests/test_calibration.py::test_cash_floor_failure_triggers_fail` until Phase 4 intentionally updates cash-floor semantics.

---

### Phase 4 — Working-capital cash floor (hard, ticket-indexed) + secondary DD financing-gap diagnostic

#### Scope

- Add liquidity policy:

```yaml
liquidity_policy:
  type: working_capital_floor
  floor_mode: financing_ticket_multiple
  floor_multiple: -1.0          # floor = -1.0 * VC
```

- Main deterministic MILP uses a hard constraint and keeps the objective clean:

```text
maximize sum_t descuento[t] * EBITDA[t]

Caja[1] = VC + EBITDA[1]
Caja[t] = Caja[t-1] + EBITDA[t]
Caja[t] >= -VC                  ∀t ∈ T
```

- If main solve is feasible:
  - Continue normal pipeline flow.
  - Output `working_capital_floor[t]`, `floor_slack[t]`, `floor_hit[t]`.
- If main solve is infeasible:
  1. Do not relax the main model.
  2. Do not add elastic shortfall to the main model.
  3. Run a secondary diagnostic solve whose only purpose is measuring the financing gap.
  4. Secondary diagnostic adds non-negative `cash_shortfall[t]` variables only to quantify:
     - amount needed beyond the VC ticket,
     - first breach month,
     - maximum breach month.
  5. Route DD alert:
     `Plan requires additional financing of $X beyond the VC ticket, first breach in month Y.`
  6. Main pipeline does not crash: feasible → normal flow; infeasible → DD captures gap and reports it.
- Diagnostic output on infeasible main solve:
  - `diagnostic_cash_shortfall[t]`
  - `diagnostic_financing_gap[t]`
  - summary fields: `max_financing_gap`, `max_financing_gap_month`, `first_floor_breach_month`
- Due Diligence hook:
  - Update liquidity diagnostic to use configured floor, not hard zero.
  - Main-model infeasibility from cash floor becomes DD financing-gap alert and recommendation.
- Calibration hook:
  - `C04_cash_floor` evaluates against policy floor on feasible runs.
  - Keep legacy `minimum_cash` config support.
- Stochastic compatibility:
  - Do not change stochastic dominance analysis.
  - Keep deterministic/stochastic cash-initialization divergence flagged as known issue in the compatibility contract.

#### Invariants to preserve

- Cash may be negative.
- Cash is not constrained to `>= 0` unless explicitly configured.
- Main solver may return `Infeasible`; secondary diagnostic solve measures financing gap so the pipeline can report it instead of breaking.
- DCF remains Enterprise Value; no Equity Value module.
- Base config should remain regression-stable if its minimum cash is above `-VC`.
- Explicit assumption: `Caja_final == VC + sum(EBITDA)` holds because the model considers only operational flows. If future extensions add CapEx, debt service, or other non-operational cash flows, this identity must be updated accordingly.

#### Minimum modular change

1. `config.py`: validate new liquidity policy.
2. `instance.py`: preprocess floor per period.
3. `model.py`: add hard floor constraints to main model and add a separate diagnostic model/solve path used only after main infeasibility.
4. `results.py`: extract floor/slack columns on feasible runs and diagnostic gap columns on infeasible diagnostic runs.
5. `pipeline.py` / DD handoff: preserve normal flow on feasible run; on infeasible run route diagnostic gap to DD instead of crashing.
6. `due_diligence/rules.py`: update liquidity diagnostic.
7. `calibration/checks.py`: update C04 threshold source.
8. `standard_report/consistency.py`: add cash/floor identity check for feasible runs.

#### New tests

- Cash equation identity holds: `Caja_final == VC + Σ EBITDA`.
- Floor default computes `-VC` when configured as `floor_multiple: -1.0`.
- Feasible config satisfies `Caja[t] >= -VC` for every period.
- Tiny-VC stress config returns main solver `Infeasible`, then secondary diagnostic returns finite `max_financing_gap` and `first_floor_breach_month`.
- Main model objective contains only discounted EBITDA, with no financing-gap term.
- DD liquidity diagnostic reports `max_financing_gap` and the alert text when main model is infeasible due to cash floor.
- C04 uses working-capital floor, not hard zero.
- Stochastic cash-initialization divergence remains flagged as known issue, not silently changed in this plan.

#### Regression tests that must stay green

- `tests/test_due_diligence.py::test_negative_cash_does_not_block`
- `tests/test_due_diligence.py::test_full_workflow_on_base_config`
- `tests/test_consistency.py`
- `tests/test_stochastic.py`
- `tests/test_multi_config_smoke.py`

---

### Phase 5 — Unit-economics / LTV-CAC consistency pass

#### Scope

- Rework `calculate_unit_economics` so all unit-economics metrics are annual.
- Stop averaging ticket/frequency across services.
- Use service-line sums:

```text
annual_purchase_count_s = 12 / frecuencia_s
unit_gross_margin_s = ticket_s - c_u_s
annual_unit_gross_profit_s = unit_gross_margin_s * annual_purchase_count_s * alpha_s
ltv_s = annual_unit_gross_profit_s / annual_churn_s
LTV_total = sum_s ltv_s
CAC = total_acquisition_cost / total_new_customers
LTV/CAC = LTV_total / CAC
```

- Keep C08 calibration alert if LTV/CAC exceeds configured sane bound.
- Do not silently correct or suppress high ratio; surface as report/calibration artifact.
- Keep DCF valuation at Enterprise Value. Do not add Equity Value.
- Preserve `unit_economics.csv` contract where possible; add `Base temporal = anual` or equivalent column if useful for audit.

#### Invariants to preserve

- Business-facing Spanish labels remain acceptable.
- `unit_economics.csv` still contains rows consumed by report and sensitivity.
- C08 stays in `calibration/checks.py`.
- DCF/multiples not replaced by unit economics.
- Multi-service lines are distinct and summed.

#### Minimum modular change

1. `unit_economics.py`: annual service-line calculation.
2. `standard_report/tables.py`: render annual unit-economics values.
3. `standard_report/sensitivity.py`: read LTV/CAC unchanged.
4. `calibration/checks.py`: keep C08 threshold and message.
5. `docs/calibration-blueprint.md` and `docs/model.md`: update formulas.

#### New tests

- Two-service fixture proves no arithmetic average ticket is used.
- LTV uses annual numerator and annual churn.
- `LTV_total == sum(ltv_s)` for service lines.
- High LTV/CAC fixture triggers C08 warning, not silent correction.
- Unit economics output remains nonempty and report renders.
- No Equity Value fields are introduced.

#### Regression tests that must stay green

- `tests/test_phase3.py` updated for new annual values.
- `tests/test_calibration.py::test_disabled_check_is_skipped`
- `tests/test_phase5b.py` sensitivity LTV/CAC reference.
- `tests/test_template_formulas.py`

## C) Grill-with-docs protocol per phase

Use same workflow for each phase.

1. Read current docs and tests.
2. State invariants before coding.
3. Run green baseline.
4. Implement only phase scope.
5. Add phase tests plus one feasibility/consistency check.
6. Run full suite.
7. Run demo-complex end-to-end.
8. Write `docs/STAGE_X.md` handoff.
9. Independent read-only re-audit before merge.

### Phase-specific protocol details

| Phase | Docs/tests to read first | Invariants to state | Feasibility/consistency check | Demo command |
|---|---|---|---|---|
| 1 | `CONTEXT.md`, `docs/model.md`, `docs/regression.md`, `tests/test_phase1.py`, `tests/test_phase2.py` | Year 1 fixed; smoothing preserved; formula ceiling is upper bound only; cap applies to total acquisition. | Formula ceiling lowers/equal EV and never violates `sum_s A[s,t] <= ceiling[t]*(1+slack)`. | `uv run adventure-capital all --config configs/demo-complex.yaml --output outputs/demo-complex-stage-1 --document reports/valuation-ev.template.yaml --schema reports/schema/valuation-ev.schema.yaml` |
| 2 | Phase 1 handoff, `docs/adr/0001-operational-cost-floor.md`, planned ADR 0006, `tests/test_phase2.py`, `tests/test_stochastic.py` | Activation flags exogenous; salesforce legacy preserved; ad-only supported; advertising recta continuous; slope positive; share bands linear; effective proportions post-solve only. | Advertising-only model solves without salesforce capacity; share-band constraints hold; no log-cap breach. | Same command with `stage-2` output. |
| 3 | `docs/report-blueprint.md` page 23, `docs/phase-5-plan.md`, `tests/test_phase5b.py`, `tests/test_phase5c.py` | `CAC` alias preserved; component sum identity; ratios postprocessed only. | `CAC == component sum` and zero acquisition gives NaN ratio. | Same command with `stage-3` output. |
| 4 | `docs/DUE_DILIGENCE.md`, `docs/adr/0005-due-diligence-umbrella.md`, `docs/STOCHASTIC_EXTENSION.md`, `tests/test_due_diligence.py`, `tests/test_stochastic.py`, `tests/test_consistency.py` | Cash starts with VC; cash may be negative down to `-VC`; main model floor is hard; secondary diagnostic measures gap only after infeasibility; DD alert not structural by itself. | Feasible case satisfies floor; infeasible stress case produces diagnostic gap and first breach month. | Same command with `stage-4` output. |
| 5 | `docs/calibration-blueprint.md`, `docs/report-blueprint.md` pages 23/33/41/46, `tests/test_phase3.py`, `tests/test_calibration.py`, `tests/test_phase5b.py` | Annual metrics only; service lines summed; C08 preserved; EV not Equity Value. | Two-service trap proves no average ticket; high LTV/CAC surfaces C08. | Same command with `stage-5` output. |

Each `docs/STAGE_X.md` handoff must include:

- Scope implemented.
- Files changed.
- Invariants checked.
- Test commands and results.
- Demo output path.
- Open risks/debt.
- Read-only re-audit checklist.

## D) Risks and tests

| Phase | Feasibility risk | EV inflation risk | Downstream desync risk | Test that catches it |
|---|---|---|---|---|
| 1 | Formula ceiling accidentally applied to year 1 and conflicts with fixed `A_base`. | Formula cap treated as fixed trajectory or replaces smoothing, allowing aggressive paths elsewhere. | Stochastic SAA ignores cap and reports optimistic plan. | Year-1 immutable test; disabled-ceiling regression; `sum_s A[s,t] <= ceiling[t]*(1+slack)` assertion; formula monotonicity test; stochastic parity test. |
| 2 | Advertising-only still constrained by salesforce capacity, or active-channel `max_share` sum below 1.0 creates avoidable infeasibility. | Validator allows invalid recta (`b <= 0`), advertising investment cost is omitted, or share constraints are implemented as proportions with bilinear terms. | Report CAC chart still decomposes only salesforce and mislabels ad spend or effective channel mix. | Advertising-only solve test; positive-slope validator test; `sum(max_share_active) >= 1.0` validator; `advertising_cac_cost == I_ad` identity; share-band assertion; component CAC chart/table test. |
| 3 | Component variables not tied to total CAC, EBITDA identity breaks. | Missing active-channel cost undercounts CAC and inflates EBITDA/EV. | Unit economics/report read old `CAC` while components differ. | Component sum identity; EBITDA definition consistency; DCF reads `CAC == total_acquisition_cost`. |
| 4 | Hard floor makes main model infeasible and pipeline treats it as crash instead of routing secondary diagnostic gap to DD. | Secondary diagnostic accidentally feeds back into main objective or relaxes the main hard floor, allowing underfunded EV. | DD/C04 still use zero floor, causing false failures; stochastic cash/funding gap inconsistent. | Feasible floor test; infeasible stress + diagnostic-gap test; objective-clean test; C04 floor-source test; stochastic divergence warning check. |
| 5 | Annualization mistakes divide by monthly churn or zero churn incorrectly. | Averaging high-ticket services inflates LTV/CAC and EV narrative. | C08/report/sensitivity expect old row names and break. | Two-service no-average test; annual churn test; C08 high-ratio warning; report render smoke. |

## Post-correction verification

- Phase order remains `1 → 2 → 3 → 4 → 5`; no new dependency changes the sequence.
- Phase 1 still owns formula-derived total acquisition cap before channel split.
- Phase 2 still depends on Phase 1 because total acquisition across channels must remain under the logarithmic ceiling.
- Phase 2 share-band constraints use existing channel acquisition variables; no proportion variables or bilinear terms are introduced.
- Phase 3 still follows Phase 2 because CAC traceability depends on channel cost components.
- Phase 4 still follows CAC phases; hard floor affects feasibility and DD but not channel mechanics.
- Phase 5 still follows output stabilization; unit economics consumes final acquisition/CAC outputs.
- Phase invariants have been updated for formula ceiling, continuous advertising recta, linear share bands, and hard cash floor.
- Risk table has been updated for corrected formula ceiling, advertising/channel-share, and cash-floor formulations.
- Grill-with-docs protocol remains unchanged except phase-specific invariants/checks reflecting corrected formulas.
- No code implementation is included in this correction.

## Compatibility contract for all phases

- Preserve existing core CSV filenames.
- Preserve existing columns: `CAC`, `Adq_clientes`, `Ingresos`, `EBITDA`, `Caja`, service-prefixed `A_`, `C_`, `R_`, `Q_`, `I_`, `Cost_op_`.
- New columns are additive unless a phase explicitly updates tests/docs.
- `CAC` remains total acquisition cost alias.
- `A[s,t]` remains total acquisition by service-period.
- Business-facing Spanish labels preserved where already used.
- No report narrative/PDF/UI changes.
- No Equity Value module.
- Stochastic SAA/Monte Carlo must either mirror deterministic constraints/costs or explicitly fail parity tests until updated; no silent drift.
- **WARNING — known stochastic divergence:** deterministic model initializes cash as `VC + EBITDA[1]`. Stochastic model (`stochastic/evaluate.py`) initializes cash as `0.0`. This divergence is a known issue flagged for future stochastic parity work. It is out of scope for this plan but must not be forgotten.

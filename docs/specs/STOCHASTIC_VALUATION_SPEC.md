# Stochastic Valuation Specification — Adventure Capital

**Date:** 2026-05-29. Evidence: ✅VC code · 📄VD docs · 🔍INF · ❓UNC.

---

## 1. Current status (precise terminology — do not overclaim)

The repository implements **two distinct stochastic mechanisms**, both real:

| Layer | Module | What it is | Status |
|---|---|---|---|
| **Phase A** | `stochastic/model.py` | **Two-stage Sample-Average-Approximation (SAA) stochastic optimization.** One first-stage plan `(A,V,L)` shared across scenarios; per-scenario recourse; objective = expected discounted EBITDA + linear terminal proxy. | ✅VC Implemented |
| **Phase B** | `stochastic/evaluate.py` | **Monte Carlo robustness evaluation** of the Phase-A plan over a larger sample; closed-form recourse, no re-solve. | ✅VC Implemented |

**Correct names to use:**
- Phase A **is stochastic optimization** (expected-value / risk-neutral, two-stage SAA). ✅VC / 📄VD ADR 0004.
- Phase B **is Monte Carlo evaluation** of a fixed plan. ✅VC
- Together: *"two-stage SAA stochastic optimization with ex-post Monte Carlo robustness evaluation."*

**What it is NOT:**
- ❌ Not "just sensitivity analysis" (sensitivity = the deterministic `sensitivity_*.csv` ±10% sweeps in `standard_report/sensitivity.py`). ✅VC
- ❌ Not "Monte Carlo on a deterministic plan only" — ADR 0004 explicitly **rejected** that and built the uncertainty-aware optimizer. 📄VD
- ❌ Not robust/worst-case, not chance-constrained, not CVaR (all documented as future). 📄VD

❓UNC: a real run (`outputs/dd-base`) reported `n_scenarios=50`; code defaults are Phase-A 100 / Phase-B 1000. Confirm the counts actually used.

---

## 2. Minimum-viable Monte Carlo design for Monday

**Use what exists.** No new code needed. The `run` command already executes Phase A → Phase B and writes `stochastic_summary.csv`. For the demo:

1. Solve deterministic plan (baseline). ✅VC
2. (Phase A) Solve SAA stochastic optimization → robust plan. ✅VC
3. (Phase B) Evaluate that plan over N scenarios. ✅VC
4. Report the distribution (below).

If timing is a problem, **lower the scenario count** in a `stochastic` config block (Phase-A `scenario_count`, Phase-B `evaluation.n_scenarios`) — no code change, config only. 🔍INF

---

## 3. Scenario generation logic ✅VC

- **SAA mode (default):** each uncertain multiplier drawn from a bounded **triangular** distribution, fixed seed, equal probability `1/N`.
- **Explicit mode:** named scenarios (`base`, `commercial_downside`, `retention_stress`, `funding_stress`, `upside`) with explicit multipliers + probabilities.

### Parameters varied ✅VC
| Uncertainty | Applied to | Default triangular (min, mode, max) |
|---|---|---|
| Churn / retention | each service `churn_anual` ×, clipped [0,1] | (0.8, 1.0, 1.3) |
| Commercial productivity | `meta` × | (0.5, 1.0, 1.2) |
| Available financing | `VC` × | (0.7, 1.0, 1.3) |
| Discount rate / WACC | `beta` absolute, ×base, truncated [0.05, 0.90] | (0.6β, β, 1.5β) |

---

## 4. Outputs to aggregate & percentiles ✅VC (`stochastic/results.py`)

Per-scenario row (`stochastic_scenarios.csv`): `VAN, total_ebitda, final_cash, funding_gap, gap_positive, breakeven_month` + scenario multipliers + `wacc`.

Summary (`stochastic_summary.csv`):
- `expected_van` (probability-weighted)
- `van_p10, van_p50, van_p90, van_min, van_max, van_std`
- `prob_van_negative`
- `prob_funding_gap, expected_funding_gap, max_funding_gap`
- `breakeven_month_p50, prob_no_breakeven`

Real example (`outputs/dd-base/stochastic_summary.csv`) ✅VC: expected VAN ≈ 1.61M; p10/p50/p90 ≈ 1.32M/1.64M/1.92M; P(VAN<0)=0; P(funding gap)=1.0; median breakeven month 23.

**Note:** the brief asks for P5/P25/P75/P95; code emits **P10/P50/P90**. 🔍INF Extending to P5/P25/P75/P95 is a one-line change in `summarize_distribution` (future, low-risk).

---

## 5. Risk metrics & downside reading

- **Downside value:** `van_p10`, `van_min`, `P(VAN<0)`. ✅VC
- **Liquidity fragility:** `prob_funding_gap`, `expected_funding_gap`, `max_funding_gap`. ✅VC (P(gap)=1.0 in the base case means *every* scenario dips below the floor at some month — a clear talking point: the plan needs a cash buffer).
- **Execution risk:** `breakeven_month_p50`, `prob_no_breakeven`. ✅VC
- **Fragility drivers:** read multipliers in `stochastic_scenarios.csv` against `VAN` (which uncertainty most lowers value). 🔍INF (no automated driver-ranking yet → future).

---

## 6. Future path to true stochastic optimization

(Full formulation in `MATHEMATICAL_FORMULATION.md` §2C.) Increments, each isolated:
1. **CVaR objective** — aux var + per-scenario excess vars; risk-adjusted blend.
2. **Cash-survival chance constraint** `P(Caja_t ≥ floor) ≥ a` — big-M binaries (expensive).
3. **Investment-thesis chance constraint** `P(ARR$_yr3 ≥ target) ≥ b` — needs ARR-$ accounting first.
4. **After-tax DCF in the objective** — linearize the tax `max`.
5. **Emergency financing recourse** with penalty cost.

State clearly in the defense: today = expected-value SAA + MC robustness; risk-adjusted/chance-constrained = future work.

# Robust Strategy & Diagnostic Design

**Project framing.** This document specifies the methodological design of the
*stochastic* and *diagnostic* layers of Adventure Capital. The system is a
**computational formalization of the A. Maureira Value Map** for **Enterprise
Value (EV) estimation and robust strategy assessment**. It is *not* a full
qualitative or commercial due-diligence engine: the qualitative judgment (team,
market, product, competitive moat, legal/commercial diligence) remains a human
responsibility and is **out of scope**. What this system formalizes is the
quantitative skeleton of the Value Map: the deterministic growth-plan model, the
post-model financial reading, the robustness study under uncertainty, and the
investment-interpretation layer that sits on top of those numbers.

The word "diagnostic" here always means **quantitative diagnostic over model
inputs and model outputs** — never a verdict on the commercial merit of the
venture.

> Terminology in this document follows `CONTEXT.md` (the ubiquitous language) and
> the current code: **Deterministic Model**, **Stochastic Model**, **Scenario**,
> **First-Stage Decision**, **Recourse Decision**, **Funding Gap**, **Valuation
> Mode**. `EV` (Enterprise Value) is the business-facing name for the DCF result
> the code computes as `VAN` (`calculate_dcf` → `dcf["VAN"]`, and the per-scenario
> `VAN` produced by `stochastic/evaluate.py`).

---

## 1. The full intended pipeline

```
input form / YAML
      │
      ▼
┌─────────────────────────┐
│ PRE-MODEL DIAGNOSTIC     │  quantitative precheck on the raw instance
│ (DD pre-rules)           │  → structural validity, unit margin, financing, churn bounds
└─────────────────────────┘
      │  (structural failure short-circuits here → rejected_for_valuation)
      ▼
┌─────────────────────────┐
│ DETERMINISTIC MODEL      │  single-scenario MILP growth-plan optimization
│ (run_pipeline,           │  → x_det (acquisition A, sellers V, leaders L),
│  baseline_only=True)     │     monthly results, base EV (DCF VAN), unit economics
└─────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│ POST-MODEL DIAGNOSTIC    │  Value-Map reading over deterministic outputs
│ (Calibration evidence    │  → breakeven, EBITDA regime, revenue growth, runway,
│  + DD synthesis +        │     funding-gap severity, LTV/CAC, margin, cash floor
│  liquidity diagnostic)   │  → aggregated DIAGNOSTIC STATE + Valuation Mode
└─────────────────────────┘
      │  (state decides whether the robustness study runs and how to read it)
      ▼
┌─────────────────────────┐
│ SAA STOCHASTIC OPTIM.    │  Phase A — optimize ONE first-stage plan across a
│ (build/solve_saa_model)  │  scenario sample → x_saa, expected objective
└─────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│ MONTE CARLO EVALUATION   │  Phase B — evaluate each candidate plan (x_det, x_saa,
│ (evaluate_strategy over  │  optional alternatives) over a LARGE common scenario
│  generate_evaluation_…)  │  sample, closed-form recourse, no re-solve
└─────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│ ROBUST STRATEGY          │  compare plans on the common scenarios via the
│ SELECTION                │  robust-dominance criterion + robust score
└─────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│ REPORT  or  DIAGNOSTIC   │  Standard Valuation Report (decision-ready) OR a
│ MEMO                     │  diagnostic memo (not investment-ready), per state
└─────────────────────────┘
```

Mapping to current code:

| Stage | Code entry point |
|---|---|
| Pre-model diagnostic | `due_diligence.rules.evaluate_pre_rules` |
| Deterministic model | `pipeline.run_pipeline(..., baseline_only=True)` |
| Post-model diagnostic | `calibration.run_calibration` + `evaluate_synthesis_rules` + `compute_liquidity_diagnostic` → `build_verdict` |
| SAA optimization (Phase A) | `stochastic.model.build_saa_model` / `solve_saa_model` |
| Monte Carlo evaluation (Phase B) | `stochastic.evaluate.evaluate_strategy` over `generate_evaluation_scenarios` |
| Distribution summary | `stochastic.results.summarize_distribution` |
| Orchestration | `due_diligence.workflow.run_assessment` |
| Report | `standard_report.*` |

---

## 2. Four distinct layers (what is and is NOT being claimed)

The design deliberately separates four conceptual layers so that no numeric
output is ever mistaken for a commercial verdict.

| Layer | In scope? | What it answers | What it must NOT claim |
|---|---|---|---|
| **A. Qualitative / commercial due diligence** | **Out of scope** | Is the team/market/product/legal case sound? | The system never asserts this. Reports must state the EV is conditional on qualitative diligence done elsewhere. |
| **B. Quantitative precheck** (pre-model) | In scope | Can this instance be modeled at all? Are inputs structurally coherent? | Not a judgment on attractiveness; only computability/feasibility. |
| **C. Post-model Value Map diagnostic** | In scope | Given the deterministic plan, does the case show a credible venture-scale financial regime (growth, breakeven, margins, liquidity)? | Not "this is a good investment"; it is a structured reading of model outputs against Value-Map thresholds. |
| **D. Investment / robustness interpretation** | In scope (quantitative only) | How robust is value/strategy under uncertainty? What EV range and downside should anchor negotiation? | Not a recommendation to invest; it frames numbers for a human decision. |

The Value Map is formalized as layers **B + C + D**. Layer **A** stays human.

---

## 3. Diagnostic states

The refined design uses **four** diagnostic states. They consolidate the current
five-verdict implementation (`due_diligence/report.py`) without losing
information — the two "adjustment" verdicts collapse into a single
`recalibration_required` state distinguished by an `adjustment_level` field.

| Refined state | Meaning | Current code verdict it maps to |
|---|---|---|
| `pass` | Inputs computable; outputs show a credible venture-scale regime; no material warnings. | `passed` |
| `pass_with_warnings` | Acceptable, but non-blocking warnings present (e.g. high-but-tolerable churn, moderate funding gap). | `passed_with_warnings` |
| `recalibration_required` | Case is modelable but not yet decision-ready: fixable business/liquidity risk (`minor`) or not-yet-venture-eligible (`major`). Carries `adjustment_level ∈ {minor, major}`. | `requires_minor_adjustment` + `requires_major_adjustment` |
| `rejected_for_valuation` | Structural infeasibility: the instance cannot be modeled or valued. | `rejected_for_stochastic` |

**Severity → state precedence** (worst-failing wins, mirrors
`aggregate_verdict`):

```
structural  → rejected_for_valuation
major       → recalibration_required (adjustment_level = major)
minor       → recalibration_required (adjustment_level = minor)
warning     → pass_with_warnings
ok          → pass
```

> Design rule (unchanged from ADR 0005): **only `structural` blocks valuation.**
> Business/financial risk — negative cash, funding gap, weak LTV/CAC, late
> breakeven, negative EV — is *diagnostic*. It shapes the state, the Valuation
> Mode, and recalibration recommendations, but it never blocks the robustness
> study, because the entire point is to study a plan's robustness *under* that
> risk.

---

## 4. Per-state behavior

For each state: does the pipeline continue, what artifact is produced, is a
valuation report allowed, and what is requested from the user.

| State | Pipeline continues? | Artifact | Valuation report allowed? | Requested from user |
|---|---|---|---|---|
| `pass` | Yes → SAA + Monte Carlo run. | **Standard Valuation Report** (Valuation Mode `final`). | **Yes — decision-ready.** | Nothing required; optional sensitivity assumptions. |
| `pass_with_warnings` | Yes → SAA + Monte Carlo run. | **Standard Valuation Report** with a warnings annex (Valuation Mode `final`, flagged). | **Yes — final, with caveats surfaced.** | Acknowledge warnings; optionally supply data to retire them (e.g. real churn). |
| `recalibration_required` | Yes → robustness study runs in **diagnostic/warning** mode. | **Diagnostic memo** (Valuation Mode `warning` if `minor`, `diagnostic` if `major`). Not a final report. | **No final report.** Preliminary/diagnostic valuation only, clearly labeled "not investment-ready". | The specific recalibrations from `adjustment_recommendations` (e.g. raise `VC`, fix pricing/costs, revisit acquisition/recurrence to reach venture-scale growth). Then **re-run**. |
| `rejected_for_valuation` | **No** — model run short-circuits (`_has_structural`). | **Rejection memo** listing `blocking_reasons`. | **No.** | The essential corrections (valid config, positive unit margin, `VC > 0`, churn in [0,1]). Re-submit the instance. |

Notes:
- A report/memo is **always written**, even on rejection (`write_due_diligence_report`).
- The robustness study inherits the state's **Valuation Mode**
  (`final` / `warning` / `diagnostic` / `none`), which is stamped onto every
  stochastic output so a reader always knows how to interpret it.

---

## 5. Robust strategy comparison methodology

The robustness study compares **candidate first-stage plans** on a **common**
Monte Carlo scenario sample. A first-stage plan is the committed decision shared
across all scenarios: acquisition `A`, sellers `V`, leaders `L` (a
**First-Stage Decision**). Per-scenario operational capacity and all financials
are **Recourse Decisions** computed closed-form per scenario (no re-solve).

**Candidate plans**

| Plan | Source | Meaning |
|---|---|---|
| `x_det` | Deterministic MILP (`solve_growth_plan`) | Optimal under point estimates; the ex-ante baseline. May be fragile to uncertainty. |
| `x_saa` | SAA model (`solve_saa_model`) | Optimal in expectation across the Phase-A scenario sample; the robust candidate. |
| `x_alt_i` (optional) | Manual / stress-shaped plans | Conservative, aggressive, or capital-constrained variants for comparison. |

**Common Monte Carlo evaluation scenarios.** All candidates are evaluated on the
**same** large ex-post sample (`generate_evaluation_scenarios`, default
`n_scenarios = 1000`, fixed seed) so differences reflect the plans, not sampling
noise. Each scenario draws churn, commercial productivity, available financing,
and WACC from configurable triangular distributions (`stochastic/scenarios.py`).
Distributions are **modeling assumptions, not empirically calibrated truth** —
state this in reports.

**Per-plan metrics** (computed from the per-scenario distribution returned by
`evaluate_strategy`, summarized by `summarize_distribution`):

| Metric | Definition | Source field |
|---|---|---|
| Expected EV | Probability-weighted mean EV | `expected_van` |
| P10 EV | 10th percentile EV (downside) | `van_p10` |
| P50 EV | Median EV | `van_p50` |
| P90 EV | 90th percentile EV (upside) | `van_p90` |
| P(EV < 0) | Probability of negative EV | `prob_van_negative` |
| P(funding gap) | Probability of breaching the liquidity floor | `prob_funding_gap` |
| Expected gap | Probability-weighted Funding Gap | `expected_funding_gap` |
| Breakeven month | Median month cumulative EBITDA ≥ 0 (with P(no breakeven)) | `breakeven_month_p50`, `prob_no_breakeven` |

The full per-scenario distribution is always written out
(`stochastic_scenarios.csv`); percentiles are summary statistics, not a
replacement for it.

---

## 6. Robust dominance criterion & robust score

**Robust dominance (partial order).** Plan `A` *robustly dominates* plan `B` iff
it is at least as good on every robustness axis and strictly better on at least
one:

```
A ⪰ B  ⟺   expected_EV(A) ≥ expected_EV(B)        (central value)
       and  P10_EV(A)      ≥ P10_EV(B)             (downside protection)
       and  P(EV<0)(A)     ≤ P(EV<0)(B)            (loss probability)
       and  P(gap)(A)      ≤ P(gap)(B)             (liquidity risk)
       and  expected_gap(A)≤ expected_gap(B)       (financing need)
A ≻ B  ⟺   A ⪰ B  and strict on ≥ 1 axis.
```

If one plan robustly dominates all others, **select it** — no weighting needed.

**Robust score (total order, for the non-dominated set).** When plans are
incomparable under the partial order, rank by a transparent weighted score over
**normalized** metrics (min-max across the compared plans, so each term ∈ [0,1];
risk terms inverted so higher is always better):

```
RobustScore(x) =  w1 · z(expected_EV)
               +  w2 · z(P10_EV)              # downside-weighted
               +  w3 · (1 − z(P(EV<0)))
               +  w4 · (1 − z(P(gap)))
               +  w5 · (1 − z(expected_gap))
               −  w6 · z(P(no_breakeven))

default weights (downside-averse): w = (0.25, 0.30, 0.20, 0.10, 0.10, 0.05)
```

- Weights are **configurable** and **reported alongside the score** — the score
  is a decision aid, never a hidden black box.
- The **downside emphasis** (`w2` on P10, penalties on loss/gap) encodes that for
  early-stage venture EV, surviving the bad scenarios matters more than maximizing
  the mean.
- Tie-break order: higher P10 EV → lower P(funding gap) → earlier breakeven.

**Selection rule.** Prefer the robust-dominant plan; if none, take the highest
RobustScore; if `x_det` and `x_saa` are within a configurable tolerance, prefer
`x_saa` (robust by construction) and note the deterministic plan's fragility.

---

## 7. Robust valuation reporting

The valuation is reported as a **range anchored on the distribution**, never a
single point, with an explicit negotiation reading.

| Reported figure | Definition | Source |
|---|---|---|
| **Base EV** | Deterministic point-estimate EV from `x_det` | `dcf["VAN"]` |
| **Expected stochastic EV** | Probability-weighted mean EV of the selected plan | `expected_van` |
| **Downside EV** | P10 EV of the selected plan (conservative anchor) | `van_p10` |
| **Valuation range** | [P10, P90] with P50 as central, Base EV shown for reference | `van_p10` / `van_p50` / `van_p90` |
| **Negotiation interpretation** | Narrative tying the range to a stance | derived |

**Negotiation reading (template).**
- **Floor / walk-away anchor:** Downside EV (P10) — value that survives adverse
  churn/productivity/financing scenarios.
- **Central / fair anchor:** Expected stochastic EV ≈ P50 — the reference point.
- **Upside / ask anchor:** P90 — justifiable only under favorable execution.
- **Base vs. expected gap:** if Base EV ≫ Expected EV, the deterministic plan is
  *optimistic/fragile*; lead with the stochastic range. If Base EV ≈ Expected EV,
  the case is robust and the point estimate is trustworthy.
- **Risk caveats:** always cite P(EV<0) and P(funding gap) next to the range, and
  stamp the **Valuation Mode** (`final` / `warning` / `diagnostic`).

The report must state that the EV is **conditional on the out-of-scope
qualitative diligence** (Section 2, Layer A).

---

## 8. Stochastic unit economics reporting

Unit economics are reported as **distributions across the Monte Carlo sample**,
not single deterministic values, so the reader sees the spread driven by churn,
productivity, and financing uncertainty. Each is derived per scenario, then
summarized (mean, P10/P50/P90, and a tail probability where relevant). The
deterministic baseline (`unit_economics.calculate_unit_economics`) supplies the
formulas; the stochastic layer re-evaluates them per scenario.

| Metric | What to report | Risk reading |
|---|---|---|
| **CAC distribution** | Cost of acquisition per client across scenarios; mean + P10/P50/P90 | Sensitivity of CAC to commercial productivity (downside productivity → higher CAC). |
| **LTV distribution** | Lifetime value per client across scenarios | Sensitivity to churn — the dominant driver. |
| **LTV/CAC distribution** | Efficiency ratio across scenarios; report **P(LTV/CAC < 1)** and **P(< 3)** | Venture viability threshold; tail probability below 1 is a red flag. |
| **Gross margin distribution** | `1 − operational_cost / revenue` across scenarios | Margin compression under low-productivity / high-cost scenarios. |
| **Churn / recurrence risk** | Distribution of effective annual churn and recurrence (repurchase) outcomes; P(no breakeven) | Retention is the highest-leverage parameter; tie to `prob_no_breakeven`. |

Report rule: present each as **central value + range**, and flag the
**probability of crossing a critical threshold** (LTV/CAC < 1, gross margin < 0,
breakeven beyond horizon). State that distributions reflect configured modeling
assumptions, not calibrated empirical data.

---

## 9. Future deterministic-model extension: acquisition-mix optimization

The current Deterministic Model treats acquisition through generic sellers `V`
and leaders `L`. The planned extension makes **commercial channels** explicit and
lets the model **optimize the acquisition mix** across them. This is a roadmap
section — design intent, not yet implemented.

**New index.** Commercial channel `k ∈ K` (e.g. direct sales force, paid
marketing, third-party / B2B2C partners).

**Per-channel structure.**

| Element | Description | Modeling note |
|---|---|---|
| **Sales force** | Headcount/effort per channel and period; productivity = acquisitions per seller | Extends current `V` / `L` to be channel-indexed with channel-specific productivity. |
| **Publicity / marketing spend** | Continuous spend per channel/period with **diminishing returns** | Concave acquisition response `f_k(spend)` (e.g. log/saturating). Requires piecewise-linear or concave handling to stay MILP-tractable. |
| **Third-party / B2B2C channel** | Partner-driven acquisition; revenue-share / margin haircut | Channel-specific take rate reduces effective ticket or adds per-acquisition cost. |
| **Channel-specific CAC** | Each channel has its own CAC = (fixed effort + variable spend + commissions) / acquisitions | Replaces the single blended CAC in `evaluate.py`. |
| **Channel productivity** | Max acquisitions per unit of effort/spend per channel | Capacity-style upper bounds per channel/period. |

**New decision.** Allocate acquisition across channels to **maximize EV subject
to budget, capacity, and diminishing-returns constraints** — i.e. choose the
acquisition mix `{A_{s,k,t}}`, sales-force levels, and marketing spend per
channel, not just a single aggregate acquisition path.

**Interaction with the stochastic layer.** Channel productivity and CAC become
additional **uncertain parameters** (per-channel `productivity_multiplier`), so
the robustness study can compare **channel-mix strategies** under uncertainty —
e.g. a marketing-heavy mix vs. a partner-led mix — using the same robust-dominance
criterion (Section 6).

---

## 10. MVP static rule set (~20 rules)

A static rule set covering ~80% of cases. Each rule carries: **status**
(pass / warn / fail), **severity** (structural / major / minor / warning),
**interpretation**, **recommendation**, and a **block/continue** decision.
Only `structural` blocks. Rules `R01–R09` already exist in
`due_diligence/rules.py`; the rest are calibration-sourced or planned synthesis
rules consumed via `map_calibration_findings`.

| # | Rule | Layer | Status logic | Severity | Block? | Interpretation | Recommendation |
|---|---|---|---|---|---|---|---|
| R01 | Instance valid (`validate_config`) | pre | fail if config invalid | structural | **Block** | Instance not modelable | Complete/fix essential inputs |
| R02 | Unit margin positive (`ticket > c_u`) | pre | fail if any service ticket ≤ unit cost | structural | **Block** | Unit economics not computable | Raise `ticket` or lower `c_u` |
| R03 | Financing present (`VC > 0`) | pre | fail if `VC ≤ 0` | structural | **Block** | No working capital to execute | Define `VC > 0` |
| R04 | Churn bounds (`churn_anual ∈ [0,1]`) | pre | fail if out of range | structural | **Block** | Invalid churn parameter | Express churn as fraction in [0,1] |
| R05 | Churn severity | pre/synth | warn ≥ 0.6, major ≥ 0.95 | major/warning | Continue | Retention incompatible with scale | Revisit retention/recurrence |
| R06 | Breakeven within horizon | synth | warn if > month 24; major if never | major/warning | Continue | No credible EBITDA regime | Extend `H`, improve margin, cut fixed cost |
| R07 | Runway / cash-negative month | synth | minor if cash<0 ≤ month 6, else warning | minor/warning | Continue | Working-capital pressure (diagnostic) | Raise `VC`, defer hires, smooth acquisition |
| R08 | Funding-gap severity | synth | warn ≥ 0.5×VC, minor ≥ 5×VC | minor/warning | Continue | Financing shortfall magnitude | Secure bridge financing / restructure spend |
| R09 | EBITDA regime by year 3 | synth | fail if annual EBITDA ≤ 0 at year 3 | major | Continue | No profitability regime | Revisit pricing/cost/acquisition speed |
| R10 | Revenue growth multiple | synth | major if last/first year < 1.5× | major | Continue | SME profile, not venture-scale | Revisit acquisition/recurrence assumptions |
| R11 | Solver status optimal | calib | fail if not optimal/feasible | structural | **Block** | Plan not reliably optimized | Inspect infeasibility / relax constraints |
| R12 | EV (VAN) computable | calib | fail if EV not computable | structural | **Block** | Valuation undefined | Fix DCF inputs (WACC, residual method) |
| R13 | EV (VAN) positive | calib | warn/minor if EV ≤ 0 | minor/warning | Continue | Negative base value | Improve plan economics; study stochastic range |
| R14 | LTV/CAC ≥ 3 | calib | warn below 3, minor below 1 | minor/warning | Continue | Acquisition capital efficiency | Lower CAC or raise LTV (retention/price) |
| R15 | Gross margin floor | calib | warn if below target margin | warning | Continue | Thin operational margin | Revisit `c_u` / pricing / capacity steps |
| R16 | Cash-floor / liquidity policy respected | calib | warn if floor breached | warning/minor | Continue | Liquidity-policy violation (diagnostic) | Adjust liquidity policy or financing |
| R17 | Retention / recurrence plausibility | calib | warn if recurrence implausible | warning | Continue | Recurrence assumptions optimistic | Validate `frecuencia` / repurchase rate |
| R18 | Residual-value method consistency | pre/calib | fail if method set but params missing | structural | **Block** | Terminal value mis-specified | Provide `ebitda_multiple` or `gordon_g` |
| R19 | Horizon sufficiency (`H` covers year 3) | synth | warn if horizon too short to judge regime | warning | Continue | Cannot assess maturity | Extend planning horizon `H` |
| R20 | Scenario distributions sane | stoch | warn if distributions degenerate/missing | warning | Continue | Robustness study weakly informative | Configure `stochastic.distributions` |

**Coverage claim.** These ~20 rules are the **MVP** intended to catch the common
80% of cases (structural input errors, non-viable unit economics, missing
financing, no venture-scale regime, liquidity pressure, optimistic retention).
They are a **quantitative diagnostic over the Value Map**, not a substitute for
qualitative commercial due diligence (Section 2, Layer A). Edge cases and
domain-specific judgments remain human.

---

## Cross-references

- `CONTEXT.md` — ubiquitous language (Scenario, First/Recourse Decision, Funding
  Gap, Valuation Mode, Deterministic/Stochastic Model).
- `docs/adr/0004-two-stage-stochastic-extension.md` — Phase A/B stochastic design.
- `docs/adr/0005-due-diligence-umbrella.md` — DD-as-umbrella, Calibration-as-evidence,
  structural-only blocking. This document's four states refine that ADR's five
  verdicts (consolidating the two adjustment verdicts into `recalibration_required`
  + `adjustment_level`).
- `src/adventure_capital/due_diligence/` — rules, workflow, verdict.
- `src/adventure_capital/stochastic/` — scenarios, SAA model, evaluation, results.

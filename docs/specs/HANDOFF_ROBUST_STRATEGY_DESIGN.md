# Handoff — Robust Strategy & Diagnostic Design

**Date:** 2026-05-31
**Repo:** `/Users/apena/gits/adventure-capital` (branch `main`)
**Status:** ✅ Deliverable complete — `ROBUST_STRATEGY_AND_DIAGNOSTIC_DESIGN.md` written at repo root.

## What was asked
Refine the methodological design of the **stochastic** and **diagnostic** layers
and produce a design document (`ROBUST_STRATEGY_AND_DIAGNOSTIC_DESIGN.md`)
covering 10 specified topics. Constraint: **do not edit code** (documentation
only). Frame the project as a **computational formalization of the A. Maureira
Value Map** for Enterprise Value estimation + robust strategy assessment, and
**do not claim full qualitative due diligence**.

## What was delivered
`ROBUST_STRATEGY_AND_DIAGNOSTIC_DESIGN.md` — all 10 requested sections:
1. Full pipeline (form/YAML → pre-model diagnostic → deterministic model →
   post-model diagnostic → SAA → Monte Carlo → robust selection → report/memo),
   with a code-mapping table.
2. Four-layer distinction (qualitative DD out of scope; quantitative precheck;
   post-model Value Map diagnostic; investment/robustness interpretation).
3. Four diagnostic states: `pass`, `pass_with_warnings`, `recalibration_required`,
   `rejected_for_valuation`.
4. Per-state table: continue?, artifact, report allowed?, info requested.
5. Robust comparison methodology (`x_det`, `x_saa`, optional alternatives, common
   MC scenarios, the 8 metrics).
6. Robust dominance criterion (partial order) + robust score (weighted, normalized).
7. Robust valuation reporting (base / expected / downside EV, range, negotiation).
8. Stochastic unit economics (CAC, LTV, LTV/CAC, gross margin, churn/recurrence).
9. Future deterministic extension (channels `k`, sales force, marketing with
   diminishing returns, B2B2C, channel CAC/productivity, mix optimization).
10. MVP ~20 static rules table (status, severity, interpretation, recommendation,
    block/continue).

A second file, this handoff, was also created.

## Key design decisions (so a reviewer can sanity-check intent)
- **States consolidated, not renamed blindly.** The code today has FIVE verdicts
  in `src/adventure_capital/due_diligence/report.py`:
  `passed`, `passed_with_warnings`, `requires_minor_adjustment`,
  `requires_major_adjustment`, `rejected_for_stochastic`.
  The doc's FOUR states map them by collapsing the two "adjustment" verdicts into
  `recalibration_required` carrying an `adjustment_level ∈ {minor, major}`.
  Mapping: `pass`←passed; `pass_with_warnings`←passed_with_warnings;
  `recalibration_required`←requires_minor+requires_major;
  `rejected_for_valuation`←rejected_for_stochastic.
- **"EV" = the code's `VAN`.** Enterprise Value is the business-facing name for
  the DCF `VAN` (`calculate_dcf` → `dcf["VAN"]`; per-scenario `VAN` in
  `stochastic/evaluate.py`). The doc states this equivalence explicitly.
- **Structural-only blocking** is preserved from ADR 0005: financial/liquidity
  risk is diagnostic and never blocks the robustness study.
- **Metrics are grounded in real fields** from
  `stochastic/results.py::summarize_distribution`: `expected_van`, `van_p10/p50/p90`,
  `prob_van_negative`, `prob_funding_gap`, `expected_funding_gap`,
  `breakeven_month_p50`, `prob_no_breakeven`.
- Section 9 (channels) and parts of Section 10 (R10–R20) are **roadmap/intended
  design**, not all implemented yet. R01–R09 exist in `due_diligence/rules.py`.

## Files read to ground the document
- `CONTEXT.md` (ubiquitous language)
- `docs/adr/0005-due-diligence-umbrella.md`, referenced `0004`
- `src/adventure_capital/pipeline.py`
- `src/adventure_capital/due_diligence/{rules,workflow,report}.py`
- `src/adventure_capital/stochastic/{scenarios,evaluate,results}.py`
- `src/adventure_capital/unit_economics.py`

## Suggested next steps (for the next agent or for Alon)
1. **Review the state mapping** — confirm collapsing the two adjustment verdicts
   into `recalibration_required` is desired, or keep five states. If the four-state
   model is adopted, a future code change to `due_diligence/report.py` would be
   needed (NOT done — this task was docs-only).
2. **Decide whether to write an ADR** (e.g. `0006-four-state-diagnostic-and-robust-selection.md`)
   to formally supersede the verdict naming in ADR 0005, since the doc refines it.
3. **Implement robust selection** — the robust-dominance criterion and robust
   score (Section 6) are specified but not yet coded; today the workflow evaluates
   only `x_saa` (`workflow._run_stochastic`). Multi-plan comparison (`x_det` vs
   `x_saa` vs alternatives over the common sample) is a real code gap.
4. **Stochastic unit economics (Section 8)** are specified but not computed today;
   `unit_economics.py` is deterministic only. Per-scenario re-evaluation is a TODO.
5. **Confirm rule weights / thresholds** in Sections 6 and 10 with the domain
   owner (A. Maureira Value Map) before implementing.

## Constraints honored
- ✅ No code edited (documentation only).
- ✅ Framed as computational formalization of the A. Maureira Value Map.
- ✅ Does not claim full qualitative due diligence (explicit Layer A = out of scope).

## Nothing committed
The two new `.md` files are untracked working-tree changes. Commit/push was not
requested. `git status` will show:
`ROBUST_STRATEGY_AND_DIAGNOSTIC_DESIGN.md`, `HANDOFF_ROBUST_STRATEGY_DESIGN.md`.

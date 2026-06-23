# Due Diligence is the umbrella assessment layer; Calibration is an evidence source

The Due Diligence workflow owns the final assessment, verdict, and report for a startup instance. It wraps the deterministic baseline (`run_pipeline`), applies its own rules over both the raw instance and the deterministic outputs, and **consumes the existing Calibration checks as one evidence source** rather than treating Calibration as a separate business phase. This reverses the earlier framing (ADR 0004 / CONTEXT.md) where Due Diligence and Calibration were peer layers: Calibration is now subordinated under Due Diligence in the methodology, though it remains a standalone technical module in the code.

## Status

accepted (refines the Due Diligence framing in ADR 0004)

## Decision detail

- **DD is iterative, not a hard gate.** It runs an assess → recommend → rerun loop: the consultant adjusts the instance per the recommendations and re-runs until the case is acceptable.
- **DD owns the verdict.** One of `passed`, `passed_with_warnings`, `requires_minor_adjustment`, `requires_major_adjustment`, `rejected_for_stochastic`, plus decision fields (`allows_stochastic`, `valuation_mode`, `adjustment_level`, `blocking_reasons`, `adjustment_recommendations`, `rerun_recommended`). `requires_major_adjustment` means the case is not yet venture-scale eligible. A report is always produced, even on failure.
- **Valuation mode tags the stochastic run.** `final` (decision-ready), `warning` (preliminary, minor adjustment), `diagnostic` (not investment-ready, major adjustment), `none` (rejected). The robustness study runs whenever not structurally rejected; the mode records how to read it.
- **Blocking is structural only.** Only structural-feasibility failures map to `critical_blocking` → `rejected_for_stochastic` (model infeasible, missing essential inputs, impossible unit economics, non-computable valuation, missing financing, corrupted outputs). Business/investment risk (weak LTV/CAC, high churn, low margin, negative NPV/EBITDA, late breakeven, low runway, high funding gap) is `critical_non_blocking` → `requires_adjustment` or warning, never an automatic block.
- **Canonical M4 requires DD eligibility.** The original prototype allowed stochastic for every verdict except `rejected_for_stochastic`. After ADR 0009, canonical channel-parity CVaR M4 runs only for `passed`, `passed_with_warnings`, and `requires_minor_adjustment`. `requires_major_adjustment` now blocks canonical M4 until YAML recalibration because the case is not yet venture-scale eligible and M4 is the final stochastic PCA, not a cheap diagnostic.
- **No duplicated logic.** DD implements only new raw-instance pre-rules and a few synthesis rules (breakeven-within-horizon, runway, funding-gap severity). All post-model financial checks (NPV, LTV/CAC, margin, cash floor, EBITDA, retention, solver status) come from Calibration's `CheckResult`s, mapped into the DD taxonomy. There must not be two sources of truth for those metrics.
- **Calibration severity mapping.** Calibration `C01` failure / model infeasibility → blocking; other Calibration errors → non-blocking by default; Calibration warnings → warning; pass → pass.

## Considered options

- **Umbrella DD consuming Calibration (chosen).** Reuses the working pipeline and Calibration, avoids inconsistency, preserves the deterministic flow.
- **DD reimplements all rules independently (rejected).** Creates duplicate thresholds and a second source of truth that would drift from Calibration.
- **DD as a pure pre-model gate, Calibration peer (superseded).** The original ADR 0004 framing; dropped because the user wants a single assessment workflow that wraps the model and reuses post-model evidence.

## Consequences

- DD must run after the deterministic baseline (it needs the outputs Calibration reads), so it is not a purely pre-model gate.
- Calibration stays untouched and independently runnable today; a future refactor may migrate its rules into a unified DD registry, but not now.
- The stochastic valuation is blocked only by `rejected_for_stochastic`; DD is the gate that decides, and it gates on structural feasibility, not financial attractiveness.

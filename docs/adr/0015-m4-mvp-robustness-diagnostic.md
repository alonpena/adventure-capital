# 0015 — M4 MVP is a robustness diagnostic, not the official growth plan

Status: Accepted  
Date: 2026-07-06

## Context

Adventure Capital already implements a canonical M4 stochastic layer: LHS scenario generation, SAA solve, ex-post evaluation, and stochastic artifacts (`stochastic_summary.csv`, `stochastic_diagnostics.json`, `stochastic_scenarios.csv`, `saa_solution.json`). ADR 0009 and ADR 0011 define the technical trajectory: a two-stage stochastic model with a mean-CVaR objective.

During thesis-stage closure, the core growth methodology was reframed as target-driven deterministic planning:

- the investment thesis fixes the growth commitment (`investment_thesis.multiple`, default ×3 from month 12 to month 36);
- the deterministic MILP finds the resource-efficient plan to reach that commitment;
- VAN and MoM are consequences, not direct calibration targets.

Using the SAA-selected strategy as the official demo plan would reopen a separate explanation burden: why the plan is selected by mean-CVaR instead of the deterministic target-driven objective, why expected VAN differs from the deterministic VAN, and how to interpret recourse. Full stochastic planning also requires a more complete recourse model and stronger parity guarantees.

## Decision

For the thesis MVP and demo stage:

1. The **official growth plan and valuation** are the deterministic target-driven outputs:
   - `optimized_results.csv`
   - `valuation_summary.json`
   - DCF outputs
   - unit economics
   - deterministic due diligence
2. M4 stochastic outputs are an **official robustness artifact**, not the source of the official plan.
3. `report.html` must include the deterministic plan and valuation as the main result, plus an ex-post robustness section with the VAN distribution across scenarios (`E[VAN]`, percentiles/CVaR, `P(VAN<0)`, funding gap, and growth-target hit probability when available).
4. The SAA stochastic optimization output (`saa_solution.json` and in-sample SAA objective metrics) is a separate technical artifact. It may be exposed in the UI/artifacts view, but it is not the business-facing official plan in the thesis MVP.
5. The UI and report wording must present M4 as:
   - robustness analysis;
   - ex-post uncertainty stress over the deterministic plan;
   - first approach to stochastic optimization;
   - not a replacement for the deterministic plan in the thesis MVP.
6. Existing M4 code remains in place. No refactor to risk-neutral `E[VAN]` or ex-post-only simulation is required before the demo.
7. The limitation is explicit: full stochastic decision support requires calibrated recourse and further validation.

Recommended business-facing wording:

> El plan oficial se obtiene con el modelo determinista target-driven. Luego M4 evalúa su robustez bajo incertidumbre mediante escenarios LHS, reportando la distribución de VAN — E[VAN], percentiles, CVaR, probabilidad de VAN negativo — y la brecha de caja. Esta etapa es una primera aproximación a optimización estocástica; no reemplaza el plan determinista en el MVP de tesis. La solución SAA queda como artefacto técnico separado.

## Consequences

### Positive

- Preserves a simple, defensible thesis narrative.
- Keeps Excel/YAML calibration tied to deterministic year-1 and target-driven growth.
- Still exposes stochastic artifacts as official evidence of robustness.
- Avoids last-minute objective refactors.
- UI can safely degrade when M4 is blocked or fails; deterministic artifacts remain valid.

### Negative

- M4 code still solves an SAA mean-CVaR model internally, so artifact captions must avoid implying the SAA strategy is the official operating plan.
- `saa_solution.json` remains a technical artifact; business-facing pages should prioritize ex-post distribution metrics.
- `report.html` must not hide stochastic robustness: the VAN distribution across scenarios is part of the official robustness evidence, but subordinate to the deterministic plan.
- There is a conceptual gap between the implemented stochastic optimizer and the demo framing; this is accepted for MVP and documented.

### Future work

- Add a true ex-post-only robustness mode over the deterministic strategy.
- Compare deterministic strategy vs SAA strategy on a common LHS evaluation sample.
- Calibrate distributions from historical/source data rather than backend defaults.
- Add bounded commercial recourse and document which decisions are first-stage vs recourse.
- Decide whether risk-neutral `E[VAN]`, mean-CVaR, or CVaR is the production stochastic objective.
- Treat `investment_thesis.multiple` as a future stochastic/sensitivity variable (e.g. downside/base/upside thesis multipliers), without turning it into a solver variable in the current MVP.

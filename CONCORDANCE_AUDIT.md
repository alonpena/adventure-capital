# Concordance Audit — Entrega2 vs Entrega3

## Inputs audited

- **Report A:** `/Users/apena/paper/Entrega2_Grupo10.pdf`
- **Report B:** `/Users/apena/paper/Entrega3_Grupo10.pdf`
- Extracted text used for audit:
  - `/tmp/Entrega2_Grupo10.txt`
  - `/tmp/Entrega3_Grupo10.txt`
- Repository cross-checks:
  - `docs/adr/0009-stochastic-channel-parity-cvar.md`
  - `docs/M4_STOCHASTIC_PARITY_PLAN.md`
  - `docs/CLI_WORKFLOW_MVP.md`
  - `docs/benchmark-v0-report.md`
  - `src/adventure_capital/stochastic/*`
  - `src/adventure_capital/workflow_registry.py`
  - `src/adventure_capital/simple_report.py`
  - `outputs/executions/run_20260622-230645_a8cf74ae/*`
  - `outputs/benchmark/*`
  - pytest run in this audit: `137 passed, 3 skipped`

## Executive summary

The two reports are **not mutually consistent as standalone final reports**, but they are broadly explainable as different project states: Report A is an older Entrega 2 snapshot, while Report B is a newer Entrega 3 that incorporates M4 canonical stochastic optimization, CLI workflow, M5 simple HTML, and preliminary benchmark claims.

Report B is generally more aligned with the current codebase for the core base-case pipeline, M4 implementation, CLI, and M5 simple report. However, Report B has several material issues before academic submission:

1. It contains an internal contradiction about empirical validation: the summary/conclusion says real-case validation remains future work, while Section 9 claims a benchmark with four real cases was executed.
2. It still describes a financing/work-capital multiplier as an M4 stochastic uncertainty, but canonical M4 code and ADR 0009 fix `VC` across scenarios and measure funding stress through runway/funding gap.
3. It uses the word “robust” in places where the implemented method is better described as risk-averse SAA with CVaR, not robust/worst-case optimization.
4. Its benchmark KavaComex VAN does not match the currently available `outputs/benchmark/kavacomex/valuation_summary.json` artifact.
5. Its older conceptual Due Diligence text still conflicts with its own later DD gate table.

## Final classification

**PARTIALLY CONSISTENT WITH MATERIAL GAPS**

Reason: the core deterministic base-case values match across reports and artifacts, but the stochastic methodology, M4 gate, report-generation claims, Unit Economics, benchmark validation status, and several quantitative stochastic/benchmark results materially diverge.

## Main inconsistencies

### 1. Due Diligence gate conflict

- Report A: major findings permit stochastic execution in diagnostic mode.
- Report B: Table 7.3 correctly says `requires_major_adjustment` blocks M4, but earlier B text still says major allows diagnostic stochastic execution.
- Code now supports the B table, not the legacy B prose.

**Risk:** High. This affects when M4 can be claimed valid.

### 2. M4 methodology evolved, but wording remains mixed

- Report A describes a previous stochastic layer: expected VAN / Monte Carlo-style robustness.
- Report B describes canonical M4 with SAA + LHS + CVaR, which matches current code.
- But Report B still includes a financing multiplier and robust-optimization wording that conflict with ADR 0009 and code.

**Risk:** High. Methodological claims are central to the thesis.

### 3. Base stochastic numerical results conflict

Report A reports older stochastic numbers:

- Expected VAN: USD 1.51MM
- P10 VAN: USD 1.20MM
- P90 VAN: USD 1.84MM
- Expected funding gap: USD 128.4K
- Max funding gap: USD 136.6K

Report B and current artifacts report:

- Expected VAN: USD 1.543MM
- P5/P10/P50/P90: USD 943K / 1.062MM / 1.538MM / 2.032MM
- CVaR 5%: USD 834K
- Expected funding gap: USD 20.8K
- Max funding gap: USD 41.2K

**Risk:** High. Report A values should be explicitly treated as legacy.

### 4. Unit Economics conflict

- Report A: LTV USD 11,937; LTV/CAC 33.2x.
- Report B/current artifacts: LTV USD 5,360; LTV/CAC 14.93x.

**Risk:** Medium. B is artifact-backed; A is obsolete.

### 5. Empirical validation / benchmark contradiction

- Report A: real-case validation remains future work.
- Report B: Section 9 says four real cases were benchmarked.
- Report B summary/conclusion also says validation with real cases remains future work.

**Risk:** Critical. This can be read as overclaiming or self-contradiction.

Recommended wording: “A preliminary benchmark v0 was run on four extracted historical cases; full empirical validation over the mandante’s portfolio remains future work.”

### 6. Benchmark artifact mismatches

- Entrena: B’s stochastic USD 570K appears to match SAA `saa_solution.expected_van`, not ex-post `stochastic_summary.expected_van` (~USD 761K). Must label clearly.
- Beloop: B’s timeout at 120s is supported by benchmark artifacts, but current M4 default is now 420s; benchmark should be rerun or labeled as pre-fix.
- KavaComex: B says VAN USD -156K; current artifact shows VAN around USD -303K. Needs reconciliation.

**Risk:** High for KavaComex; Medium for Entrena/Beloop.

## Concordance matrix

A machine-readable full matrix with evidence locations and corrections is available in:

- `CONCORDANCE_MATRIX.csv`

Condensed matrix:

| # | Topic / claim | Status | Severity | Recommended correction |
|---:|---|---|---|---|
| 1 | Project problem and operational bottleneck | MATCH | LOW | Keep; no material correction needed. |
| 2 | Overall project objective | MATCH | LOW | Keep B as updated formulation. |
| 3 | System architecture | PARTIAL MATCH | LOW | Explain A as prior version; B as updated state. |
| 4 | Input data source | PARTIAL MATCH | LOW | If both reports remain referenced, note B supersedes A with CLI registry. |
| 5 | Due Diligence gate semantics | CONFLICT | HIGH | Fix B internal inconsistency: remove legacy statement that major allows M4. |
| 6 | Deterministic model channel scope | PARTIAL MATCH | MEDIUM | State A reflects older deterministic model; B supersedes with multichannel refinement. |
| 7 | Operational cost floor | MATCH | LOW | Keep consistent. |
| 8 | DCF and multiples methodology | MATCH | LOW | Keep B wording that multiples are reference only. |
| 9 | Unit economics reported values | CONFLICT | MEDIUM | Use B values/current artifacts. |
| 10 | Stochastic objective | CONFLICT | HIGH | Treat B as current; mark A as prior prototype. |
| 11 | Stochastic sampling | CONFLICT | HIGH | Use B sampling description. |
| 12 | Financing uncertainty in M4 | CONFLICT | HIGH | Remove financing multiplier from B M4 uncertainty list. |
| 13 | Use of term robust | PARTIAL MATCH | MEDIUM | Replace robust optimization wording with risk-averse/CVaR wording. |
| 14 | M5/report generation | CONFLICT | MEDIUM | Use B current state: simple HTML MVP. |
| 15 | CLI workflow | MISSING IN A | LOW | Accept as new in B. |
| 16 | Streamlit UI | MISSING IN A | LOW | Keep B current; do not overclaim production UI. |
| 17 | Base deterministic results | MATCH | LOW | Keep. |
| 18 | Base DCF valuation | MATCH | LOW | Keep. |
| 19 | Base Due Diligence result | PARTIAL MATCH | MEDIUM | Clarify current findings from artifacts. |
| 20 | Base stochastic results | CONFLICT | HIGH | Use B/current artifact values. |
| 21 | Base stochastic conclusion on value/liquidity | PARTIAL MATCH | MEDIUM | Keep liquidity conclusion; avoid robust wording. |
| 22 | Test count | CONFLICT | LOW | Use current 137 passed / 3 skipped. |
| 23 | ADR/documentation count | PARTIAL MATCH | LOW | Update count if mentioned. |
| 24 | Benchmark with real cases | CONFLICT | CRITICAL | Call it preliminary benchmark v0; full validation remains future. |
| 25 | Benchmark GoDemos | MISSING IN A | MEDIUM | Keep B; label benchmark v0. |
| 26 | Benchmark Entrena en Casa | MISSING IN A | MEDIUM | Clarify stochastic value is SAA expected, not ex-post expected. |
| 27 | Benchmark Beloop | MISSING IN A | MEDIUM | Note timeout used old 120s setting; rerun after 420s fix. |
| 28 | Benchmark KavaComex | PARTIAL MATCH | HIGH | Reconcile -156K vs current -303K artifact. |
| 29 | Benchmark KavaComex DD reason | PARTIAL MATCH | MEDIUM | Use exact verdict `requires_major_adjustment`. |
| 30 | Benchmark validation tolerance | MISSING IN A | LOW | Keep B but call preliminary criteria. |
| 31 | Initial clients/model gap | MISSING IN A | MEDIUM | Keep as evidence-backed future schema extension. |
| 32 | Physical/logistics business support | MISSING IN A | MEDIUM | Keep as future work; consider ADR if implementing. |
| 33 | Solver time limit parameter | MISSING IN A | LOW | Keep B current; rerun old timeout benchmarks. |
| 34 | M4 code support/tag | MISSING IN A | LOW | Keep B; ensure tag is available. |
| 35 | Report output evidence | PARTIAL MATCH | MEDIUM | Claim simple HTML unless PDF generated for the exact run. |
| 36 | Conclusions | PARTIAL MATCH | HIGH | Use B as current but fix validation contradiction and robust wording. |

## Evidence-backed corrections

1. **Fix DD gate prose in Report B Section 7.2.** The current code and B Table 7.3 block M4 for `requires_major_adjustment`.
2. **Remove M4 financing multiplier from Report B Section 7.6.** Current code samples churn, salesforce efficiency, advertising efficiency, third-party efficiency, and WACC; `VC` is fixed.
3. **Replace “optimización robusta” with “optimización estocástica aversa al riesgo mediante CVaR”.** Robust/worst-case optimization is not implemented.
4. **Clarify the benchmark as preliminary.** Use “benchmark v0 de cuatro casos extraídos” and say full empirical validation remains pending.
5. **Reconcile KavaComex values.** Current artifact is around VAN USD -303K; B/benchmark report text says USD -156K.
6. **Clarify Entrena stochastic value.** USD 570K appears to be SAA expected VAN (`saa_solution`), not ex-post expected VAN (`stochastic_summary` ≈ USD 761K).
7. **Update report-generation claim.** Current M5 deliverable is simple `report.html`; do not claim polished PDF unless generated and attached.
8. **Use B/current Unit Economics values.** A’s LTV/LTV-CAC values are obsolete.

## Risk assessment for academic submission

- **Critical risk:** validation/benchmark contradiction in Report B. A committee can interpret this as claiming both that validation is future and already done.
- **High risk:** M4 methodology wording. Financing multiplier and robust-optimization language conflict with code/ADR.
- **High risk:** benchmark numerical inconsistency for KavaComex.
- **Medium risk:** Report A and B stochastic results differ materially; if both are submitted without version framing, the evaluator may see unexplained result drift.
- **Medium risk:** PDF/report claims can overstate current M5 if simple HTML is the actual current deliverable.

## Recommended next actions

1. Treat `Entrega2_Grupo10.pdf` as legacy only.
2. Patch `Entrega3_Grupo10.pdf` source (likely `/Users/apena/paper/main.tex` or current paper source) using `REPORT_FIX_PLAN.md`.
3. Rerun or clearly label benchmark outputs after the 420s M4 time-limit fix, especially Beloop.
4. Reconcile KavaComex VAN from the exact artifact used in the report.
5. Regenerate Report B PDF after corrections.
6. Keep `CONCORDANCE_MATRIX.csv` as audit evidence for the correction process.

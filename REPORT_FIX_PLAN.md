# Report Fix Plan — Entrega2 / Entrega3 Concordance

## Scope

Reports audited:

- Report A: `/Users/apena/paper/Entrega2_Grupo10.pdf`
- Report B: `/Users/apena/paper/Entrega3_Grupo10.pdf`

Decision: treat Report A as legacy. Fix Report B/current paper source only.

## Priority P0 — must fix before academic submission

### P0.1 Resolve validation contradiction

**Problem:** Report B says full validation with real cases remains future work, but Section 9 claims four real cases were benchmarked.

**Correction:** Use this framing everywhere:

> Se ejecutó un benchmark preliminar v0 con cuatro casos históricos extraídos desde planillas del mandante. Este benchmark permite identificar brechas de calibración, pero no constituye todavía una validación empírica completa sobre la cartera del mandante.

**Edit locations:**

- Resumen
- Section 8.1 Limitaciones
- Section 9 title/intro
- Conclusions

### P0.2 Fix M4 uncertainty list

**Problem:** Report B states M4 includes a “Multiplicador de Capital de Trabajo y Financiamiento”. Current M4 fixes `VC` and measures liquidity stress via funding gap/runway.

**Correction:** Replace uncertainty list with:

- churn multiplier
- salesforce efficiency multiplier
- advertising efficiency multiplier
- third-party efficiency multiplier
- WACC multiplier

Add:

> El VC se mantiene fijo por escenario; el estrés de liquidez se mide mediante runway y funding gap.

**Edit location:** Section 7.6 M4.

### P0.3 Fix DD gate prose

**Problem:** Report B Section 7.2 says major allows stochastic diagnostic, conflicting with Table 7.3 and code.

**Correction:**

- `requires_major_adjustment` blocks canonical M4.
- `requires_minor_adjustment` allows M4 in warning mode.

**Edit locations:** Section 7.2 and Section 7.5.

### P0.4 Replace robust-optimization wording

**Problem:** Both reports use “robust” loosely. Current method is CVaR risk-averse SAA, not robust/worst-case optimization.

**Correction terms:**

Use:

- “optimización estocástica aversa al riesgo”
- “análisis de cola adversa mediante CVaR”
- “resiliencia bajo escenarios adversos”

Avoid:

- “optimización robusta”
- “simulación robusta”
- “plan robusto” unless explicitly informal and qualified.

**Edit locations:** Resumen, Sections 5, 7.6, 8, 9, Conclusions.

### P0.5 Reconcile KavaComex VAN

**Problem:** Report B says KavaComex VAN USD -156K. Current `outputs/benchmark/kavacomex/valuation_summary.json` shows approximately USD -303K. `docs/benchmark-v0-report.md` also says -156K, so there are stale/versioned benchmark artifacts.

**Correction options:**

1. If -156K came from a specific saved run, cite exact output directory/artifact and commit.
2. Otherwise update table to current artifact value (~USD -303K) and adjust delta vs Excel.

**Edit locations:** Section 9.1 KavaComex and Table 9.2.

## Priority P1 — important consistency improvements

### P1.1 Clarify Entrena stochastic value

**Problem:** Report B table lists “Modelo (Estoc.) USD 570K”. Current artifacts show:

- `saa_solution.expected_van` ≈ USD 570K
- `stochastic_summary.expected_van` ≈ USD 761K

**Correction:** Label the column precisely:

- “SAA expected VAN” if using USD 570K.
- Or update to ex-post LHS expected VAN if using `stochastic_summary.csv`.

### P1.2 Update Beloop benchmark after M4 time-limit fix

**Problem:** Report B says M4 Not Solved due 120s timeout. Current code now has M4 default 420s and CLI override.

**Correction:** Either:

- rerun Beloop with 420s and update outcome; or
- label current result as “benchmark v0 before M4 time-limit fix”.

### P1.3 State Report A as legacy if referenced

**Problem:** Report A values and method are older.

**Correction:** If both PDFs are mentioned, add note:

> Entrega 2 corresponde a una versión previa del sistema; Entrega 3 actualiza la metodología y los resultados tras M4 canónico y CLI/M5.

### P1.4 Update test/doc count

Use current evidence:

```text
137 passed, 3 skipped
```

Do not claim full ruff clean unless baseline is fixed; current truthful wording:

> El linter está limpio en los archivos modificados recientes; el baseline completo conserva advertencias preexistentes.

### P1.5 Confirm report output claim

Claim only:

```text
M5 genera report.html simple en español.
```

Do not claim production-quality PDF unless generated for the exact final run.

## Priority P2 — polish / academic clarity

### P2.1 Add a versioned evidence table

Add a small table near results:

| Evidence | Path |
|---|---|
| Base run artifacts | `outputs/executions/run_20260622-230645_a8cf74ae/` |
| M4 implementation decision | `docs/adr/0009-stochastic-channel-parity-cvar.md` |
| M4 plan | `docs/M4_STOCHASTIC_PARITY_PLAN.md` |
| CLI workflow | `docs/CLI_WORKFLOW_MVP.md` |
| Benchmark report | `docs/benchmark-v0-report.md` |

### P2.2 Clarify preliminary benchmark role

Recommended Section 9 title:

```text
Benchmark preliminar v0 con casos históricos extraídos
```

Avoid:

```text
Validación empírica y benchmark de casos reales
```

unless full validation protocol is actually completed.

### P2.3 Make limitations explicit

Include:

- benchmark v0 is not full validation;
- M4 performance can be slow for mixed-channel/multiservice;
- product/logistics business models require schema extension;
- initial active client pool is missing;
- multiples are not market-calibrated;
- current report is simple HTML, not final consulting-grade design.

## Suggested edit order

1. Fix Section 7.2 / 7.5 DD gate.
2. Fix Section 7.6 M4 methodology: remove financing multiplier, robust wording.
3. Fix Section 9 validation framing.
4. Reconcile benchmark tables (KavaComex, Entrena label, Beloop timeout note).
5. Update Summary and Conclusions last.
6. Regenerate PDF.
7. Rerun concordance spot-check.

## Acceptance criteria

Before final submission, the corrected Report B should satisfy:

- No statement that major DD findings allow canonical M4.
- No M4 financing multiplier claim.
- No unqualified “robust optimization” claim.
- Benchmark described as preliminary v0, not full empirical validation.
- Every table value either matches an artifact or cites the exact run/version used.
- Report output claim limited to simple HTML unless PDF artifact exists for final run.
- Entrega2 clearly treated as previous version if included.

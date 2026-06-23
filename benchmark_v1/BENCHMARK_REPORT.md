# Benchmark v1 — Pipeline vs. Manual Excel Targets

**Date:** 2026-06-23
**Branch:** `benchmark-mvp` · **Functional tag:** `functional-2026-06-23` (commit `e349441`)
**Instances:** `/Users/apena/Downloads/instances_yaml_v1/` (godemos, entrena-en-casa, beloop, kavacomex)
**Targets:** verified manually from source `.xlsx` (see `INFORME_CONSISTENCIA.md`)

> Scope: RUN the current pipeline on the 4 real instances and REPORT differences vs.
> manually-derived Excel data. No calibration, no model edits. All ⚠ params
> (`ticket`, `c_min`, `c_u`, `alpha`, …) are **uncalibrated starting points**, so
> absolute revenue/EBITDA deltas are expected. The value here is the *structural*
> patterns that survive regardless of calibration.

---

## CLI / artifact contract (discovered, current code)

- Single config runs via `uv run adventure-capital run --config <yaml> --output <dir>`
  (`run` and `all` are both flagged legacy but functional; both route through the
  **DD assessment gate** — `baseline_only=False`. There is no CLI path to the raw
  deterministic baseline that bypasses the gate.)
- Deterministic metrics live in:
  - `summary.json` → `van` (USD scalar), `valor_desecho_vp` (terminal value VP)
  - `dcf_annual_summary.csv` → `Año, Ingresos, …, EBITDA` per year (USD)
- DD gate verdict in `due_diligence.txt` / `error_log.txt`.

Units: model artifacts are **USD**. Targets are **MUS$ = thousands USD**
(godemos/entrena/kava) and **kUSD** (beloop). To compare, model USD ÷ 1000.

---

## Summary

| Case | DD verdict | VAN model (k) | VAN target (k) | VAN Δ | Status |
|------|-----------|--------------:|---------------:|------:|--------|
| GoDemos | **rejected** (DD03, VC=0) | — | 2005.1 | — | 🚫 GATE-BLOCKED |
| Entrena-en-casa | passed_with_warnings | 933.99 | 1412.85 | **−33.9%** | ⚠ FLAG |
| Beloop | (M1–M3 ok) | 10949.81 | 1923.3 | **+469%** | 🔴 STRUCTURAL |
| KavaComex | (M1–M3 ok) | 1198.71 | 1789.2 | **−33.0%** | ⚠ FLAG |

---

## Per-case detail (model ÷1000 vs target, same units)

### GoDemos — 🚫 blocked before MILP
DD03 `financing_present` is **structural** → `VC <= 0` rejected → verdict
`rejected_for_stochastic`, `valuation_mode: none`. Pipeline stops; **no
`optimized_results.csv`, no `summary.json`, no VAN**. Source treats `VC: 0` as
valid (operating company, working capital = 0). Current gate cannot evaluate it.

### Entrena-en-casa
| Metric | yr1 | yr2 | yr3 |
|--------|----:|----:|----:|
| Revenue model | 125.27 | 498.89 | 2028.50 |
| Revenue target | 173.0 | 486.4 | 1140.7 |
| Δ | −27.6% | +2.6% | **+77.8%** |
| EBITDA model | −51.53 | 312.21 | 1778.09 |
| EBITDA target | −17.8 | 293.4 | 942.2 |
| Δ | (both neg) | +6.4% | **+88.7%** |

VAN: 933.99 vs 1412.85 → **−33.9%**. `valor_desecho_vp = 0`.

### Beloop (kUSD; H=38 → a 4th partial period appears)
| Metric | yr1 | yr2 | yr3 | yr4 |
|--------|----:|----:|----:|----:|
| Revenue model | 668.01 | 4152.14 | 17604.99 | 6127.05 |
| Revenue target | 827.7 | 2324.4 | 4057.8 | — |
| Δ | −19.3% | +78.6% | **+333.9%** | (no target) |
| EBITDA model | 449.41 | 3518.22 | 16096.63 | 5712.53 |
| EBITDA target | 439.6 | 1296.7 | 2387.8 | — |
| Δ | +2.2% | +171% | **+574%** | — |

VAN: 10949.81 vs 1923.3 → **+469%**. Revenue compounding dominates.

### KavaComex
| Metric | yr1 | yr2 | yr3 |
|--------|----:|----:|----:|
| Revenue model | 113.46 | 906.16 | 4103.87 |
| Revenue target | 135.3 | 1052.2 | 2361.0 |
| Δ | −16.1% | −13.9% | **+73.8%** |
| EBITDA model | −113.08 | 403.70 | 2537.07 |
| EBITDA target | −95.6 | 531.2 | 1622.8 |
| Δ | (both neg) | −24.0% | **+56.3%** |

VAN: 1198.71 vs 1789.2 → **−33.0%**. `valor_desecho_vp = 0`.

---

## Structural differences (independent of calibration)

1. **yr3 revenue over-grows systematically** (+74% to +334% across all 3 runnable
   cases) while yr1/yr2 sit roughly in band. The model's recurrence/`alpha`
   compounding ramps far steeper than the Excel ARR curve. A scalar `ticket`
   calibration cannot fix this — it would over/under-shoot a different year.
   → recommend per-year revenue scaling (schema extension), not a `ticket` hack.

2. **Terminal value missing.** `valor_desecho_vp = 0.0` in all runs, but the Excel
   targets include valor desecho (e.g. GoDemos 1197.6). This systematically
   understates VAN — visible as the consistent **≈−33%** on Entrena and KavaComex,
   the two cases not dominated by the revenue blow-up. Worth confirming whether
   terminal value is intended to be off for these configs or is a wiring gap.

3. **GoDemos blocked by DD03.** The gate rejects `VC <= 0` as a structural failure,
   but `VC: 0` is intentional for an operating company. Current code has no way to
   value GoDemos. Either the gate needs a "operating, no initial capital" exemption
   or GoDemos needs a different entry path.

4. **Beloop is a 4-period (H=38) animal** with revenue compounding to ~26× yr1 by
   yr3 — ticket units / recurrence almost certainly mis-specified vs Excel
   (downgrades Enterprise→Pro→Simple not modeled). Expected per INFORME §5; the
   +469% VAN confirms it. Out of ±20% by construction.

## What is NOT a bug
- Absolute revenue/EBITDA gaps in yr1 (−16% to −28%): `ticket` is uncalibrated ⚠.
- EBITDA yr1 negative (Entrena, KavaComex): expected, matches targets' sign.
- `liquidity_policy: none` allowing negative yr1 cash: intentional, reproduces Excel.

## Reproduce
```
uv run adventure-capital run --config <instance>.yaml --output benchmark_v1/<case>_det
# metrics: summary.json:van  +  dcf_annual_summary.csv (Ingresos/EBITDA per Año)
```
Outputs under `benchmark_v1/<case>_det/`. GoDemos produces only DD artifacts (gate stop).
</content>

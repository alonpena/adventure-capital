# Report Generation Specification — Adventure Capital

**Date:** 2026-05-29. Evidence: ✅VC code · 📄VD docs · 🔍INF.
**Key finding:** the working single source of truth is **`report_data.json`** (built by `standard_report/package.py`, consumed by `render.py`). A separate `report_context.yaml` is **NOT needed for Monday** — it is future work. ✅VC

---

## 1. Existing report structure (✅VC, `templates/report.html.j2` + tables/charts/narrative)

The professional report renders from `report_data.json` and is organized as the **4-layer MapValue** (📄VD `report-blueprint.md`): inputs → operating flows → financial results → valuation. Scope is auto-detected `full | ev_only`. ✅VC

Sections actually produced (tables + figures + banded narrative each) ✅VC:
1. Cover (scope-aware), 2. Executive summary, 3. Clients, 4. Services, 5. Revenue, 6. CAC, 7. Operational cost / gross margin, 8. Admin, 9. HR, 10. P&L (EBITDA), 11. Valuation (DCF/EV + WACC + multiples), 12. Unit economics, 13. Sensitivity (WACC×multiple heatmap, tornado, breakeven), + MapValue diagram.

Mapping to the task brief's 18-section target:

| Brief section | Status | Source |
|---|---|---|
| Cover / title | ✅ | document YAML |
| Executive summary | ✅ | `narrate_executive_summary` |
| Company / business model | ✅ (full scope) | document YAML |
| Input assumptions | 🔍 partial (service params tables) | tables |
| Strategic growth plan | ✅ | clients/services tables + figures |
| Optimization results | ✅ | `optimized_results.csv` |
| Client-based indicators | ✅ partial | clients table; **clients-to-X counts missing** |
| Revenue & cost projection | ✅ | revenue/op-cost tables |
| Unit economics | ✅ (terminology caveats) | unit-econ table |
| Enterprise Value (DCF) | ✅ | valuation table + figure |
| Due-diligence diagnostic | 🔍 separate file, not in PDF | `due_diligence_report.md` |
| Monte Carlo / robustness | 🔍 separate CSV, not in PDF | `stochastic_summary.csv` |
| Key risks & warnings | 🔍 partial (narrative + error_log) | narrative |
| Recommendations (entrepreneur/investor) | 🔍 partial | DD recommendations |
| Limitations | ❌ not a section | future |
| Appendices | 🔍 partial | tables |

**Gap to close (future, not Monday):** the DD verdict and the stochastic distribution are produced but **not embedded** in the PDF — they live as sibling files. Embedding them is a template change (medium risk).

---

## 2. `report_data.json` schema (✅VC, the real single source of truth)

```jsonc
{
  "schema_version": "1.0",
  "created_at": "<iso>",
  "document": { "title", "company_name", "report_date", "author", "scope" },
  "dcf": { ...document.dcf... },
  "valuation": { ...summary.json: van, vr_*, beta_*, ebitda_* },
  "due_diligence": { "verdict", "allows_stochastic", "summary", "findings" },
  "summary": { "total_acquisition","total_revenue","total_ebitda","final_cash",
               "minimum_cash","last_year_revenue","last_year_ebitda",
               "last_month_ebitda","unit_economics": {<name>: value} },
  "narrative": { ...full document YAML... },
  "tables": { clientes, servicios, ingresos, cac, costos_operacionales,
              administracion, rrhh, pnl, valorizacion, unit_economics,
              sensibilidad, wacc_base },
  "narratives": { executive, clientes, ..., sensibilidad },
  "source_artifacts": {...}, "derived_artifacts": {...},
  "figures": { <17 figure keys>: "figures/<name>.png" },
  "sensitivity": { "method", "include_ltv_cac_reference" }
}
```

---

## 3. Tables required (✅VC, all built in `tables.py`)
clients (summary + by-service), services (+params), revenue (+recurrence ratio col), CAC decomposition, op-cost (+GP%), admin, HR, P&L cascade, valuation (+WACC components), unit-economics (detail + annual), sensitivity (WACC×multiple, tornado, breakeven).

## 4. Charts required (✅VC, all in `charts.py`, dark theme)
The 17 figures listed in §1 of the demo spec. MapValue is the signature diagram.

## 5. Narrative rules (✅VC, `narrative.py`)
Threshold-**banded** Spanish prose per section (e.g. churn "saludable/moderado/elevado"; LTV/CAC "crítico/ajustado/saludable/excepcional"). The engine **already self-warns** when LTV/CAC > 50× and when GP > 90% — keep those; they show methodological honesty.

## 6. Diagnostic rules surfaced
From calibration (C01–C11) + DD findings + consistency (5 identities). The report should (future) include a "diagnostic" section pulling `due_diligence_report.json` + `calibration_report.json`.

## 7. Investor-facing vs entrepreneur-facing language
- **Investor:** EV range (DCF vs multiples), LTV/CAC (with caveat), robustness p10/p50/p90, P(VAN<0), funding gap, verdict + valuation_mode.
- **Entrepreneur:** required clients/sellers per year, break-even month, funding gap, the DD `adjustment_recommendations` ("raise VC", "smooth acquisition").

## 8. Internal technical work document (concise, traceable)
Already largely exists as the sibling files; for the thesis appendix, consolidate per run:
- `assessment_summary.json` (verdict + decision fields + stochastic).
- `consistency_report.json` (5 math identities pass/fail).
- `calibration_report.md` (C01–C11 with formulas + suggestions).
- `due_diligence_report.md` (findings + recommendations).
- `mapvalue.json` (4-layer snapshot).

## 9. `report_context.yaml` — FUTURE WORK (per scope note)
`report_data.json` already consolidates inputs + results + valuation + DD + narratives. A YAML twin would only add human-editability; **defer**. If ever built, mirror §2 with added `stochastic_summary` and `recommendations` blocks. Low priority.

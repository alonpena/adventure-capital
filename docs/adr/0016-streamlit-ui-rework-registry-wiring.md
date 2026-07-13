# 0016 — Streamlit UI Rework: Registry Wiring and Report-First Views

## Status

Accepted

> Nota 2026-07-12: este archivo era el segundo "0008" (colisión de numeración).
> Renumerado a 0016. La decisión estratégica de arquitectura UI (Streamlit
> in-place, no React) vive en `0008-ui-architecture-consulting-tool.md`; este
> documento cubre el retrabajo mecánico que la implementó.

## Context

The Streamlit MVP pages in `streamlit_pages/` were built for an earlier product
iteration. They worked but had mismatches with the evolved product vision:

1. **No Executive Report as primary view.** The product vision defines
   `report.html` (embedded via iframe) as the authoritative client-facing
   deliverable, with Streamlit drill-down tabs as supporting exploration.

2. **Workflow registry not used.** The CLI now uses `instances create` →
   `executions run` via `workflow_registry.py`, writing to
   `outputs/instances/<id>/` and `outputs/executions/<id>/`. The Streamlit
   config page bypassed this entirely via `tempfile.mkdtemp`.

3. **Terminology outdated.** The product vision distinguishes Consensuated Plan
   (months 1–12, fixed `A_base`) from Projections (months 13–36, optimized).
   The growth plan page showed a single undifferentiated series.

4. **No execution history browsing.** Each run was ephemeral.

5. **No integration with Phase 5 standard report.** The report generator lived
   only in the CLI.

6. **No downloadable artifacts.** The product vision requires PDF, Excel, and
   HTML+PDF downloads per page.

7. **Due Diligence verdict schema incomplete.** The product vision defines 5
   verdicts with decision fields (`valuation_mode`, `adjustment_level`,
   `blocking_reasons`, `rerun_recommended`).

8. **Stochastic page used overly technical terms.** The product vision prefers
   generic/descriptive Spanish for the consulting audience.

## Decision

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Streamlit UI (app.py + streamlit_pages/)             │
│                                                       │
│  Sidebar:                                             │
│    Gestor de Instancias  ← always available           │
│    Ejecuciones Recientes ← pick from past runs        │
│    Drill-down tabs      ← shown when run selected     │
│      [Informe Ejecutivo]  ← report.html via iframe    │
│      [Plan de Crecimiento]                            │
│      [Valoración]                                     │
│      [Due Diligence]                                  │
│      [Análisis de Escenarios]                         │
│                                                       │
│  Reads from: outputs/executions/<run_id>/              │
│    - Canonical CSVs (optimized_results.csv, …)         │
│    - Canonical JSONs (growth_plan_summary.json, …)     │
│    - report.html (iframe)                              │
│    - postprocessed_results/ (derived view)              │
└─────────────────────────────────────────────────────┘
```

### Key Decisions

1. **Workflow registry is the source of truth for runs.**
   `outputs/instances/<id>/` and `outputs/executions/<id>/` are the canonical
   locations. The Streamlit UI reads and writes from the same directory
   structure as the CLI.

2. **Executive Report is embedded via iframe as first tab.**
   `report.html` is shown automatically when a run is selected. The drill-down
   tabs read the same canonical artifacts that feed the report.

3. **Instance manager is the landing page.**
   First view: create instances via form or YAML upload, list existing
   instances, delete instances. From an instance, trigger an execution.

4. **Execution history is browsable from the sidebar.**
   Past executions are listed with status indicators (🟢 completed, 🔴 failed,
   🟡 blocked). Selecting one switches the main view to its results.

5. **Canonical CSVs are the primary data source.**
   `components.py` reads `optimized_results.csv`, `dcf_*.csv`,
   `unit_economics.csv`, etc. directly. `postprocessed_results/` is a
   secondary/derived view.

6. **Download buttons generate on-the-fly.**
   - Growth Plan → Excel (.xlsx) from canonical CSVs
   - Valuation → HTML+PDF from standard report artifacts
   - Executive Report → PDF from report.pdf

7. **Phase 5 report generation is offered post-run.**
   If `report_data.json` / `report.html` don't exist, the UI shows a
   "Generar Reporte Estandar" button that calls `render_report()`.

8. **Due Diligence shows full verdict schema.**
   All 5 verdicts, `valuation_mode`, `adjustment_level`, `blocking_reasons`,
   `rerun_recommended`, and findings by severity.

9. **Stochastic page uses generic Spanish.**
   "Análisis de Escenarios" with descriptive labels: Escenarios generados,
   Distribución de VAN, Probabilidades, Brecha de financiamiento — not
   academic acronyms.

10. **Consensuated Plan vs Projections displayed side-by-side.**
    Months 1–12 (Consensuated) and 13–36 (Projections) as adjacent columns
    with a combined 36-month chart below.

## Consequences

- Streamlit runs are now visible to the CLI and vice versa — instances and
  executions are shared state under `outputs/`.
- The old `tempfile.mkdtemp` pattern is removed.
- `components.py` must handle both canonical CSVs and postprocessed JSONs
  gracefully, falling back to one when the other is missing.
- Download helpers require `openpyxl` for Excel output.
- The UI no longer calls `run_pipeline()` directly — it delegates to the
  workflow registry, which calls it.

## References

- CONTEXT.md — UI Architecture section
- `src/adventure_capital/workflow_registry.py` — instances + executions
- `src/adventure_capital/postprocess.py` — postprocessed results view
- `src/adventure_capital/standard_report/` — Phase 5 report pipeline
- `docs/adr/0002-standard-report-blueprint.md` — report blueprint

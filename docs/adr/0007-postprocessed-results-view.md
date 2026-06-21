# Postprocessed Results are a derived view, not a source of truth

## Status

Accepted

## Context

The pipeline already produces two artifact layers:

1. **Canonical flat outputs** — `optimized_results.csv`, `dcf_cashflow.csv`,
   `unit_economics.csv`, `valuation_summary.json`, `formula_trace.json`,
   `growth_plan_summary.json`, `model_instance.json`, and the due-diligence /
   stochastic outputs. These are the computed source of truth.
2. **Report Data Package** — `report_data.json` + `artifacts_manifest.json`
   (see ADR 0003), a render-ready normalization consumed by the standard report.

The accelerated growth plan and valuation workbook need an additional
representation: audience-tagged folders that read like an Excel workbook for the
entrepreneur (Alejandro) and that the future UI can navigate page-by-page. The
risk is introducing a **third** copy of the same numbers that can silently drift
from the canonical layer and break auditability.

## Decision

Add a third layer, `postprocessed_results/`, defined strictly as a **derived,
non-canonical view**:

- It only **copies** existing JSON artifacts or **selects/renames** columns from
  the canonical CSVs, plus trivial presentation transforms (year/month index,
  cumulative sums, month-over-month deltas).
- It **never** recomputes valuation, unit economics, due diligence, or
  stochastic metrics. Any file that would duplicate a canonical JSON is a copy of
  it, not a re-derivation with a new schema.
- It is built by a single idempotent function that reads the flat files from
  `output_dir` on disk (not from in-memory model objects), so it is structurally
  incapable of recomputing model logic — the same way the UI will read it.
- Folders are written only when their source artifacts exist, so deterministic-
  only runs, `baseline_only` runs, and `rejected_for_stochastic` cases degrade
  gracefully.

Canonical sources of truth remain the flat outputs, the Report Data Package, and
the artifacts manifest.

## Consequences

- One extra, cheap presentation layer; auditors trace any workbook value back to
  one canonical file.
- Reading from disk enforces invariant #8 (UI/report reads artifacts, never
  recomputes) at the layer boundary.
- Trade-off: a fourth thing to keep wired into both `run_pipeline` and
  `run_assessment`; mitigated by a single shared function and presence checks.
- If a workbook file would only duplicate a canonical JSON, we copy rather than
  invent a parallel schema, avoiding the drift this ADR exists to prevent.

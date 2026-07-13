# Report data package boundary for standard valuation reports

Status: Accepted (header añadido 2026-07-12; decisión vigente, sin revisión desde su creación)

The standard valuation report uses a separate document YAML and an intermediate Report Data Package instead of rendering directly from model configuration and raw CSV outputs.

The core `run` command remains scoped to Phases 1-4: financial model, optimization, valuation, unit economics, and basic artifacts. The Phase 5 `report` command consumes an existing output directory plus a required document YAML under `reports/`.

The document YAML contains report narrative and presentation inputs. It does not define optimization assumptions. The report command validates required blueprint narrative fields by default. Missing required document fields or missing core artifacts fail the command, write `report_validation.json`, and do not generate `report.html`.

When validation succeeds, Phase 5 builds:

- `report_data.json` with normalized render-ready business facts.
- `artifacts_manifest.json` with artifact inventory, provenance, source file map, and checks.

The renderer consumes these package files rather than recomputing all facts from scattered CSV files.

This adds an explicit boundary between calculation and document composition, supports auditability, and allows future HTML, PDF, PPT, or web renderers to reuse the same data package. The trade-off is additional schema and artifact management compared with a simpler direct CSV-to-template renderer.

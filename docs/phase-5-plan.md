# Phase 5 Plan: Standard Valuation Report Generator

Phase 5 turns the current Phase 4 report artifacts into a full standard valuation report generator based on `docs/report-blueprint.md`.

## Goal

Generate a Spanish business-facing valuation report of roughly 36-48 pages from one YAML instance and pipeline outputs.

Target artifacts:

- `report.html`
- `report.pdf`
- `figures/*.png`
- enriched CSV outputs
- `mapvalue.json`

## Inputs

### Required existing inputs

- `configs/base.yaml` or scenario YAML
- `optimized_results.csv`
- `fixed_cashflow.csv`
- `dcf_cashflow.csv`
- `dcf_annual_summary.csv`
- `multiples_valuation.csv`
- `unit_economics.csv`

### Document YAML

Phase 5 uses a separate document YAML per report. The model/scenario YAML remains focused on optimization and valuation assumptions. The document YAML owns report narrative and presentation-only fields and can reference an existing output directory.

Document YAML files live under `reports/`.

Example paths:

```text
reports/valuation-base.yaml
reports/solutionops-valuation.yaml
```

Document-only sections:

- `document`
- `empresa`
- `target_market`
- `modelo_negocio`
- `equipo`
- `problemas`
- `unidades`
- `fx`
- `fecha_referencia`
- `dcf` extended presentation assumptions
- `inversion`
- `cap_table`
- `pasivos`
- `floor_value`
- `report`

These fields feed the report generator only unless explicitly wired into model calculations later.

The standard report expects all blueprint narrative fields by default. Missing document fields are validation findings and should block standard rendering unless a future draft mode explicitly allows placeholders.

### Report Data Package

Phase 5 introduces a report-ready intermediate package between optimization/valuation outputs and final rendering:

- `report_data.json` — normalized report-ready facts, tables, section metrics, and references used by HTML/PDF generation.
- `artifacts_manifest.json` — inventory, provenance, source file map, and validation checks for the run.

The renderer consumes the Report Data Package first. CSVs remain raw/audit outputs and can still be referenced for traceability. If strict document validation fails, write `report_validation.json` only; do not write `report_data.json` because that file means a complete render-ready package.

## Outputs to Add

### Sensitivity outputs

- `sensitivity_wacc_multiple.csv`
- `sensitivity_variables.csv`
- `breakeven_variables.csv`

### MapValue output

- `mapvalue.json`

`mapvalue.json` snapshots the 4 report layers:

1. Input variables
2. Operating flows
3. Financial results
4. Valuation

## Architecture

Keep existing `src/adventure_capital/reporting.py` for Phase 4 basic reports. Add a separate Phase 5 package to avoid breaking existing imports:

```text
src/adventure_capital/standard_report/
├── __init__.py
├── document.py         # document YAML loading
├── schema.py           # simple YAML schema loading and required-path checks
├── validation.py       # validation result model and report_validation.json writer
├── package.py          # report_data.json and artifacts_manifest.json builders
├── charts.py           # Matplotlib pre-rendered figures
├── sensitivity.py      # WACC/multiple and variable sensitivity tables
├── render.py           # HTML/PDF rendering
├── templates/
│   ├── report.html.j2
│   └── styles.css
└── sections.py         # blueprint/TOC page metadata if needed
```

## Public API

```python
from adventure_capital.pipeline import run_pipeline
from adventure_capital.reporting import render_report

result = run_pipeline(config, output_dir="outputs/base")
render_report("outputs/base", blueprint_path="docs/report-blueprint.md")
```

CLI targets stay separated by pipeline boundary:

```bash
# Phases 1-4: core model, optimization, valuation, basic artifacts
uv run adventure-capital run --config configs/base.yaml --output outputs/base

# Phase 5: standard valuation document from an existing output directory
uv run adventure-capital report --input outputs/base --document reports/valuation-base.yaml --blueprint docs/report-blueprint.md
```

`--document` is required for the `report` command. `run` does not accept report document inputs. `report` does not solve the optimization model.

## Dependency Plan

Add only when implementation starts:

- `jinja2` for templates
- `weasyprint` for PDF rendering

Keep Matplotlib for chart generation.

Do not make PDF rendering required for core model tests. If WeasyPrint system dependencies are problematic, HTML generation remains required and PDF generation can be optional/skipped.

## Delivery Split

### Phase 5A — Data contract

- Add separate document YAML support for report-only narrative and presentation fields.
- Keep model/scenario YAML independent from report narrative.
- Define required document fields in `reports/schema/valuation-document.schema.yaml` using a simple custom YAML schema with required paths and basic collection constraints.
- Treat blueprint pages marked `[OPT]` as optional for validation: missing optional sections do not block report generation.
- Still define schemas for optional sections so they can be filled and validated later (`equipo`, `timeline`, `problemas`, scenario comparison, `floor_value`/`pasivos`, and `report.team`).
- Omit optional pages from `report.html` when their document sections are absent; visible page numbers are sequentially generated from rendered pages.
- Preserve blueprint page references as metadata in `report_data.json` or `artifacts_manifest.json` for traceability only.
- Build `report_data.json` from the document YAML plus the minimal context needed from existing core output artifacts.
- Do not require an in-memory `run_pipeline()` result to build `report_data.json`; Phase 5 reads an existing output directory.
- Build `artifacts_manifest.json` as the output inventory and provenance layer.
- Validate document YAML against required blueprint narrative fields by default using the schema file.
- Flag missing document fields before rendering; default report generation is strict because the standard report is client-facing.
- On missing required document fields or missing Phase 1-4 core artifacts, fail the report command, write `report_validation.json`, and do not generate `report.html`.
- Require these existing core artifacts before building the Report Data Package: `optimized_results.csv`, `fixed_cashflow.csv`, `dcf_cashflow.csv`, `dcf_annual_summary.csv`, `multiples_valuation.csv`, and `unit_economics.csv`.
- Ensure core pipeline still runs if report-only document YAML is absent.

### Phase 5B — Derived report artifacts

Implement pure calculations:

- WACC × EBITDA multiple sensitivity matrix.
- Operational variable sensitivity table.
- EBITDA=0 breakeven table.
- MapValue JSON.

Sensitivity analysis is configured in the document YAML because it is report analysis configuration, not a core model assumption. Default method is `calculation`, using existing Phase 1-4 outputs. MVP does not re-optimize the MILP. The implementation must keep a clear method boundary for upcoming `deterministic_rerun` sensitivity, where multiple standard instances are solved with parameter variations. This is deterministic scenario rerunning, not stochastic optimization.

Example document YAML:

```yaml
sensitivity:
  method: calculation
  wacc_range: [-0.06, -0.04, -0.02, 0, 0.02, 0.04, 0.06]
  ebitda_multiple_range: [0.5, 0.75, 1.0, 1.25, 1.5]
  include_ltv_cac_reference: true
```

If `include_ltv_cac_reference` is true and LTV/CAC is available in `unit_economics.csv`, the LTV/CAC ratio is included as a valid reference multiple in sensitivity outputs.

Outputs:

- `sensitivity_wacc_multiple.csv`
- `sensitivity_variables.csv`
- `breakeven_variables.csv`
- `mapvalue.json`

### Phase 5C — Figure catalog

Generate required figure PNGs:

- `acquisition_year1.png`
- `revenue_breakdown_3y.png`
- `cashflow_monthly.png`
- `client_revenue_36m.png`
- `cac_components.png`
- `gross_margin_progression.png`
- `sensitivity_heatmap.png`
- `unit_economics_grid.png`
- `mapvalue_diagram.png`

### Phase 5D — HTML report MVP

Build one normalized report context from `report_data.json` plus `artifacts_manifest.json`.

`report_data.json` combines:

- document YAML narrative sections
- pipeline result metrics
- annual aggregations
- chart references
- derived report artifacts

`artifacts_manifest.json` combines:

- source file paths
- generated artifact paths
- provenance metadata
- validation checks

Render `report.html` using Jinja2 and a dark theme CSS.

Must support:

- blueprint-aligned section order
- page-oriented sections
- hero tiles
- tables
- chart embeds
- placeholders for optional narrative fields
- footer: `Confidencial · Adventure Capital · {{report_date}} · {{page}}`

### Phase 5E — CLI and tests

- Add `adventure-capital report --input outputs/base --blueprint docs/report-blueprint.md`.
- Add report smoke tests for HTML generation and required artifacts.
- Keep core model tests independent from report-only fields.

### Phase 5F — PDF and polish

Render `report.pdf` with WeasyPrint from the same HTML.

PDF rendering is exposed through `render_report(..., pdf=True)` and CLI `--pdf`. Tests should not hard-fail only because the PDF backend is unavailable in a given environment.

Add pagination/theme polish after HTML content is complete.

## Phase 6 — Scenario comparison

Support optional `report.comparativa.config_ref`.

If present:

- run second scenario
- produce PULL vs PUSH comparison table
- render optional page 40

## Tests

Minimum Phase 5 tests:

- Base config validates with new report sections.
- Pipeline still runs without report-only sections.
- Sensitivity WACC × multiple output has expected grid dimensions and finite values.
- Breakeven output has expected variables and finite/nullable values.
- `mapvalue.json` contains 4 layers.
- HTML report renders and contains expected section titles.
- PDF render is smoke-tested only when WeasyPrint is available.
- CLI `report` command creates `report.html` from existing output directory.

## Non-goals for Phase 5

- Do not change MILP objective.
- Do not make narrative fields required for optimization.
- Do not rewrite the solver or valuation core.
- Do not require PDF generation for Colab/notebook usage.
- Do not implement full design perfection before HTML content is complete.

## Risks

- WeasyPrint system dependencies may break portability.
- 36-48 page scope is large; HTML should come before polished PDF.
- Future enriched model reruns may need to replace or complement the current default calculation-based sensitivity method.
- `report-blueprint.md` is declarative but not machine-readable yet; initial implementation can hardcode section order while preserving blueprint alignment.

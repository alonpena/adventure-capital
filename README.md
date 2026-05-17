# Adventure Capital

MILP optimization model for accelerated growth planning.

## Setup

```bash
uv sync
```

## Run pipeline

CLI writes artifacts by default. If `--output` omitted, output goes to timestamped directory under `outputs/`.

```bash
uv run adventure-capital run --config configs/base.yaml --output outputs/experiment-1
```

Generated Phase 1-4 artifacts:

- `financial_report.md`
- `dashboard.png`
- `fixed_cashflow.csv`
- `optimized_results.csv`
- `dcf_cashflow.csv`
- `dcf_annual_summary.csv`
- `multiples_valuation.csv`
- `unit_economics.csv`

## Generate standard valuation report

Phase 5 consumes an existing output directory from `run` plus a required document YAML under `reports/`.

```bash
uv run adventure-capital report \
  --input outputs/experiment-1 \
  --document reports/valuation-base.yaml \
  --blueprint docs/report-blueprint.md
```

Generated Phase 5 artifacts:

- `report_data.json`
- `artifacts_manifest.json`
- `sensitivity_wacc_multiple.csv`
- `sensitivity_variables.csv`
- `breakeven_variables.csv`
- `mapvalue.json`
- `figures/*.png`
- `report.html`

PDF rendering:

```bash
uv run adventure-capital report \
  --input outputs/experiment-1 \
  --document reports/valuation-base.yaml \
  --pdf
```

On macOS, WeasyPrint may need Homebrew libraries visible:

```bash
brew install pango
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib uv run adventure-capital report \
  --input outputs/experiment-1 \
  --document reports/valuation-base.yaml \
  --pdf
```

## Python API

```python
from adventure_capital.config import default_config, load_config
from adventure_capital.pipeline import run_pipeline

result = run_pipeline(default_config())

config = load_config("configs/base.yaml")
result = run_pipeline(config, output_dir="outputs/experiment-1")
```

Without `output_dir`, API returns dataframes/dicts and writes no files.

## Tests

```bash
uv run pytest
uv run ruff check src tests
```

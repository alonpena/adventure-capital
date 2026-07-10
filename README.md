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

## Launch the app (Streamlit UI)

**Online (recommended — no install):**

App is hosted on Streamlit Community Cloud from the `deploy-production` branch:

```
https://<your-app-name>.streamlit.app
```

Just open the link in a browser. Nothing to install.

**Local (for development):**

```bash
uv sync
uv run streamlit run app.py
```

Opens at `http://localhost:8501`. Requires `uv` installed (`brew install uv` on macOS).

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

## Future work

- **Working-capital management.** Advanced working-capital policy (e.g. minimum-cash
  covenants, payment-cycle timing) is deferred. The MILP currently enforces a single
  liquidity contract: accumulated cash may not fall below the financing ticket,
  `Caja[t] >= -VC`. See ADR 0010.
- **Stochastic parity for the growth law.** The deterministic model uses the logarithmic
  market-saturation ceiling (ADR 0010); the stochastic model still uses the legacy
  moving-average smoothing. Aligning them is pending (ADR 0009 territory).
- **After-tax valuation.** The MILP objective is pre-tax NPV(EBITDA); taxes and
  free-cash-flow timing are applied linearly post-solve in `valuation.py`.

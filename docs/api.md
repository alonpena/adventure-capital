# Python API Plan

The package must support notebook and Colab-style exploration in addition to the CLI.

## Intended Usage

```python
from adventure_capital.config import default_config, load_config
from adventure_capital.pipeline import run_pipeline

config = default_config()
result = run_pipeline(config)
```

Load YAML config:

```python
config = load_config("configs/base.yaml")
result = run_pipeline(config)
```

Generate artifacts from Python by passing an output directory:

```python
result = run_pipeline(config, output_dir="outputs/experiment-1")
```

## API Principles

- Python API returns structured objects for interactive analysis.
- Python API does not write files unless `output_dir` is provided.
- CLI writes artifacts by default for product-facing runs.
- All core calculations must be callable without report generation.
- Outputs preserve Spanish business-facing labels.
- Codebase uses English module and function names.

## Core API Surface

```python
def default_config() -> dict: ...
def load_config(path: str) -> dict: ...
def generate_instance(config: dict) -> dict: ...
def build_financial_model(instance: dict) -> object: ...
def solve_growth_plan(instance: dict, *, verbose: bool = False, time_limit: int = 120) -> object: ...
def extract_results(instance: dict, solution: object) -> object: ...
def calculate_dcf(results, instance: dict) -> dict: ...
def calculate_unit_economics(results, instance: dict, dcf: dict | None = None): ...
def run_pipeline(config: dict, *, output_dir: str | None = None, verbose_solver: bool = False) -> object: ...
def generate_report(result: object, output_dir: str) -> dict: ...
def render_report(output_dir: str, *, blueprint_path: str = "docs/report-blueprint.md") -> dict: ...
```

Current `run_pipeline()` return dictionary after Phase 4:

- `instance`: generated model instance dictionary.
- `fixed_cashflow`: 12-row fixed acquisition period DataFrame.
- `solution`: solver status, objective, PuLP problem, and variables.
- `optimized_results`: full-horizon monthly results DataFrame.
- `summary`: aggregate optimization metrics.
- `dcf`: DCF valuation dictionary, including monthly cashflow, annual summary, and `VAN`.
- `multiples_valuation`: revenue and EBITDA multiples valuation dictionary.
- `unit_economics`: business-facing unit economics DataFrame.
- `artifacts`: output path dictionary when `output_dir` is provided.

When `output_dir` is provided, report generation writes:

- `financial_report.md`
- `dashboard.png`
- `fixed_cashflow.csv`
- `optimized_results.csv`
- `dcf_cashflow.csv`
- `dcf_annual_summary.csv`
- `multiples_valuation.csv`
- `unit_economics.csv`

Concrete return types may later move from dictionaries/DataFrames to typed result objects.

## Phase 5 Report API

Phase 5 adds a standard valuation report renderer based on `docs/report-blueprint.md`.

Phase 5 uses a separate document YAML under `reports/` for report narrative and presentation-only fields. Optimization config stays focused on model assumptions.

Planned Python usage:

```python
from adventure_capital.config import load_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.reporting import build_report_data_package, render_report

config = load_config("configs/base.yaml")
result = run_pipeline(config, output_dir="outputs/base")
build_report_data_package(
    "outputs/base",
    document_path="reports/valuation-base.yaml",
    blueprint_path="docs/report-blueprint.md",
)
render_report("outputs/base", document_path="reports/valuation-base.yaml")
```

Planned CLI usage keeps the core and report pipelines separate:

```bash
uv run adventure-capital run --config configs/base.yaml --output outputs/base
uv run adventure-capital report --input outputs/base --document reports/valuation-base.yaml --blueprint docs/report-blueprint.md
```

`run` owns Phases 1-4 and writes core artifacts. `report` owns Phase 5 and consumes an existing output directory. `--document` is required for `report`. Standard report generation validates required blueprint narrative fields and required Phase 1-4 core artifacts by default, writes `report_validation.json` on missing inputs, fails hard, and does not generate `report.html`.

Expected Phase 5 data-package outputs:

- `report_data.json` — normalized report-ready facts, section metrics, and references.
- `artifacts_manifest.json` — provenance, source file map, generated artifact inventory, and checks.

Core pipeline calculations must remain callable without Phase 5 report generation.

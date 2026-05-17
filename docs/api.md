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
def generate_report(result: object, output_dir: str) -> None: ...
```

Concrete return types will be finalized during implementation. First refactor may use dictionaries and pandas DataFrames; later versions can introduce typed result objects.

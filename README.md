# Adventure Capital

MILP optimization model for accelerated growth planning.

## Setup

```bash
uv sync
```

## Phase 1: fixed-period financial model

```bash
uv run adventure-capital run --config configs/base.yaml --output outputs/phase-1
```

Python API:

```python
from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline

result = run_pipeline(default_config())
fixed_cashflow = result["fixed_cashflow"]
```

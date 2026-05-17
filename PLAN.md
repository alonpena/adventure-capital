# Plan: Convert Colab Notebook Export into Cohesive Python Codebase

## Goal

Turn `optimizacion_plan_crecimiento_acelerado_v3 (1).py` into groundwork for a full financial planning pipeline managed with `uv` and `pyproject.toml`.

The immediate migration preserves current optimization behavior, but package boundaries should support the larger product pipeline:

1. Financial modeling of cashflow structure for fixed acquisition period.
2. Optimization of accelerated growth plan for remaining horizon.
3. DCF valuation and unit economics calculation.
4. Financial report generation.

## Current State

- Single exported Colab Python file, about 2,000 lines.
- Contains notebook markdown, Colab magic, imports, configuration, preprocessing, MILP model, result extraction, valuation, unit economics, visualization, and pipeline orchestration.
- Not cleanly importable because of `!pip install pulp --quiet` and top-level execution.
- Functions are already mostly separable, so refactor can be incremental.
- Current model is multi-service by service index `s`: each service has its own acquisition, active client pool, recurrence frequency, price, churn, and costs.

## Target Layout

```text
adventure-capital/
├── pyproject.toml
├── README.md
├── PLAN.md
├── .python-version
├── configs/
│   └── base.yaml
├── outputs/
│   └── .gitkeep
├── src/
│   └── adventure_capital/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── instance.py
│       ├── financial_model.py
│       ├── model.py
│       ├── results.py
│       ├── valuation.py
│       ├── unit_economics.py
│       ├── reporting.py
│       └── pipeline.py
└── tests/
    ├── test_instance.py
    ├── test_model_smoke.py
    └── test_valuation.py
```

## Module Responsibilities

### `config.py`

Owns input configuration.

- Load config from YAML.
- Provide default/base config equivalent to current `cargar_parametros_base()`.
- Validate required fields and basic shape.

### `instance.py`

Owns model instance generation.

- Port `generar_instancia()`.
- Port `mostrar_resumen_instancia()` as optional reporting helper.
- Keep preprocessing deterministic and side-effect free except explicit reporting.

### `financial_model.py`

Owns deterministic cashflow modeling for the fixed acquisition period.

- Build the first 12 months from configured `A_base` acquisition.
- Treat the fixed acquisition period as exactly 12 months.
- Treat total planning horizon `H` as configurable.
- Reuse cohort, revenue, cost, CAC, EBITDA, and cash formulas shared with optimization.
- Produce baseline cashflow outputs independent of solver feasibility.

### `model.py`

Owns PuLP model construction and solve for the optimization period.

- Port `construir_y_resolver_modelo()`.
- Keep months 1-12 fixed from `A_base`.
- Optimize acquisition and resource decisions from month 13 through configurable horizon `H`.
- Split into `build_model()` and `solve_model()` if useful.
- Preserve current constraints first; improve only after tests capture baseline behavior.

### `results.py`

Owns conversion from solver variables to tabular outputs.

- Port `extraer_resultados()`.
- Port `imprimir_resultados_mvp()`.
- Add CSV export helpers later if needed.

### `valuation.py`

Owns valuation calculations.

- Port `calcular_valorizacion_dcf()`.
- Port `calcular_valorizacion_multiplos()`.

### `unit_economics.py`

Owns unit economics calculations.

- Port `calcular_unit_economics()`.

### `reporting.py`

Owns financial report generation.

- Treat visualization as one report-generation output, not as core modeling logic.
- Generate Markdown report, dashboard PNG, core CSV tables, charts, tables, and narrative summaries.
- Initially port dashboard plot generation here or under a reporting submodule.

### `pipeline.py`

Owns orchestration.

- Port `run_optimization_pipeline()`.
- Return structured result object or dictionary.
- No implicit execution at import time.

### `cli.py`

Owns command line entrypoint.

Expected command:

```bash
uv run adventure-capital run --config configs/base.yaml --output outputs/
```

If `--output` is omitted, CLI writes to a timestamped directory under `outputs/`.

### Python API

Supports notebooks and Colab-style exploration without mandatory file writes.

```python
from adventure_capital.config import load_config
from adventure_capital.pipeline import run_pipeline

config = load_config("configs/base.yaml")
result = run_pipeline(config)
```

Passing `output_dir` enables report/dashboard/CSV generation from Python.

## Dependency Management

Use `uv` and `pyproject.toml`.

Initial dependencies:

```toml
[project]
name = "adventure-capital"
version = "0.1.0"
description = "MILP optimization model for accelerated growth planning"
requires-python = ">=3.11"
dependencies = [
  "matplotlib>=3.8",
  "numpy>=1.26",
  "pandas>=2.2",
  "pulp>=2.8",
  "pyyaml>=6.0",
]

[project.scripts]
adventure-capital = "adventure_capital.cli:main"

[dependency-groups]
dev = [
  "pytest>=8.0",
  "ruff>=0.6",
]
```

## Migration Steps

1. Create package skeleton, `pyproject.toml`, `.python-version`, and output directory.
2. Move base parameters into `configs/base.yaml`.
3. Port `cargar_parametros_base()` into `config.py` as loader/default config.
4. Port `generar_instancia()` into `instance.py`.
5. Extract deterministic fixed-period cashflow modeling into `financial_model.py` for baseline/reporting.
6. Port full-horizon optimization build/solve into `model.py`, keeping months 1-12 fixed and months 13-H optimized.
7. Port result extraction/reporting into `results.py`.
8. Port valuation into `valuation.py`.
9. Port unit economics into `unit_economics.py`.
10. Port visualization/report output into `reporting.py` as first report-generation capability.
11. Port orchestration into `pipeline.py`.
12. Add CLI in `cli.py`.
13. Delete notebook top-level execution from migrated code.
14. Add smoke tests.
15. Update README with `uv sync`, `uv run`, config, and output examples.

## Test Plan

### Unit tests

- Config loads and validates, including `H >= 14`.
- Instance generation creates expected horizon, service count, base acquisition, discount factors, churn, recurrence, and survival dictionaries.
- Fixed-period financial model produces 12 monthly cashflow rows from `A_base`.
- DCF returns expected keys and finite values for minimal fixture.

### Smoke test

- Load base config.
- Generate instance.
- Solve with small time limit.
- Extract non-empty results dataframe.
- Assert solver status is known (`Optimal`, `Infeasible`, etc.) and no exceptions occur.

### Regression baseline

Before refactor, run current notebook logic once after removing Colab magic/top-level hazards or by temporary script extraction. Save key outputs:

- solver status
- total acquisition
- total revenue
- total EBITDA
- final cash
- DCF VAN

After refactor, compare same metrics within tolerance.

## Known Code Issues to Address During Migration

- Remove `!pip install pulp --quiet`.
- Replace commented liquidity constraints with explicit configurable liquidity policy.
- Remove all import-time execution.
- Resolve duplicate `generar_visualizaciones()`.
- Avoid mutating input dataframes in visualization code unless intentional.
- Decide whether Spanish function/domain names stay or Python API moves to English.
- Decide whether configuration schema stays Spanish to match model terminology.
- Capture solver status and infeasibility handling consistently.
- Fix commercial staffing monotonicity at the month 12 to month 13 transition.

## Decisions

1. Public API language: English codebase, Spanish business-facing outputs.
2. Configuration source of truth: YAML primary, with Python `default_config()` for tests and examples.
3. Pipeline has four stages: cashflow modeling for the fixed acquisition period, accelerated growth optimization for the remaining horizon, valuation/unit economics, and financial report generation.
4. Optimization implementation remains full-horizon initially: months 1-12 fixed, months 13-H optimized. Interfaces should allow future split where optimization starts from Stage 1 ending state.
5. Fixed acquisition period is exactly 12 months. Total planning horizon `H` remains configurable and must be greater than 12. First refactor validates `H >= 14` because current smoothing constraints reference months 13 and 14 explicitly.
6. Model granularity is monthly only. Annual figures are aggregations of monthly periods, not separate annual model periods.
7. Multi-service semantics remain service-indexed: acquisition, active client pool, recurring sales, new sales, and total services sold are calculated per service.
8. Repurchase timing remains preprocessed as a binary parameter to reduce optimization complexity, not modeled as a solver decision variable.
9. Churn is service-specific and exogenous, applied through service cohort survival; a customer may churn from one service without implying churn from another service.
10. Acquisition creates exactly one new sale for the same service and same monthly period.
11. Service price is constant per service in the first refactor. Configuration/schema should leave room for future period-specific prices.
12. Repurchase rate (`alpha`) applies only to eligible surviving customers in a service cohort during a repurchase window.
13. Liquidity policy is configurable. First refactor defaults to `none` to preserve current behavior, while supporting future policies such as `non_negative`, `minimum_cash`, `runway_months`, and `working_capital_dynamic`.
14. Optimization objective remains discounted EBITDA for the first refactor. Future objective policies may include post-tax cashflow or full DCF VAN.
15. Commercial staffing is monotonic across the transition from fixed period to optimized forecast: month 13 staffing must be at least month 12 staffing, and staffing remains non-decreasing afterward.
16. Commercial productivity lag is configurable. Default is same-period productivity (`lag = 0`) to preserve current behavior; `lag = 1` can require prior-month staff for acquisition capacity.
17. Operational cost uses max-cost semantics: each service-period cost is constrained by both variable usage cost and minimum capacity-step cost, so the effective cost is the greater of the two, not fixed plus variable.
18. First report generator produces a Markdown report with linked dashboard PNG and CSV outputs.
19. Package exposes both CLI and Python API. CLI writes a timestamped output directory by default; Python API returns objects by default and writes artifacts only when `output_dir` is provided.
20. Python API is documented in `docs/api.md` for notebook and Colab-style exploration.
21. Use simple config validation first: plain dictionaries/dataclasses with explicit validation functions. Defer Pydantic until config complexity or UX requires it.
22. Use light solver abstraction now: PuLP/CBC remains the only implemented solver, but config includes solver name, time limit, and verbosity for future extension.
23. Formal mathematical formulation lives in `docs/model.md`, not README or code-only docstrings.

## Open Decisions

No open decisions currently.

## Recommended Defaults

- Use English module/function names for package API.
- Preserve Spanish dataframe column labels and domain labels initially to avoid breaking notebook outputs.
- Use YAML config as primary external config, with Python `default_config()` for tests.
- Keep PuLP/CBC as the only implemented solver for first refactor, behind light solver config.
- Maintain full-horizon MILP first for regression safety, while leaving boundaries open for later staged optimization.
- Treat dashboard visualization as reporting, not core optimization.
- CLI writes timestamped outputs by default; Python API writes only when `output_dir` is provided.
- Use manual validation first; add Pydantic only if config complexity grows.

# AGENTS.md

Guidance for coding agents working on this repository.

## Project Goal

Convert `optimizacion_plan_crecimiento_acelerado_v3 (1).py`, an exported Colab notebook, into a cohesive Python codebase managed with `uv` and `pyproject.toml`.

This is not only notebook cleanup. It is groundwork for a full financial planning pipeline:

1. Financial modeling of cashflow structure for the fixed acquisition period.
2. Optimization of the accelerated growth plan for the remaining horizon.
3. DCF valuation and unit economics calculation.
4. Financial report generation.

Read these files before changing architecture:

- `PLAN.md`
- `CONTEXT.md`
- `docs/model.md`
- `docs/api.md`
- `docs/adr/0001-operational-cost-floor.md`

## Current Source File

Main legacy source:

```text
optimizacion_plan_crecimiento_acelerado_v3 (1).py
```

It is an exported Colab notebook and is not cleanly importable because it contains:

- `!pip install pulp --quiet`
- notebook markdown blocks
- top-level execution
- duplicate visualization function

Main functions inside legacy file:

- `cargar_parametros_base()`
- `generar_instancia()`
- `mostrar_resumen_instancia()`
- `construir_y_resolver_modelo()`
- `extraer_resultados()`
- `imprimir_resultados_mvp()`
- `calcular_valorizacion_dcf()`
- `calcular_valorizacion_multiplos()`
- `calcular_unit_economics()`
- `generar_visualizaciones()` — defined twice; second version overrides first
- `run_optimization_pipeline()`

## Target Layout

```text
adventure-capital/
├── pyproject.toml
├── README.md
├── PLAN.md
├── AGENTS.md
├── .python-version
├── configs/
│   └── base.yaml
├── outputs/
│   └── .gitkeep
├── docs/
│   ├── api.md
│   ├── model.md
│   └── adr/
│       └── 0001-operational-cost-floor.md
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

## Language Policy

- Codebase/API: English.
- Business-facing outputs: Spanish.
- Do not use `adquisition`.
- English term: `Acquisition`.
- Spanish output label: `Adquisición`.

Preserve Spanish column/report labels where they are business-facing, e.g. `Ingresos`, `Caja`, `EBITDA`, `Adq_clientes` if needed for continuity.

## Domain Decisions

See `CONTEXT.md` for glossary. Key decisions:

- Planning periods are monthly only.
- Annual values are aggregations, not separate model periods.
- Fixed acquisition period is exactly 12 months.
- Total horizon `H` is configurable and must be greater than 12.
- First refactor validates `H >= 14` because smoothing constraints reference months 13 and 14.
- Model is multi-service by service index `s`.
- Acquisition, active client pool, recurrent sales, new sales, total services sold, churn, prices, and costs are calculated per service.
- Repurchase timing is preprocessed as a binary parameter, not a solver decision variable.
- Churn is service-specific and exogenous.
- Acquisition creates exactly one new sale for same service and period.
- Service price is constant in first refactor, but schema should allow future period-specific pricing.
- Repurchase rate `alpha` applies only to eligible surviving customers in a service cohort during a repurchase window.

## Optimization Decisions

- Keep full-horizon MILP for first refactor.
- Months 1–12 are fixed from `A_base`.
- Months 13–H are optimized.
- Keep interface boundaries open so later optimization can start from Stage 1 ending state.
- Objective remains discounted EBITDA for first refactor.
- Liquidity policy is configurable. Default `none` to preserve current behavior.
- Commercial staffing is monotonic across month 12→13 and afterward.
- Commercial productivity lag is configurable. Default lag = 0, meaning same-period productivity.
- Solver abstraction is light: PuLP/CBC only implemented, but config should include solver name, time limit, verbosity.

## Operational Cost Methodology

Operational cost uses floor/max semantics:

```text
Cost_op[s,t] >= c_u[s] * Q[s,t]
Cost_op[s,t] >= c_min[s] * m_op[s,t]
```

Effective cost is max(variable usage cost, capacity-step floor), not fixed plus variable.

This is deliberate methodology. See `docs/adr/0001-operational-cost-floor.md`.

## Pipeline Stages

### Stage 1: Financial model

Create deterministic cashflow model for fixed acquisition period:

- first 12 months from `A_base`
- cohort survival
- new sales
- recurring sales
- total services sold
- revenue
- CAC
- operational cost
- EBITDA
- cash

This stage should not require solver feasibility.

### Stage 2: Growth optimization

Build/solve full-horizon MILP initially:

- fixed months 1–12
- optimized months 13–H
- preserve current behavior first
- apply documented fixes/decisions only when explicit in `PLAN.md`

### Stage 3: Valuation and unit economics

Port:

- DCF valuation
- multiples valuation
- unit economics

### Stage 4: Financial report generation

First reporting artifact should include:

- Markdown report
- dashboard PNG
- core CSV outputs

Visualization belongs to reporting, not core model logic.

## API and CLI

Support both:

### Python API

Notebook/Colab friendly. No file writes unless `output_dir` passed.

Expected shape:

```python
from adventure_capital.config import default_config, load_config
from adventure_capital.pipeline import run_pipeline

config = default_config()
result = run_pipeline(config)

config = load_config("configs/base.yaml")
result = run_pipeline(config, output_dir="outputs/experiment-1")
```

Documented in `docs/api.md`.

### CLI

Product-facing. Writes artifacts by default.

Expected command:

```bash
uv run adventure-capital run --config configs/base.yaml --output outputs/
```

If `--output` omitted, CLI writes to timestamped directory under `outputs/`.

## Config Policy

- YAML primary config source: `configs/base.yaml`.
- Python `default_config()` for tests/examples/notebooks.
- Use simple validation first: plain dictionaries/dataclasses and explicit validation functions.
- Do not add Pydantic yet.
- Defer Pydantic until config complexity or UX demands it.

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

## Implementation Rules

- Remove Colab magic.
- Remove import-time execution.
- Preserve current behavior before improving model.
- Keep pure calculations separate from printing/reporting.
- Keep solver-specific code in `model.py`.
- Keep report generation in `reporting.py`.
- Keep mathematical formulation in `docs/model.md`.
- Do not bury domain decisions only in code comments.
- Update `PLAN.md` when scope/architecture changes.
- Update `CONTEXT.md` when domain language is clarified.
- Create ADR only for hard-to-reverse, surprising, trade-off decisions.

## First Implementation Sequence

1. Create `pyproject.toml`, `.python-version`, package skeleton, `configs/base.yaml`, `outputs/.gitkeep`.
2. Port base config to `config.py` and YAML.
3. Implement config validation.
4. Port instance preprocessing to `instance.py`.
5. Extract deterministic fixed-period cashflow model to `financial_model.py`.
6. Port full-horizon MILP to `model.py`.
7. Port result extraction to `results.py`.
8. Port DCF/multiples to `valuation.py`.
9. Port unit economics to `unit_economics.py`.
10. Port dashboard + Markdown/CSV report generation to `reporting.py`.
11. Implement `pipeline.py` orchestration.
12. Implement `cli.py`.
13. Add smoke tests.
14. Update README.

## Test Expectations

Minimum tests:

- Config loads and validates.
- `H >= 14` validation enforced.
- Instance generation produces horizon, service count, base acquisition, churn, survival, recurrence, discount factors.
- Fixed-period financial model produces 12 monthly cashflow rows from `A_base`.
- Solver smoke test runs with known status and no exception.
- Results dataframe non-empty when solver produces solution.
- DCF returns expected keys and finite numeric values.

Regression metrics to compare before/after migration:

- solver status
- total acquisition
- total revenue
- total EBITDA
- final cash
- DCF VAN

## Known Legacy Code Issues

- `!pip install pulp --quiet` invalid in normal Python.
- Top-level code executes model multiple times.
- `generar_visualizaciones()` defined twice.
- Liquidity constraints are commented out; replace with explicit configurable policy.
- Commercial staffing monotonicity currently starts after month 13; desired behavior includes transition from month 12 to month 13.
- Some formal notebook text differs from active code; trust active code plus documented decisions.

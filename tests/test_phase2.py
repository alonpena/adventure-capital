from adventure_capital.config import default_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import solve_growth_plan
from adventure_capital.pipeline import run_pipeline
from adventure_capital.results import extract_results


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_growth_model_solver_smoke():
    instance = generate_instance(_fast_config())
    solution = solve_growth_plan(instance, time_limit=30)
    assert solution["status"] in {"Optimal", "Not Solved", "Infeasible", "Unbounded"}
    assert solution["problem"] is not None
    assert solution["variables"]


def test_results_dataframe_non_empty_when_solution_exists():
    instance = generate_instance(_fast_config())
    solution = solve_growth_plan(instance, time_limit=30)
    df = extract_results(instance, solution)
    assert len(df) == 14
    assert {"Adq_clientes", "Ingresos", "EBITDA", "Caja"}.issubset(df.columns)
    assert df.loc[df["t"] <= 12, "Adq_clientes"].tolist() == [2, 2, 3, 4, 5, 5, 6, 7, 8, 8, 9, 10]


def test_pipeline_runs_phase2_outputs(tmp_path):
    result = run_pipeline(_fast_config(), output_dir=str(tmp_path))
    assert result["solution"]["status"] == "Optimal"
    assert len(result["optimized_results"]) == 14
    assert (tmp_path / "fixed_cashflow.csv").exists()
    assert (tmp_path / "optimized_results.csv").exists()

"""Phase 3 — CAC cost-component aggregation and post-solve traceability."""

import numpy as np
import pytest

from adventure_capital.config import default_config, load_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import solve_growth_plan
from adventure_capital.results import _safe_div, extract_results

# CBC reports component variables within its feasibility tolerance (~1e-3).
SOLVER_TOL = 1e-2


def _solve(path):
    instance = generate_instance(load_config(path))
    solution = solve_growth_plan(instance)
    return instance, solution, extract_results(instance, solution)


def _fast(config):
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_component_sum_identity_legacy():
    _, _, df = _solve("configs/demo-complex.yaml")
    components = df["salesforce_cac_cost"] + df["third_party_cost"]
    assert (components - df["total_acquisition_cost"]).abs().max() <= SOLVER_TOL
    assert (df["total_acquisition_cost"] - df["CAC"]).abs().max() == pytest.approx(0.0, abs=1e-9)


def test_component_sum_identity_mixed():
    _, _, df = _solve("configs/demo-mixed-channels.yaml")
    components = df["salesforce_cac_cost"] + df["advertising_cac_cost"] + df["third_party_cost"]
    assert (components - df["total_acquisition_cost"]).abs().max() <= SOLVER_TOL
    assert (df["total_acquisition_cost"] - df["CAC"]).abs().max() == pytest.approx(0.0, abs=1e-9)


def test_period_cac_per_user_formula():
    _, _, df = _solve("configs/demo-mixed-channels.yaml")
    expected = df["total_acquisition_cost"] / df["new_customers"]
    assert (df["period_cac_per_user"] - expected).abs().max() == pytest.approx(0.0, abs=1e-9)


def test_cumulative_cac_per_user_formula():
    _, _, df = _solve("configs/demo-mixed-channels.yaml")
    expected = df["total_acquisition_cost"].cumsum() / df["new_customers"].cumsum()
    assert (df["cumulative_cac_per_user"] - expected).abs().max() == pytest.approx(0.0, abs=1e-9)


def test_safe_div_zero_customers_returns_nan():
    out = _safe_div([100.0, 50.0, 0.0], [0.0, 5.0, 0.0])
    assert np.isnan(out[0])
    assert out[1] == pytest.approx(10.0)
    assert np.isnan(out[2])


def test_legacy_columns_preserved_and_new_added():
    _, _, df = _solve("configs/demo-complex.yaml")
    assert {"CAC", "Adq_clientes", "Ingresos", "EBITDA", "Caja"}.issubset(df.columns)
    assert {
        "new_customers",
        "salesforce_cac_cost",
        "third_party_cost",
        "total_acquisition_cost",
        "period_cac_per_user",
        "cumulative_cac_per_user",
    }.issubset(df.columns)


def test_third_party_cost_wired():
    config = _fast(default_config())
    config["channels"] = {
        "salesforce": {"active": True, "min_share": 0.0, "max_share": 1.0},
        "advertising": {"active": False, "min_share": 0.0, "max_share": 1.0},
        "third_party": {
            "active": True,
            "commission": 0.1,
            "min_share": 0.2,
            "max_share": 0.5,
        },
    }
    instance = generate_instance(config)
    solution = solve_growth_plan(instance)
    assert solution["status"] == "Optimal"
    df = extract_results(instance, solution)
    ticket = instance["servicios"][0]["ticket"]
    expected = 0.1 * ticket * df["A_third_party"]
    assert (df["third_party_cost"] - expected).abs().max() <= SOLVER_TOL
    # min_share forces non-zero third-party acquisition, so the cost is actually wired.
    assert df["A_third_party"].sum() > 0
    assert df["third_party_cost"].sum() > 0


def test_no_cac_ratio_in_milp():
    instance, solution, _ = _solve("configs/demo-mixed-channels.yaml")
    keys = set(solution["variables"].keys())
    assert "period_cac_per_user" not in keys
    assert "cumulative_cac_per_user" not in keys
    # Only cost components are decision variables.
    assert {"salesforce_cac_cost", "total_acquisition_cost"}.issubset(keys)

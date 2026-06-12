"""Phase 1 — logarithmic acquisition ceiling tests."""

import math

import pytest

from adventure_capital.config import default_config, load_config, validate_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import solve_growth_plan
from adventure_capital.results import extract_results
from adventure_capital.valuation import calculate_dcf


def _services(df):
    return [c[2:] for c in df.columns if c.startswith("A_") and c != "Adq_clientes"]


def _solve(config_path):
    config = load_config(config_path)
    instance = generate_instance(config)
    solution = solve_growth_plan(instance)
    df = extract_results(instance, solution)
    return config, instance, solution, df


def test_ceiling_disabled_regression():
    """demo-complex.yaml has no ceiling block: behaves exactly as baseline."""
    config = load_config("configs/demo-complex.yaml")
    instance = generate_instance(config)
    assert instance["log_ceiling"] == {}
    solution = solve_growth_plan(instance)
    assert solution["status"] == "Optimal"
    df = extract_results(instance, solution)
    # No diagnostic columns when ceiling inactive.
    assert "Log_ceiling" not in df.columns
    assert "Log_ceiling_slack" not in df.columns


def test_ceiling_formula_monotonic():
    """Marginal ceiling decreases month over month; cumulative reaches S_target - S_0."""
    config = default_config()
    config["acquisition_ceiling"] = {
        "enabled": True,
        "target_stock_multiplier": 2.0,
        "slack": 0.0,
    }
    instance = generate_instance(config)
    ceiling = instance["log_ceiling"]
    H = instance["H"]
    months = list(range(13, H + 1))
    assert set(ceiling.keys()) == set(months)

    for t in months[:-1]:
        assert ceiling[t] > ceiling[t + 1], f"ceiling not decreasing at t={t}"

    S_0 = sum(instance["A_base"][(s, t)] for s in range(instance["S"]) for t in instance["T_base"])
    S_target = S_0 * 2.0
    assert sum(ceiling.values()) == pytest.approx(S_target - S_0, rel=1e-9)


def test_year1_immutable_with_ceiling():
    """Months 1-12 acquisition stays exactly A_base even with ceiling active."""
    config, instance, solution, df = _solve("configs/demo-complex-ceiling.yaml")
    assert solution["status"] == "Optimal"
    for s, service in enumerate(instance["servicios"]):
        name = service["nombre"]
        for t in range(1, 13):
            assert df.loc[df["t"] == t, f"A_{name}"].iloc[0] == pytest.approx(
                instance["A_base"][(s, t)]
            )


def test_ceiling_binds():
    """Total acquisition never exceeds ceiling * (1 + slack) for t >= 13."""
    config, instance, solution, df = _solve("configs/demo-complex-ceiling.yaml")
    ceiling = instance["log_ceiling"]
    slack = instance["ceiling_slack"]
    for t, value in ceiling.items():
        total = df.loc[df["t"] == t, "Adq_clientes"].iloc[0]
        assert total <= value * (1 + slack) + 1e-6, f"ceiling breached at t={t}"


def test_ceiling_lowers_ev():
    """A tight ceiling cannot raise Enterprise Value vs. no ceiling."""
    _, inst_open, _, df_open = _solve("configs/demo-complex.yaml")
    _, inst_tight, _, df_tight = _solve("configs/demo-ceiling-tight.yaml")
    ev_open = calculate_dcf(df_open, inst_open)["VAN"]
    ev_tight = calculate_dcf(df_tight, inst_tight)["VAN"]
    assert ev_tight <= ev_open + 1e-6


def test_ceiling_tight_feasible():
    """The stress config remains solvable."""
    _, _, solution, _ = _solve("configs/demo-ceiling-tight.yaml")
    assert solution["status"] == "Optimal"


def test_config_validation():
    """Validator enforces ceiling domain rules only when enabled."""
    bad_mult = default_config()
    bad_mult["acquisition_ceiling"] = {"enabled": True, "target_stock_multiplier": 1.0, "slack": 0.1}
    with pytest.raises(ValueError, match="target_stock_multiplier"):
        validate_config(bad_mult)

    bad_slack = default_config()
    bad_slack["acquisition_ceiling"] = {"enabled": True, "target_stock_multiplier": 2.0, "slack": -0.1}
    with pytest.raises(ValueError, match="slack"):
        validate_config(bad_slack)

    disabled = default_config()
    disabled["acquisition_ceiling"] = {"enabled": False}
    validate_config(disabled)  # no extra fields required when disabled

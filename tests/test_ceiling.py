"""Phase 1 — logarithmic acquisition ceiling tests."""

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


def test_ceiling_default_on_when_block_absent():
    """ADR 0010: the log growth law is default-on. A config with no ceiling block
    still gets the saturation ceiling (no moving-average smoothing fallback)."""
    config = load_config("configs/demo-complex.yaml")
    assert "acquisition_ceiling" not in config  # no explicit block
    instance = generate_instance(config)
    assert instance["log_ceiling"] != {}
    H = instance["H"]
    assert set(instance["log_ceiling"].keys()) == set(range(13, H + 1))
    solution = solve_growth_plan(instance)
    assert solution["status"] == "Optimal"


def test_ceiling_explicit_disable_opts_out():
    """Only an explicit enabled: false removes the growth ceiling (mechanism check).
    Solvability then depends on other bounds — see the unbounded test below."""
    config = load_config("configs/demo-complex.yaml")
    enabled = generate_instance(config)
    assert enabled["log_ceiling"] != {}  # default-on

    config["acquisition_ceiling"] = {"enabled": False}
    disabled = generate_instance(config)
    assert disabled["log_ceiling"] == {}
    assert disabled["ceiling_slack"] == 0.0


def test_disabled_ceiling_without_floor_is_unbounded():
    """ADR 0010 consequence: removing the smoothing law means the log ceiling (or a
    cash/capacity bound) is what keeps growth finite. Disabling it with no liquidity
    floor leaves acquisition unbounded — a deliberate, documented behavior."""
    config = load_config("configs/demo-complex.yaml")
    config["acquisition_ceiling"] = {"enabled": False}
    config["liquidity_policy"] = {"type": "none"}
    instance = generate_instance(config)
    solution = solve_growth_plan(instance)
    assert solution["status"] == "Unbounded"


def test_ceiling_targets_active_stock():
    """ADR 0010: the ceiling anchors the ACTIVE client stock. Acquiring at the ceiling
    every month (net of churn) drives the projected stock to multiplier x the
    end-of-year-1 active stock. Ceiling stays non-negative (churn replacement included)."""
    config = default_config()
    config["acquisition_ceiling"] = {
        "enabled": True,
        "target_stock_multiplier": 3.0,
        "slack": 0.0,
    }
    instance = generate_instance(config)
    ceiling = instance["log_ceiling"]
    H = instance["H"]
    S = instance["S"]
    months = list(range(13, H + 1))
    assert set(ceiling.keys()) == set(months)
    assert all(v >= 0.0 for v in ceiling.values())

    # End-of-year-1 active stock (net of churn), aggregated over services.
    C_0 = sum(
        instance["phi"][(s, c, 12)] * instance["A_base"][(s, c)]
        for s in range(S)
        for c in instance["T_base"]
    )

    # Reconstruct net stock acquiring exactly at the ceiling each month.
    stock = C_0
    for t in months:
        churn_agg = sum(instance["churn_mensual"][(s, t)] for s in range(S)) / S
        stock = stock * (1 - churn_agg) + ceiling[t]
    assert stock == pytest.approx(C_0 * 3.0, rel=1e-9)


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

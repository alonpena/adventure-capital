"""Model-class behavior tests (closing audit, 2026-07-05).

These assert *dynamics*, not instance numbers: monotonicity in ticket, value
of recurrence, churn direction, CAC cost direction, VC neutrality on the
operating plan, and the ability of the salesforce to grow in the projection
months. Each solve uses a small horizon (H=14) so the suite stays fast.
"""

from __future__ import annotations

import pytest

from adventure_capital.config import default_config, validate_config
from adventure_capital.pipeline import run_pipeline


def _fast_config(**overrides) -> dict:
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    for key, value in overrides.items():
        config[key] = value
    return config


def _solve(config: dict) -> dict:
    result = run_pipeline(config, baseline_only=True)
    return {
        "van": float(result["dcf"]["VAN"]),
        "optimized": result["optimized_results"],
    }


@pytest.fixture(scope="module")
def base_solution() -> dict:
    return _solve(_fast_config())


def test_van_monotonic_in_ticket(base_solution) -> None:
    config = _fast_config()
    config["servicios"][0]["ticket"] = config["servicios"][0]["ticket"] * 1.3
    richer = _solve(config)
    assert richer["van"] > base_solution["van"]


def test_recurrence_adds_value(base_solution) -> None:
    config = _fast_config()
    config["servicios"][0]["alpha"] = 0.0  # no repurchases at all
    no_recurrence = _solve(config)
    assert no_recurrence["van"] < base_solution["van"]


def test_higher_churn_destroys_value(base_solution) -> None:
    config = _fast_config()
    config["servicios"][0]["churn_anual"] = [0.9, 0.9, 0.9]
    churny = _solve(config)
    assert churny["van"] < base_solution["van"]


def test_higher_cac_costs_reduce_value(base_solution) -> None:
    config = _fast_config()
    config["rem_v"] = config["rem_v"] * 2.0
    config["com_v"] = config["com_v"] * 2.0
    expensive = _solve(config)
    assert expensive["van"] < base_solution["van"]


def test_vc_does_not_improve_the_operating_plan(base_solution) -> None:
    """While the cash floor is slack, extra VC must not change the plan;
    the VAN shifts by exactly -delta_VC (capital is not operating value)."""
    config = _fast_config()
    delta = 50_000.0
    config["VC"] = float(config["VC"]) + delta
    richer_ticket = _solve(config)
    # Same operating plan -> same revenue trajectory.
    base_rev = base_solution["optimized"]["Ingresos"].sum()
    new_rev = richer_ticket["optimized"]["Ingresos"].sum()
    assert abs(base_rev - new_rev) / max(base_rev, 1.0) < 5e-3
    # VAN moves by -delta (linear in VC).
    assert richer_ticket["van"] == pytest.approx(base_solution["van"] - delta, rel=1e-3)


def test_sellers_and_leaders_can_grow_in_projection() -> None:
    """Months >= 13 must allow hiring above the consensuated year-1 headcount
    when the growth brake leaves room (regression for the jump-then-flat /
    stagnation diagnosis)."""
    config = _fast_config()
    config["acquisition_ceiling"] = {
        "enabled": True,
        "target_stock_multiplier": 8.0,
        "slack": 0.15,
    }
    solved = _solve(config)
    df = solved["optimized"]
    v12 = float(df.loc[df["t"] == 12, "Vendedores"].iloc[0])
    v13 = float(df.loc[df["t"] == 13, "Vendedores"].iloc[0])
    l12 = float(df.loc[df["t"] == 12, "Lideres"].iloc[0])
    l13 = float(df.loc[df["t"] == 13, "Lideres"].iloc[0])
    assert v13 > v12, "sellers frozen at the consensuated headcount"
    assert l13 >= l12
    # Leaders must scale with sellers (span of control).
    assert v13 <= config["sup"] * l13 + 1e-9


def test_invalid_channel_minimums_fail_validation() -> None:
    config = default_config()
    config["channels"] = {
        "salesforce": {"active": True, "min_share": 0.7, "max_share": 1.0},
        "advertising": {
            "active": True,
            "I_min": 0, "I_max": 1000, "A_min": 0, "A_max": 10, "A_ad_cap": 10,
            "min_share": 0.6, "max_share": 1.0,
        },
        "third_party": {"active": False, "commission": 0.0, "min_share": 0.0, "max_share": 1.0},
    }
    with pytest.raises(ValueError, match="min_share"):
        validate_config(config)


def test_insufficient_channel_maximums_fail_validation() -> None:
    config = default_config()
    config["channels"] = {
        "salesforce": {"active": True, "min_share": 0.0, "max_share": 0.4},
        "advertising": {
            "active": True,
            "I_min": 0, "I_max": 1000, "A_min": 0, "A_max": 10, "A_ad_cap": 10,
            "min_share": 0.0, "max_share": 0.3,
        },
        "third_party": {"active": False, "commission": 0.0, "min_share": 0.0, "max_share": 1.0},
    }
    with pytest.raises(ValueError, match="max_share"):
        validate_config(config)

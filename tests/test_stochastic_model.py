"""SAA channel-parity + CVaR model tests (small samples so CBC stays fast)."""

from __future__ import annotations

import pulp
import pytest

from adventure_capital.config import default_config
from adventure_capital.stochastic.model import build_saa_model, solve_saa_model
from adventure_capital.stochastic.scenarios import generate_scenarios


def _sf_config() -> dict:
    config = default_config()
    config["H"] = 14
    config["stochastic"] = {"saa_scenario_count": 6, "seed_saa": 7}
    return config


def _three_channel_config() -> dict:
    config = default_config()
    config["H"] = 14
    # Force a genuine channel mix: salesforce capped, ad + third-party floored.
    config["channels"]["salesforce"].update({"min_share": 0.0, "max_share": 0.6})
    config["channels"]["advertising"] = {
        "active": True,
        "I_min": 0,
        "I_max": 5000,
        "A_min": 0,
        "A_max": 40,
        "A_ad_cap": 50,
        "min_share": 0.2,
        "max_share": 0.5,
    }
    config["channels"]["third_party"] = {
        "active": True,
        "commission": 0.1,
        "min_share": 0.2,
        "max_share": 0.4,
    }
    config["stochastic"] = {"saa_scenario_count": 5, "seed_saa": 3}
    return config


def test_saa_solves_salesforce_only() -> None:
    config = _sf_config()
    bundle = build_saa_model(config, generate_scenarios(config))
    solution = solve_saa_model(bundle, time_limit=90)
    assert solution["status"] == "Optimal"
    assert solution["objective"] == "cvar_van"


def test_cvar_is_finite_and_conservative() -> None:
    config = _sf_config()
    bundle = build_saa_model(config, generate_scenarios(config))
    solution = solve_saa_model(bundle, time_limit=90)
    assert solution["cvar_van"] is not None
    assert solution["expected_van"] is not None
    # CVaR of the downside tail cannot exceed the mean.
    assert solution["cvar_van"] <= solution["expected_van"] + 1e-6


def test_strategy_exposes_channel_plans() -> None:
    config = _sf_config()
    bundle = build_saa_model(config, generate_scenarios(config))
    solution = solve_saa_model(bundle, time_limit=90)
    strategy = solution["strategy"]
    for key in ("A_sf_plan", "A_ad_plan", "A_tp_plan", "A_plan", "V", "L", "I_ad"):
        assert key in strategy
    # No legacy single-channel acquisition key.
    assert "A" not in strategy


def test_three_channels_active_and_used() -> None:
    config = _three_channel_config()
    bundle = build_saa_model(config, generate_scenarios(config))
    solution = solve_saa_model(bundle, time_limit=120)
    assert solution["status"] == "Optimal"
    strategy = solution["strategy"]
    assert sum(strategy["A_ad_plan"].values()) > 0.0
    assert sum(strategy["A_tp_plan"].values()) > 0.0
    # Advertising spend appears only from month 13 onward.
    assert all(v == pytest.approx(0.0) for t, v in strategy["I_ad"].items() if t <= 12)
    assert any(v > 1e-6 for t, v in strategy["I_ad"].items() if t >= 13)


def test_van_varies_by_scenario() -> None:
    # Efficiency multipliers must make realized outcomes scenario-dependent.
    config = _sf_config()
    bundle = build_saa_model(config, generate_scenarios(config))
    solve_saa_model(bundle, time_limit=90)
    van_values = [pulp.value(var) for var in bundle["variables"]["VAN"].values()]
    assert max(van_values) - min(van_values) > 1e-3

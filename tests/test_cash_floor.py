"""Phase 4 — working-capital cash floor and financing-gap diagnostic."""

import copy

import pytest

from adventure_capital.config import load_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import (
    build_model,
    diagnose_financing_gap,
    solve_growth_plan,
    solve_with_working_capital,
)
from adventure_capital.results import extract_results

WC_CONFIG = "configs/demo-working-capital.yaml"


def _instance(vc=None):
    config = load_config(WC_CONFIG)
    if vc is not None:
        config = copy.deepcopy(config)
        config["VC"] = vc
    return config, generate_instance(config)


def test_cash_floor_feasible():
    config, instance = _instance()
    result = solve_with_working_capital(instance)
    assert result["feasible"] is True
    assert result["min_cash_balance"] >= -float(instance["VC"]) - 1e-6
    assert result["financing_gap_usd"] == 0.0


def test_cash_floor_binding():
    # VC tuned just above the fixed-period cumulative-EBITDA trough so the floor binds.
    vc = 53700
    config, instance = _instance(vc=vc)
    result = solve_with_working_capital(instance)
    assert result["feasible"] is True
    min_cash = result["min_cash_balance"]
    assert min_cash >= -vc - 1e-6              # floor respected
    assert min_cash <= -vc + 1000.0            # cash actually touches the floor


def test_cash_floor_infeasible_diagnostic():
    # VC below the fixed-period trough: year 1 cannot be funded -> main infeasible.
    config, instance = _instance(vc=40000)
    result = solve_with_working_capital(instance)
    assert result["feasible"] is False
    assert result["financing_gap_usd"] > 0
    assert result["first_breach_month"] is not None
    assert result["total_gap"] > 0


def test_cash_identity():
    config, instance = _instance()
    result = solve_with_working_capital(instance)
    assert result["feasible"] is True
    df = extract_results(instance, result["solution"])
    caja_final = float(df["Caja"].iloc[-1])
    expected = float(instance["VC"]) + float(df["EBITDA"].sum())
    assert caja_final == pytest.approx(expected, rel=1e-6)


def test_legacy_no_working_capital():
    # A config without a working_capital block keeps the Phase 3 liquidity behavior.
    config = load_config("configs/demo-complex.yaml")
    instance = generate_instance(config)
    assert instance["parametros"].get("working_capital", {}).get("enabled", False) is False
    solution = solve_growth_plan(instance)
    assert solution["status"] == "Optimal"
    # No shortfall variables exist in the legacy path.
    assert solution["variables"]["cash_shortfall"] == {}
    df = extract_results(instance, solution)
    assert df["Caja"].min() == pytest.approx(2620.0, abs=1.0)


def test_diagnostic_does_not_modify_main_model():
    config, instance = _instance(vc=40000)
    main = build_model(instance)
    constraints_before = len(main["problem"].constraints)
    sense_before = main["problem"].sense
    assert main["variables"]["cash_shortfall"] == {}  # hard floor, no shortfall vars

    diagnostic = diagnose_financing_gap(instance)
    assert diagnostic["feasible"] is False

    # The main model object is untouched by the diagnostic build/solve.
    assert len(main["problem"].constraints) == constraints_before
    assert main["problem"].sense == sense_before
    assert main["variables"]["cash_shortfall"] == {}

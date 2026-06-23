"""Phase 4 — working-capital cash floor and financing-gap diagnostic."""

import copy

import pytest

from adventure_capital.config import load_config
from adventure_capital.instance import generate_instance
from adventure_capital.due_diligence.workflow import run_due_diligence
from adventure_capital.model import (
    build_model,
    diagnose_financing_gap,
    solve_growth_plan,
    solve_with_working_capital,
)
from adventure_capital.pipeline import run_pipeline
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


def test_pipeline_continues_with_diagnostic_outputs(tmp_path):
    config = load_config(WC_CONFIG)
    config["VC"] = 40000
    config["solver"]["time_limit"] = 60

    result = run_pipeline(config, output_dir=str(tmp_path))

    assert result["solution"]["status"] == "Infeasible"
    diagnostic = result["working_capital_diagnostic"]
    assert diagnostic["feasible"] is False
    assert diagnostic["financing_gap_usd"] > 0
    assert result["diagnostic_solution"]["status"] == "Optimal"
    assert (tmp_path / "optimized_results.csv").exists()
    assert "diagnostic_cash_shortfall" in result["optimized_results"].columns


def test_due_diligence_receives_financing_gap_alert(tmp_path):
    config = load_config(WC_CONFIG)
    config["VC"] = 40000
    config["solver"]["time_limit"] = 60

    result = run_due_diligence(config, output_dir=tmp_path)
    verdict = result["verdict"]

    # The financing gap is a minor (fixable) signal, never a structural block.
    assert verdict.verdict != "rejected_for_stochastic"
    dd11 = next(f for f in verdict.findings if f.id == "DD11")
    assert dd11.severity_class == "minor"
    assert "additional financing" in dd11.message
    assert verdict.liquidity_diagnostic["financing_gap_usd"] > 0
    assert "first breach" in verdict.liquidity_diagnostic["financing_gap_alert"]

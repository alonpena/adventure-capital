import json
from pathlib import Path

import pandas as pd

from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_baseline_run_builds_deterministic_view(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path), baseline_only=True)
    root = tmp_path / "postprocessed_results"

    # Deterministic folders always present.
    growth = root / "accelerated_growth_plan"
    workbook = root / "valuation_workbook"
    assert growth.is_dir() and workbook.is_dir()

    growth_files = {
        "01_customer_flow.csv", "02_service_flow.csv", "03_revenue_flow.csv",
        "04_commercial_plan.csv", "05_operational_capacity.csv", "06_costs_and_cac.csv",
        "07_cash_and_working_capital.csv", "08_growth_plan_summary.json",
    }
    assert growth_files.issubset({p.name for p in growth.iterdir()})

    workbook_files = {
        "01_cashflow_detail.csv", "02_dcf_inputs.json", "03_dcf_calculation.csv",
        "04_terminal_value.json", "05_valuation_summary.json", "06_unit_economics_detail.csv",
        "07_formula_trace.json",
    }
    assert workbook_files.issubset({p.name for p in workbook.iterdir()})

    # Backward compatibility: flat canonical outputs still exist.
    assert (tmp_path / "optimized_results.csv").exists()
    assert (tmp_path / "valuation_summary.json").exists()


def test_view_is_derived_not_recomputed(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path), baseline_only=True)
    root = tmp_path / "postprocessed_results"

    # Workbook valuation_summary is a byte-for-byte copy of the canonical file.
    canonical = (tmp_path / "valuation_summary.json").read_text(encoding="utf-8")
    derived = (root / "valuation_workbook" / "05_valuation_summary.json").read_text(encoding="utf-8")
    assert canonical == derived

    # Customer-flow values match optimized_results (selection, not recompute).
    flat = pd.read_csv(tmp_path / "optimized_results.csv")
    view = pd.read_csv(root / "accelerated_growth_plan" / "01_customer_flow.csv")
    pd.testing.assert_series_equal(flat["Adq_clientes"], view["Adq_clientes"])

    manifest = _load_json(root / "postprocessed_manifest.json")
    assert manifest["is_canonical"] is False


def test_assessment_run_builds_dd_and_stochastic_view(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path), baseline_only=False)
    root = tmp_path / "postprocessed_results"

    dd = root / "due_diligence"
    assert dd.is_dir()
    assert {"due_diligence_assessment.json", "due_diligence_flags.csv",
            "recommended_levers.json"}.issubset({p.name for p in dd.iterdir()})

    assessment = _load_json(dd / "due_diligence_assessment.json")
    assert {"verdict", "allows_stochastic", "valuation_mode", "findings"}.issubset(assessment)

    levers = _load_json(dd / "recommended_levers.json")
    assert "levers" in levers

    # Stochastic folder only when stochastic ran.
    stoch = root / "stochastic_assessment"
    if stoch.is_dir():
        status = _load_json(stoch / "stochastic_method_status.json")
        assert status["is_robust_optimization"] is False
        assert status["lhs_implemented"] is True
        assert status["method"] == "sample_average_approximation"
        assert status["objective"] == "cvar_van"


def test_method_status_does_not_overclaim(tmp_path):
    from adventure_capital.postprocess import _stochastic_method_status

    status = _stochastic_method_status()
    assert status["is_robust_optimization"] is False
    assert status["lhs_implemented"] is True
    assert status["saa_implemented"] is True
    assert "robust" not in status["method"]

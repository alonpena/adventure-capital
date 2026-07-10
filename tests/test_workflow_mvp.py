"""Tests for the M4 fixes + CLI workflow MVP + M5 simple report."""

from __future__ import annotations

import json

import pandas as pd

from adventure_capital import workflow_registry as reg
from adventure_capital.simple_report import REPORT_FILENAME, build_simple_report
from adventure_capital.stochastic.defaults import M4_DEFAULTS
from adventure_capital.stochastic.results import write_outputs


def test_m4_default_solver_time_limit_is_420():
    assert M4_DEFAULTS["solver_time_limit"] == 420


def _evaluation_frame(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "scenario": [f"eval_{i:04d}" for i in range(n)],
            "probability": [1.0 / n] * n,
            "VAN": [1000.0 + i for i in range(n)],
            "funding_gap": [0.0] * n,
            "final_active_clients": [500.0] * n,
            "breakeven_month": [12] * n,
            "runway_month": [24] * n,
            "cash_below_floor": [0.0] * n,
            "cac_per_customer": [10.0] * n,
            "ltv_cac": [3.0] * n,
            "arpu": [50.0] * n,
            "arr": [600.0] * n,
        }
    )


def test_saa_solution_scenario_counts_separated(tmp_path):
    from adventure_capital.stochastic.results import summarize_distribution

    evaluation = _evaluation_frame(40)
    summary = summarize_distribution(evaluation, cvar_alpha=0.05)
    solution = {
        "status": "Optimal",
        "objective": "cvar_van",
        "cvar_alpha": 0.05,
        "cvar_van": 1000.0,
        "expected_van": 1020.0,
        "strategy": {k: {} for k in ("V", "L", "I_ad", "A_sf_plan", "A_ad_plan", "A_tp_plan")},
    }
    write_outputs(
        evaluation,
        summary,
        tmp_path,
        solution=solution,
        saa_scenario_count=6,
        evaluation_scenario_count=40,
    )
    saa = json.loads((tmp_path / "saa_solution.json").read_text())
    # scenario_count must mean SAA count (back-compat), not the ex-post count.
    assert saa["scenario_count"] == 6
    assert saa["saa_scenario_count"] == 6
    assert saa["evaluation_scenario_count"] == 40


def test_simple_report_degraded_when_no_artifacts(tmp_path):
    path = build_simple_report(tmp_path)
    assert path.name == REPORT_FILENAME
    html = path.read_text()
    assert "no se ejecutó" in html  # M4 status note
    assert "no disponible" in html  # missing M1/M2/M3 artifacts


def test_simple_report_renders_present_artifacts(tmp_path):
    (tmp_path / "growth_plan_summary.json").write_text(
        json.dumps({"solver_status": "Optimal", "total_ebitda": 5000.0, "final_cash": 1000.0,
                    "total_acquisition": 2000.0, "enabled_channels": ["salesforce"]})
    )
    (tmp_path / "valuation_summary.json").write_text(
        json.dumps({"method": "dcf", "van": 1234.0, "vc_invested": 500.0})
    )
    (tmp_path / "due_diligence_report.json").write_text(
        json.dumps({"verdict": "passed", "allows_stochastic": True, "valuation_mode": "final"})
    )
    pd.DataFrame([{"n_scenarios": 1000, "expected_van": 1500.0, "cvar_5": 900.0,
                   "van_p50": 1400.0}]).to_csv(tmp_path / "stochastic_summary.csv", index=False)
    html = build_simple_report(tmp_path).read_text()
    assert "USD 1,234" in html  # VAN
    assert "USD 1,500" in html  # expected VAN
    assert "passed" in html


def test_simple_report_formats_recommendation_dicts(tmp_path):
    (tmp_path / "due_diligence_report.json").write_text(
        json.dumps(
            {
                "verdict": "requires_minor_adjustment",
                "allows_stochastic": True,
                "adjustment_recommendations": [
                    {"id": "DD07", "severity_class": "warning", "recommendation": "Aumentar VC."}
                ],
            }
        )
    )
    html = build_simple_report(tmp_path).read_text()
    assert "Aumentar VC." in html
    assert "DD07" not in html  # no ID leaked
    assert "severity_class" not in html  # no raw dict leaked


def test_registry_instance_roundtrip(tmp_path):
    config = {"servicios": [], "stochastic": {"saa_scenario_count": 5}}
    meta = reg.create_instance(config, name="Caso test", config_source="x.yaml", root=tmp_path)
    assert meta["id"].startswith("inst_")
    listing = reg.list_instances(root=tmp_path)
    assert any(m["id"] == meta["id"] for m in listing)
    got = reg.get_instance(meta["id"], root=tmp_path)
    assert got["name"] == "Caso test"
    loaded = reg.load_instance_config(meta["id"], root=tmp_path)
    assert loaded["stochastic"]["saa_scenario_count"] == 5

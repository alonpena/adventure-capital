"""Smoke tests for the iterative Due Diligence workflow.

Covers the 5-verdict taxonomy, decision fields, liquidity diagnostic, the
structural short-circuit, and the full assess -> stochastic orchestration.
"""

from __future__ import annotations

from pathlib import Path


from adventure_capital.config import default_config
from adventure_capital.due_diligence.report import (
    PASSED,
    PASSED_WITH_WARNINGS,
    REJECTED_FOR_STOCHASTIC,
    REQUIRES_MAJOR_ADJUSTMENT,
    REQUIRES_MINOR_ADJUSTMENT,
    aggregate_verdict,
    build_verdict,
)
from adventure_capital.due_diligence.rules import (
    MAJOR,
    MINOR,
    STRUCTURAL,
    WARNING,
    Finding,
    evaluate_pre_rules,
    resolve_thresholds,
)
from adventure_capital.due_diligence.workflow import run_assessment, run_due_diligence

ALL_VERDICTS = {
    PASSED,
    PASSED_WITH_WARNINGS,
    REQUIRES_MINOR_ADJUSTMENT,
    REQUIRES_MAJOR_ADJUSTMENT,
    REJECTED_FOR_STOCHASTIC,
}


def _fast_config() -> dict:
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_aggregate_verdict_precedence() -> None:
    f_struct = Finding("S", "s", STRUCTURAL, False, "")
    f_major = Finding("M", "m", MAJOR, False, "")
    f_minor = Finding("N", "n", MINOR, False, "")
    f_warn = Finding("W", "w", WARNING, False, "")
    assert aggregate_verdict([f_warn, f_minor, f_major, f_struct]) == REJECTED_FOR_STOCHASTIC
    assert aggregate_verdict([f_warn, f_minor, f_major]) == REQUIRES_MAJOR_ADJUSTMENT
    assert aggregate_verdict([f_warn, f_minor]) == REQUIRES_MINOR_ADJUSTMENT
    assert aggregate_verdict([f_warn]) == PASSED_WITH_WARNINGS
    assert aggregate_verdict([]) == PASSED


def test_decision_fields_per_verdict() -> None:
    # ADR 0009 gate: minor runs M4 in warning mode; major blocks M4.
    v_minor = build_verdict([Finding("DD07", "runway", MINOR, False, "neg cash")])
    assert v_minor.verdict == REQUIRES_MINOR_ADJUSTMENT
    assert v_minor.allows_stochastic is True
    assert v_minor.valuation_mode == "warning"
    assert v_minor.adjustment_level == "minor"
    assert v_minor.rerun_recommended is True

    v_major = build_verdict([Finding("DD10", "revenue_growth", MAJOR, False, "SME-like")])
    assert v_major.verdict == REQUIRES_MAJOR_ADJUSTMENT
    assert v_major.allows_stochastic is False
    assert v_major.valuation_mode == "none"
    assert v_major.adjustment_level == "major"

    v_struct = build_verdict([Finding("DD03", "financing_present", STRUCTURAL, False, "no VC")])
    assert v_struct.verdict == REJECTED_FOR_STOCHASTIC
    assert v_struct.allows_stochastic is False
    assert v_struct.valuation_mode == "none"
    assert v_struct.adjustment_level == "structural"
    assert v_struct.blocking_reasons == ["no VC"]


def test_m4_gate_policy_all_verdicts() -> None:
    # Canonical M4 (ADR 0009) runs only for passed / passed_with_warnings /
    # requires_minor_adjustment; major + structural block it.
    v_passed = build_verdict([])
    assert v_passed.verdict == PASSED
    assert v_passed.allows_stochastic is True
    assert v_passed.valuation_mode == "final"

    v_warn = build_verdict([Finding("DDW", "soft", WARNING, False, "")])
    assert v_warn.verdict == PASSED_WITH_WARNINGS
    assert v_warn.allows_stochastic is True
    assert v_warn.valuation_mode == "final"

    v_minor = build_verdict([Finding("DD07", "runway", MINOR, False, "")])
    assert v_minor.allows_stochastic is True
    assert v_minor.valuation_mode == "warning"

    v_major = build_verdict([Finding("DD10", "growth", MAJOR, False, "")])
    assert v_major.allows_stochastic is False
    assert v_major.valuation_mode == "none"

    v_struct = build_verdict([Finding("DD03", "financing", STRUCTURAL, False, "")])
    assert v_struct.allows_stochastic is False
    assert v_struct.valuation_mode == "none"


def test_negative_cash_does_not_block() -> None:
    # A minor liquidity finding must not block the stochastic run.
    v = build_verdict([Finding("DD07", "runway", MINOR, False, "cash negative month 10")])
    assert v.allows_stochastic is True
    assert v.verdict == REQUIRES_MINOR_ADJUSTMENT


def test_pre_rule_blocks_invalid_unit_economics() -> None:
    config = _fast_config()
    config["servicios"][0]["ticket"] = 10
    config["servicios"][0]["c_u"] = 30
    findings = evaluate_pre_rules(config, resolve_thresholds(None))
    dd02 = next(f for f in findings if f.id == "DD02")
    assert dd02.severity_class == STRUCTURAL
    assert not dd02.passed


def test_structural_pre_rule_short_circuits_model(tmp_path: Path) -> None:
    config = _fast_config()
    config["VC"] = 0  # DD03 structural: no financing
    result = run_due_diligence(config, output_dir=tmp_path)
    assert result["ran_model"] is False
    assert result["verdict"].verdict == REJECTED_FOR_STOCHASTIC
    assert not result["verdict"].allows_stochastic
    assert Path(result["artifacts"]["json"]).exists()
    assert Path(result["artifacts"]["markdown"]).exists()


def test_full_workflow_on_base_config(tmp_path: Path) -> None:
    config = _fast_config()
    result = run_due_diligence(config, output_dir=tmp_path)

    assert result["ran_model"] is True
    verdict = result["verdict"]
    assert verdict.verdict in ALL_VERDICTS
    assert (tmp_path / "due_diligence_report.md").exists()
    assert (tmp_path / "optimized_results.csv").exists()
    assert (tmp_path / "calibration_report.json").exists()
    assert verdict.calibration_verdict in {"PASS", "WARN", "FAIL"}
    # ADR 0009 gate: only passed / passed_with_warnings / requires_minor_adjustment run M4.
    assert verdict.allows_stochastic == (
        verdict.verdict in {PASSED, PASSED_WITH_WARNINGS, REQUIRES_MINOR_ADJUSTMENT}
    )
    # Liquidity diagnostic populated.
    diag = verdict.liquidity_diagnostic
    assert {"min_cash", "max_funding_gap", "breakeven_month", "cash_recovers"}.issubset(diag)


def test_run_assessment_chains_stochastic(tmp_path: Path) -> None:
    config = _fast_config()
    # Tiny stochastic sample so the chained run stays fast.
    config["stochastic"] = {
        "saa_scenario_count": 5,
        "seed_saa": 7,
        "evaluation_scenario_count": 30,
        "seed_eval": 99,
    }
    result = run_assessment(config, output_dir=tmp_path, stochastic_time_limit=60)

    verdict = result["verdict"]
    assert (tmp_path / "assessment_summary.json").exists()
    if verdict.allows_stochastic:
        assert result["stochastic"] is not None
        assert result["stochastic"]["ran"] is True
        assert result["stochastic"]["valuation_mode"] == verdict.valuation_mode
    else:
        assert result["stochastic"]["ran"] is False
        assert result["stochastic"]["valuation_mode"] == "none"
        expected_reason = {
            REQUIRES_MAJOR_ADJUSTMENT: "requires_major_adjustment_recalibration_required",
            REJECTED_FOR_STOCHASTIC: "rejected_for_stochastic",
        }.get(verdict.verdict)
        if expected_reason is not None:
            assert result["stochastic"]["reason"] == expected_reason

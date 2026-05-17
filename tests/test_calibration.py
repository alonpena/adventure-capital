"""End-to-end tests for the calibration gate."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from adventure_capital.calibration import run_calibration, write_calibration_report
from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


@pytest.fixture
def baseline_run(tmp_path: Path) -> Path:
    """Pipeline run against the smoke config."""
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    # Persist the config so the calibration gate can read it.
    import yaml
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(_fast_config()), encoding="utf-8")
    return tmp_path


def test_calibration_runs_against_baseline(baseline_run: Path) -> None:
    verdict = run_calibration(
        baseline_run,
        instance_path=baseline_run / "config.yaml",
        document_path="reports/valuation-base.yaml",
        thresholds_path="configs/calibration.yaml",
    )
    assert verdict.verdict in {"PASS", "WARN", "FAIL"}
    assert verdict.total_checks >= 10
    # Every result must declare an id and severity.
    for result in verdict.checks:
        assert result.id
        assert result.severity in {"error", "warning", "info"}


def test_calibration_writes_reports(baseline_run: Path) -> None:
    verdict = run_calibration(
        baseline_run,
        instance_path=baseline_run / "config.yaml",
        document_path="reports/valuation-base.yaml",
        thresholds_path="configs/calibration.yaml",
    )
    paths = write_calibration_report(verdict, baseline_run)
    assert paths["json"].exists() and paths["markdown"].exists()
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["verdict"] == verdict.verdict
    assert len(payload["checks"]) == verdict.total_checks


def test_cash_floor_failure_triggers_fail(baseline_run: Path) -> None:
    """Force a negative cash entry in optimized_results and check we get FAIL."""
    opt = pd.read_csv(baseline_run / "optimized_results.csv")
    opt.loc[opt.index[0], "Caja"] = -500_000.0
    opt.to_csv(baseline_run / "optimized_results.csv", index=False)
    verdict = run_calibration(
        baseline_run,
        instance_path=baseline_run / "config.yaml",
        document_path="reports/valuation-base.yaml",
        thresholds_path="configs/calibration.yaml",
    )
    assert verdict.verdict == "FAIL"
    c04 = next(c for c in verdict.checks if c.id == "C04")
    assert not c04.passed
    assert "Caja" in c04.message
    assert verdict.suggestions["C04"]


def test_disabled_check_is_skipped(tmp_path: Path, baseline_run: Path) -> None:
    """Disable C08 via custom thresholds and assert it is reported as skipped."""
    import yaml
    thresholds_path = tmp_path / "calibration_custom.yaml"
    thresholds_path.write_text(
        yaml.safe_dump({"C08_ltv_cac": {"enabled": False, "severity": "warning"}}),
        encoding="utf-8",
    )
    verdict = run_calibration(
        baseline_run,
        instance_path=baseline_run / "config.yaml",
        document_path="reports/valuation-base.yaml",
        thresholds_path=thresholds_path,
    )
    c08 = next(c for c in verdict.checks if c.id == "C08")
    assert c08.skipped is True


def test_verdict_aggregation_rule(baseline_run: Path) -> None:
    """If only warnings, verdict is WARN. With errors -> FAIL."""
    opt = pd.read_csv(baseline_run / "optimized_results.csv")
    opt.loc[opt.index[0], "Caja"] = -50_000.0
    opt.to_csv(baseline_run / "optimized_results.csv", index=False)
    v = run_calibration(
        baseline_run,
        instance_path=baseline_run / "config.yaml",
        document_path="reports/valuation-base.yaml",
        thresholds_path="configs/calibration.yaml",
    )
    assert v.errors >= 1
    assert v.verdict == "FAIL"

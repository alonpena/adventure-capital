import json

import pytest

from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.standard_report.package import build_report_data_package
from adventure_capital.standard_report.validation import validate_report_inputs


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_phase5a_builds_report_data_package(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))

    artifacts = build_report_data_package(
        tmp_path,
        document_path="reports/valuation-base.yaml",
        blueprint_path="docs/report-blueprint.md",
    )

    assert artifacts["report_data"].exists()
    assert artifacts["artifacts_manifest"].exists()

    report_data = json.loads(artifacts["report_data"].read_text(encoding="utf-8"))
    assert report_data["document"]["title"] == "Informe de Valorización"
    assert report_data["summary"]["total_revenue"] >= 0

    manifest = json.loads(artifacts["artifacts_manifest"].read_text(encoding="utf-8"))
    assert manifest["checks"]["valid"] is True


def test_phase5a_validation_fails_without_core_artifacts(tmp_path):
    result = validate_report_inputs(tmp_path, "reports/valuation-base.yaml")

    assert result.valid is False
    assert "optimized_results.csv" in result.missing_core_artifacts


def test_phase5a_invalid_inputs_write_validation_only(tmp_path):
    with pytest.raises(ValueError):
        build_report_data_package(tmp_path, document_path="reports/valuation-base.yaml")

    assert (tmp_path / "report_validation.json").exists()
    assert not (tmp_path / "report_data.json").exists()

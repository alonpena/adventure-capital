import json
from pathlib import Path

from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.standard_report.package import build_report_data_package


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_p0_artifact_contract_files_created(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))

    expected = {
        "fixed_cashflow.csv",
        "optimized_results.csv",
        "dcf_cashflow.csv",
        "dcf_annual_summary.csv",
        "multiples_valuation.csv",
        "unit_economics.csv",
        "summary.json",
        "model_instance.json",
        "growth_plan_summary.json",
        "valuation_summary.json",
        "formula_trace.json",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})


def test_model_instance_artifact_required_fields(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    data = _load_json(tmp_path / "model_instance.json")

    assert data["schema_version"] == "1.0"
    assert {"created_at", "H", "T", "T_base", "S", "services"}.issubset(data)
    assert {"beta_anual", "beta_mensual", "descuento"}.issubset(data["discount_assumptions"])
    assert "channels" in data
    assert "acquisition_ceiling" in data
    assert isinstance(data["A_base"], dict)


def test_growth_and_valuation_summary_required_fields(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))

    growth = _load_json(tmp_path / "growth_plan_summary.json")
    assert {
        "schema_version",
        "solver_status",
        "objective_value",
        "total_acquisition",
        "total_revenue",
        "total_ebitda",
        "final_cash",
        "minimum_cash",
        "max_sellers",
        "max_leaders",
        "enabled_channels",
    }.issubset(growth)

    valuation = _load_json(tmp_path / "valuation_summary.json")
    assert {
        "schema_version",
        "method",
        "vc_invested",
        "van",
        "vp_flujos",
        "valor_desecho_nominal",
        "valor_desecho_vp",
        "beta_anual",
        "beta_mensual",
        "tax",
        "ebitda_ultimo_mes",
        "ebitda_anualizado",
        "multiples_reference",
        "unit_economics",
    }.issubset(valuation)
    assert valuation["multiples_reference"]["status"] == "implemented_reference"


def test_formula_trace_required_fields(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    trace = _load_json(tmp_path / "formula_trace.json")

    assert trace["schema_version"] == "1.0"
    formulas = trace["formulas"]
    assert len(formulas) >= 6
    formula_ids = {formula["id"] for formula in formulas}
    assert {"DCF-001", "DCF-002", "DCF-003", "UE-001", "UE-002", "UE-003"}.issubset(formula_ids)
    required = {"id", "name", "expression", "source_fields", "output_fields", "assumptions", "limitations", "implementation_status"}
    for formula in formulas:
        assert required.issubset(formula)


def test_artifacts_manifest_includes_contract_extensions(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    build_report_data_package(
        tmp_path,
        document_path="reports/valuation-base.yaml",
        instance_path=tmp_path / "config.yaml",
    )

    manifest = _load_json(tmp_path / "artifacts_manifest.json")
    artifacts = manifest["artifacts"]
    assert {
        "model_instance",
        "growth_plan_summary",
        "valuation_summary",
        "formula_trace",
    }.issubset(artifacts)
    assert manifest["stage_status"]["instance"] == "passed"
    assert manifest["stage_status"]["deterministic"] == "passed"
    assert manifest["stage_status"]["valuation"] == "passed"
    assert manifest["stage_status"]["report_package"] == "passed"
    assert manifest["audience"]["model_instance"] == "audit"
    assert manifest["audience"]["valuation_summary"] == "entrepreneur"

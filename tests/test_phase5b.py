import json

import pandas as pd

from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.standard_report.document import load_document
from adventure_capital.standard_report.package import build_report_data_package
from adventure_capital.standard_report.sensitivity import write_derived_artifacts


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_phase5b_writes_derived_artifacts(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    document = load_document("reports/valuation-base.yaml")

    paths = write_derived_artifacts(tmp_path, document)

    assert paths["sensitivity_wacc_multiple"].exists()
    assert paths["sensitivity_variables"].exists()
    assert paths["breakeven_variables"].exists()
    assert paths["mapvalue"].exists()

    wacc = pd.read_csv(paths["sensitivity_wacc_multiple"])
    assert {"method", "wacc", "ebitda_multiple", "enterprise_value"}.issubset(wacc.columns)
    assert len(wacc) >= 7 * 5
    assert wacc["enterprise_value"].notna().all()
    assert (wacc["method"] == "calculation").all()

    variables = pd.read_csv(paths["sensitivity_variables"])
    assert "Referencia LTV/CAC" in set(variables["variable"])

    breakeven = pd.read_csv(paths["breakeven_variables"])
    assert {"Ingresos", "CAC", "Costo operacional"}.issubset(set(breakeven["variable"]))

    mapvalue = json.loads(paths["mapvalue"].read_text(encoding="utf-8"))
    assert set(mapvalue["layers"]) == {"input_variables", "operating_flows", "financial_results", "valuation"}


def test_phase5b_package_references_derived_artifacts(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))

    artifacts = build_report_data_package(tmp_path, document_path="reports/valuation-base.yaml")

    report_data = json.loads(artifacts["report_data"].read_text(encoding="utf-8"))
    manifest = json.loads(artifacts["artifacts_manifest"].read_text(encoding="utf-8"))

    assert report_data["sensitivity"]["method"] == "calculation"
    assert "sensitivity_wacc_multiple" in report_data["derived_artifacts"]
    assert "mapvalue" in manifest["artifacts"]

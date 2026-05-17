from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.standard_report.charts import FIGURE_NAMES, generate_figures
from adventure_capital.standard_report.document import load_document
from adventure_capital.standard_report.package import build_report_data_package
from adventure_capital.standard_report.sensitivity import write_derived_artifacts


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_phase5c_generates_required_figures(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    document = load_document("reports/valuation-base.yaml")
    write_derived_artifacts(tmp_path, document)

    paths = generate_figures(tmp_path)

    assert set(paths) == set(FIGURE_NAMES)
    for path in paths.values():
        assert path.exists()
        assert path.stat().st_size > 0


def test_phase5c_package_references_figures(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))

    artifacts = build_report_data_package(tmp_path, document_path="reports/valuation-base.yaml")
    text = artifacts["report_data"].read_text(encoding="utf-8")

    assert "figures/acquisition_year1.png" in text
    assert (tmp_path / "figures" / "mapvalue_diagram.png").exists()

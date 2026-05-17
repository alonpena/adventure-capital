import pytest

from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.standard_report.package import build_report_data_package
from adventure_capital.standard_report.render import render_report


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_phase5f_renders_pdf_when_backend_available(tmp_path):
    try:
        __import__("weasyprint")
    except Exception as exc:
        pytest.skip(f"WeasyPrint backend unavailable: {exc}")

    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    build_report_data_package(tmp_path, document_path="reports/valuation-base.yaml")

    paths = render_report(tmp_path, pdf=True)

    assert paths["html"].exists()
    assert paths["pdf"].exists()
    assert paths["pdf"].stat().st_size > 0

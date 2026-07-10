from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.standard_report.package import build_report_data_package
from adventure_capital.standard_report.render import render_report


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_phase5d_renders_html_report(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    build_report_data_package(tmp_path, document_path="reports/valuation-base.yaml")

    path = render_report(tmp_path)

    assert path.exists()
    html = path.read_text(encoding="utf-8")
    assert "Resumen ejecutivo" in html
    assert "Sensibilidad" in html
    assert "figures/acquisition_year1.png" in html

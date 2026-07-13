from bs4 import BeautifulSoup
from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.standard_report.package import build_report_data_package
from adventure_capital.standard_report.render import render_report

def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config

def test_ev_only_renders_15_pages(tmp_path):
    """Reporte EV-only: 14 .page."""
    out_dir = tmp_path / "ev_only"
    run_pipeline(_fast_config(), output_dir=str(out_dir))
    
    # Render with EV-only template
    build_report_data_package(out_dir, document_path="reports/valuation-ev.template.yaml", schema_path="reports/schema/valuation-ev.schema.yaml")
    path = render_report(out_dir)
    
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    pages = soup.find_all("section", class_="page")
    assert len(pages) == 14, f"Esperadas 14 páginas, encontradas {len(pages)}"

def test_full_renders_16_pages(tmp_path):
    """Reporte full: 14 .page."""
    out_dir = tmp_path / "full"
    run_pipeline(_fast_config(), output_dir=str(out_dir))
    
    # Render with full base document
    build_report_data_package(out_dir, document_path="reports/valuation-base.yaml")
    path = render_report(out_dir)
    
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    pages = soup.find_all("section", class_="page")
    assert len(pages) == 14, f"Esperadas 14 páginas, encontradas {len(pages)}"

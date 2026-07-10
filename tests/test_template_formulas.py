from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.standard_report.package import build_report_data_package
from adventure_capital.standard_report.render import render_report
from bs4 import BeautifulSoup

def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config

def test_report_contains_0_formula_blocks(tmp_path):
    """El HTML renderizado no debe contener bloques .formula-container (eliminados)."""
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    build_report_data_package(tmp_path, document_path="reports/valuation-base.yaml")
    path = render_report(tmp_path)
    
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.find_all(class_="formula-container")
    assert len(blocks) == 0, f"Encontrados {len(blocks)}, esperados 0"

def test_each_formula_block_has_pre_element(tmp_path):
    """Pasar si no hay bloques de fórmulas."""
    pass

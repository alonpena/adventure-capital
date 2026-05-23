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

def test_report_contains_9_formula_blocks(tmp_path):
    """El HTML renderizado debe contener exactamente 9 bloques .formula-container."""
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    build_report_data_package(tmp_path, document_path="reports/valuation-base.yaml")
    path = render_report(tmp_path)
    
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.find_all(class_="formula-container")
    assert len(blocks) == 9, f"Encontrados {len(blocks)}, esperados 9"

def test_each_formula_block_has_pre_element(tmp_path):
    """Cada bloque debe tener un <pre class='formula'> con contenido."""
    run_pipeline(_fast_config(), output_dir=str(tmp_path))
    build_report_data_package(tmp_path, document_path="reports/valuation-base.yaml")
    path = render_report(tmp_path)
    
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    for block in soup.find_all(class_="formula-container"):
        pre = block.find("pre", class_="formula")
        assert pre is not None, "Bloque sin <pre class='formula'>"
        assert len(pre.text.strip()) > 10, "Fórmula vacía o demasiado corta"

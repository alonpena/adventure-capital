import pytest
import pathlib
import json
import yaml
import pandas as pd
from adventure_capital.standard_report.consistency import check_consistency
from adventure_capital.pipeline import run_pipeline
from adventure_capital.config import load_config

def test_base_config_passes_all_checks(tmp_path):
    """Pipeline base debe pasar los 5 checks de consistencia."""
    config = load_config("configs/base.yaml")
    # Run the pipeline baseline to populate the output directory
    run_pipeline(config, output_dir=str(tmp_path), baseline_only=True)
    
    report = check_consistency(tmp_path, tmp_path / "config.yaml")
    assert report["all_passed"] is True
    failed = [c for c in report["checks"] if not c["passed"] and not c.get("skipped")]
    assert failed == [], f"Checks fallaron: {failed}"

def test_aijourney_passes_all_checks(tmp_path):
    """Pipeline AiJourney debe pasar los 5 checks de consistencia."""
    config = load_config("configs/aijourney.yaml")
    run_pipeline(config, output_dir=str(tmp_path), baseline_only=True)
    
    report = check_consistency(tmp_path, tmp_path / "config.yaml")
    assert report["all_passed"] is True

def test_consistency_report_written_to_disk(tmp_path):
    """El archivo consistency_report.json debe existir tras el check."""
    config = load_config("configs/base.yaml")
    run_pipeline(config, output_dir=str(tmp_path), baseline_only=True)
    
    report_path = tmp_path / "consistency_report.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert "all_passed" in data
    assert "checks" in data

def test_negative_ebitda_inconsistency_detected():
    """Un EBITDA manipulado debe hacer fallar el check ebitda_definition."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        df = pd.DataFrame({
            "t": [1, 2],
            "Año": [1, 1],
            "Mes": [1, 2],
            "Ingresos": [100, 100],
            "Costo_operacional": [40, 40],
            "CAC": [10, 10],
            "G_adm": [5, 5],
            "RRHH": [5, 5],
            "EBITDA": [999, 999],  # incorrecto: debería ser 40
            "Caja": [100000, 100000]
        })
        df.to_csv(tmp / "optimized_results.csv", index=False)
        
        # annual financials placeholder
        annual_df = pd.DataFrame({
            "Año": [1],
            "Ingresos": [200],
            "Costo_operacional": [80],
            "CAC": [20],
            "G_adm": [10],
            "RRHH": [10],
            "EBITDA": [80]
        })
        annual_df.to_csv(tmp / "dcf_annual_summary.csv", index=False)
        
        # unit economics placeholder
        ue_df = pd.DataFrame([
            {"Unit Economic": "Gross Profit (GP)", "Valor": 0.6}
        ])
        ue_df.to_csv(tmp / "unit_economics.csv", index=False)
        
        # Crear YAML mínimo de documento
        doc = {"document": {"title": "X", "company_name": "X", "author": "X", "report_date": "2025-01-01"},
               "params": {"config_path": "configs/base.yaml"},
               "dcf": {"tasa_descuento": 0.35, "horizonte_meses": 36, "valor_residual_metodo": "none"}}
        (tmp / "doc.yaml").write_text(yaml.dump(doc))

        report = check_consistency(tmp, tmp / "doc.yaml")
        ebitda_check = next(c for c in report["checks"] if c["name"] == "ebitda_definition")
        assert ebitda_check["passed"] is False
        assert report["all_passed"] is False

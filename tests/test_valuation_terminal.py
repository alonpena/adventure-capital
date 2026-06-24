import pytest
from adventure_capital.valuation import calcular_valor_residual

WACC = 0.35
EBITDA_LAST = 100_000  # $100k/mes -> $1.2M anual

def test_none_returns_zero():
    assert calcular_valor_residual(EBITDA_LAST, "none", WACC) == 0.0

def test_ebitda_multiple_correct():
    vr = calcular_valor_residual(EBITDA_LAST, "ebitda_multiple", WACC, ebitda_multiple=6.0)
    expected = EBITDA_LAST * 12 * 6.0  # = 7,200,000
    assert abs(vr - expected) < 1.0

def test_gordon_correct():
    g = 0.03
    vr = calcular_valor_residual(EBITDA_LAST, "gordon", WACC, gordon_g=g)
    ebitda_anual = EBITDA_LAST * 12
    expected = ebitda_anual * (1 + g) / (WACC - g)
    assert abs(vr - expected) < 1.0

def test_gordon_wacc_lt_g_raises():
    with pytest.raises(ValueError, match="mayor que g"):
        calcular_valor_residual(EBITDA_LAST, "gordon", 0.02, gordon_g=0.05)

def test_ebitda_multiple_missing_param_raises():
    with pytest.raises(ValueError, match="ebitda_multiple requerido"):
        calcular_valor_residual(EBITDA_LAST, "ebitda_multiple", WACC)

def test_unknown_method_raises():
    with pytest.raises(ValueError, match="desconocido"):
        calcular_valor_residual(EBITDA_LAST, "magic_formula", WACC)


def test_pipeline_document_propagation(tmp_path):
    import yaml
    from adventure_capital.config import default_config
    from adventure_capital.pipeline import run_pipeline

    # Create a config
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 10
    config["servicios"][0]["ticket"] = 100000

    # Create a doc YAML with gordon method
    doc = {
        "document": {"title": "X", "company_name": "X", "author": "X", "report_date": "2026-01-01"},
        "params": {"config_path": "configs/base.yaml"},
        "dcf": {
            "tasa_descuento": 0.30,
            "horizonte_meses": 14,
            "valor_residual_metodo": "gordon",
            "gordon_g": 0.05
        }
    }
    doc_path = tmp_path / "test_doc.yaml"
    doc_path.write_text(yaml.dump(doc), encoding="utf-8")

    # Run the pipeline with document_path
    res = run_pipeline(config, output_dir=str(tmp_path / "out"), document_path=str(doc_path))
    dcf = res["dcf"]

    # Verify WACC is 0.30
    assert dcf["beta_anual"] == 0.30
    # Verify method is gordon and gordon_g is 0.05
    assert dcf["valor_desecho_nominal"] > 0.0


def test_pipeline_document_validation_errors(tmp_path):
    import yaml
    from adventure_capital.config import default_config
    from adventure_capital.pipeline import run_pipeline

    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 10

    # Gordon method missing gordon_g
    doc1 = {
        "document": {"title": "X", "company_name": "X", "author": "X", "report_date": "2026-01-01"},
        "params": {"config_path": "configs/base.yaml"},
        "dcf": {
            "tasa_descuento": 0.30,
            "horizonte_meses": 14,
            "valor_residual_metodo": "gordon",
        }
    }
    doc_path1 = tmp_path / "doc1.yaml"
    doc_path1.write_text(yaml.dump(doc1), encoding="utf-8")

    with pytest.raises(ValueError, match="gordon_g es requerido"):
        run_pipeline(config, document_path=str(doc_path1))

    # EBITDA multiple without an explicit ebitda_multiple now falls back to the
    # default 1.0 (1x last-year EBITDA, going-concern terminal) instead of erroring.
    doc2 = {
        "document": {"title": "X", "company_name": "X", "author": "X", "report_date": "2026-01-01"},
        "params": {"config_path": "configs/base.yaml"},
        "dcf": {
            "tasa_descuento": 0.30,
            "horizonte_meses": 14,
            "valor_residual_metodo": "ebitda_multiple",
        }
    }
    doc_path2 = tmp_path / "doc2.yaml"
    doc_path2.write_text(yaml.dump(doc2), encoding="utf-8")

    result = run_pipeline(config, document_path=str(doc_path2))
    assert result["dcf"]["VAN"] is not None


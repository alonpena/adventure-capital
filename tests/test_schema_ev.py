import jsonschema
import yaml
import pathlib

SCHEMA_PATH = pathlib.Path("reports/schema/valuation-ev.schema.yaml")
TEMPLATE_PATH = pathlib.Path("reports/valuation-ev.template.yaml")

def load(path):
    return yaml.safe_load(path.read_text())

def test_template_passes_ev_schema():
    """El template mínimo sin campos cualitativos debe pasar validación."""
    schema = load(SCHEMA_PATH)
    doc = load(TEMPLATE_PATH)
    # Reemplazar placeholders para que el schema no falle por formato
    doc["document"]["company_name"] = "TestCo"
    doc["document"]["report_date"] = "2025-01-01"
    jsonschema.validate(doc, schema)  # debe no lanzar excepción

def test_document_without_qualitative_passes():
    """Documento sin empresa.descripcion, cap_table, etc. es válido."""
    schema = load(SCHEMA_PATH)
    minimal = {
        "document": {"title": "EV Report", "company_name": "X", "author": "Y", "report_date": "2025-01-01"},
        "params": {"config_path": "configs/base.yaml"},
        "dcf": {"tasa_descuento": 0.35, "horizonte_meses": 36, "valor_residual_metodo": "none"}
    }
    jsonschema.validate(minimal, schema)

def test_document_missing_required_dcf_fails():
    """Documento sin dcf.tasa_descuento debe fallar validación."""
    schema = load(SCHEMA_PATH)
    invalid = {
        "document": {"title": "EV Report", "company_name": "X", "author": "Y", "report_date": "2025-01-01"},
        "params": {"config_path": "configs/base.yaml"},
        "dcf": {"horizonte_meses": 36, "valor_residual_metodo": "none"}  # falta tasa_descuento
    }
    try:
        jsonschema.validate(invalid, schema)
        assert False, "Debió lanzar ValidationError"
    except jsonschema.ValidationError:
        pass

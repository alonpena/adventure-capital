import math

from adventure_capital.config import default_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import solve_growth_plan
from adventure_capital.pipeline import run_pipeline
from adventure_capital.results import extract_results
from adventure_capital.unit_economics import calculate_unit_economics
from adventure_capital.valuation import calculate_dcf, calculate_multiples_valuation


def _phase3_fixture():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    instance = generate_instance(config)
    solution = solve_growth_plan(instance, time_limit=30)
    df = extract_results(instance, solution)
    return instance, df


def test_dcf_returns_expected_keys_and_finite_values():
    instance, df = _phase3_fixture()
    dcf = calculate_dcf(df, instance)
    expected = {"df_flujo_caja", "resumen_anual_dcf", "vp_flujos", "valor_desecho_vp", "VAN"}
    assert expected.issubset(dcf.keys())
    assert len(dcf["df_flujo_caja"]) == 14
    assert math.isfinite(dcf["VAN"])
    assert math.isfinite(dcf["vp_flujos"])


def test_multiples_valuation_returns_table():
    instance, df = _phase3_fixture()
    multiples = calculate_multiples_valuation(df, instance)
    assert len(multiples["df_multiplos"]) == 2
    assert math.isfinite(multiples["valor_por_ingresos"])
    assert math.isfinite(multiples["valor_por_ebitda"])


def test_unit_economics_returns_business_table():
    instance, df = _phase3_fixture()
    dcf = calculate_dcf(df, instance)
    unit_economics = calculate_unit_economics(df, instance, dcf)
    assert len(unit_economics) == 15
    assert {"Unit Economic", "Definición", "Fórmula / Fuente", "Valor", "Unidad"}.issubset(unit_economics.columns)
    assert "Adquisición" in unit_economics["Unit Economic"].tolist()
    assert unit_economics["Valor"].notna().any()


def test_pipeline_runs_phase3_outputs(tmp_path):
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    result = run_pipeline(config, output_dir=str(tmp_path))
    assert {"dcf", "multiples_valuation", "unit_economics"}.issubset(result.keys())
    assert (tmp_path / "dcf_cashflow.csv").exists()
    assert (tmp_path / "multiples_valuation.csv").exists()
    assert (tmp_path / "unit_economics.csv").exists()

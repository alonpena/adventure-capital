import math

import pytest

from adventure_capital.config import default_config, load_config, validate_config
from adventure_capital.financial_model import build_fixed_period_financial_model
from adventure_capital.instance import generate_instance


def test_config_loads_and_validates():
    config = load_config("configs/base.yaml")
    validate_config(config)
    assert config["H"] == 36


def test_horizon_minimum_enforced():
    config = default_config()
    config["H"] = 13
    with pytest.raises(ValueError, match="H must be >= 14"):
        validate_config(config)


def test_instance_generation_core_parameters():
    instance = generate_instance(default_config())
    assert instance["H"] == 36
    assert instance["S"] == 1
    assert len(instance["T"]) == 36
    assert instance["A_base"][(0, 1)] == 2.0
    assert 0 < instance["churn_mensual"][(0, 1)] < 1
    assert instance["phi"][(0, 1, 1)] == 1.0
    assert instance["delta"][(0, 1, 4)] == 1
    assert math.isfinite(instance["descuento"][1])


def test_fixed_period_financial_model_outputs_12_rows():
    instance = generate_instance(default_config())
    df = build_fixed_period_financial_model(instance)
    assert len(df) == 12
    assert df["Adq_clientes"].tolist() == [2, 2, 3, 4, 5, 5, 6, 7, 8, 8, 9, 10]
    assert {"Ingresos", "CAC", "Costo_operacional", "EBITDA", "Caja"}.issubset(df.columns)
    assert df["Caja"].notna().all()

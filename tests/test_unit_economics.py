"""Phase 5 — unit economics, LTV/CAC consistency, breakeven analysis."""

import numpy as np
import pandas as pd
import pytest

from adventure_capital.calibration.checks import check_ltv_cac
from adventure_capital.config import default_config, load_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import solve_growth_plan
from adventure_capital.results import extract_results
from adventure_capital.unit_economics import (
    annual_ltv,
    compute_runway,
    compute_unit_economics_metrics,
)


def _two_service_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    config["servicios"] = [
        {
            "nombre": "Alto",
            "ticket": 5000, "frecuencia": 6, "alpha": 0.8,
            "churn_anual": [0.4, 0.3, 0.2], "c_u": 500, "c_min": 2000,
            "u_max": 50, "A_base": [1, 1, 2, 2, 2, 3, 3, 4, 4, 5, 5, 6],
        },
        {
            "nombre": "Bajo",
            "ticket": 500, "frecuencia": 3, "alpha": 0.7,
            "churn_anual": [0.5, 0.35, 0.2], "c_u": 50, "c_min": 800,
            "u_max": 200, "A_base": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15],
        },
    ]
    return config


def _solve(config):
    instance = generate_instance(config)
    solution = solve_growth_plan(instance)
    return instance, extract_results(instance, solution), solution


def test_ltv_uses_annual_metrics():
    services = [
        {"ticket": 1000, "frecuencia": 4, "c_u": 200, "churn_anual": [0.25, 0.2, 0.1]},
    ]
    expected = 1000 * (12 / 4) * (1 - 200 / 1000) / 0.25
    assert annual_ltv(services) == pytest.approx(expected)
    # Uses the annual churn rate directly, NOT a monthly conversion.
    monthly_churn = 1 - (1 - 0.25) ** (1 / 12)
    assert annual_ltv(services) != pytest.approx(
        1000 * (12 / 4) * (1 - 200 / 1000) / monthly_churn
    )


def test_ltv_sums_services_not_averages():
    services = _two_service_config()["servicios"]
    ltv_alto = 5000 * (12 / 6) * (1 - 500 / 5000) / 0.4
    ltv_bajo = 500 * (12 / 3) * (1 - 50 / 500) / 0.5
    assert annual_ltv(services) == pytest.approx(ltv_alto + ltv_bajo)
    # An averaging implementation would give a very different (smaller) number.
    assert annual_ltv(services) != pytest.approx((ltv_alto + ltv_bajo) / 2)


def test_cac_uses_cumulative():
    instance, df, _ = _solve(_two_service_config())
    metrics = compute_unit_economics_metrics(df, instance)
    expected_cac = float(df["cumulative_cac_per_user"].iloc[-1])
    assert metrics["cac_per_customer"] == pytest.approx(expected_cac)
    assert metrics["ltv_cac"] == pytest.approx(metrics["annual_ltv"] / expected_cac)


def test_ltv_cac_alert_c08(tmp_path):
    unit = pd.DataFrame(
        [{"Unit Economic": "LTV/CAC", "Definición": "", "Fórmula / Fuente": "", "Valor": 25.0, "Unidad": "ratio"}]
    )
    unit.to_csv(tmp_path / "unit_economics.csv", index=False)
    result = check_ltv_cac({"severity": "warning", "max_ratio": 20.0}, tmp_path)
    assert result.passed is False
    assert "Artefacto" in result.message


def test_breakeven_customers():
    instance, df, _ = _solve(_two_service_config())
    metrics = compute_unit_economics_metrics(df, instance)
    contribution = metrics["annual_contribution_per_customer"]
    expected = metrics["annual_fixed_costs"] / contribution
    assert metrics["breakeven_customers"] == pytest.approx(expected)


def test_payback_customers():
    instance, df, _ = _solve(_two_service_config())
    metrics = compute_unit_economics_metrics(df, instance)
    contribution = metrics["annual_contribution_per_customer"]
    expected = float(instance["VC"]) / contribution
    assert metrics["payback_customers"] == pytest.approx(expected)


def test_payback_month():
    instance, df, _ = _solve(load_config("configs/demo-complex.yaml"))
    metrics = compute_unit_economics_metrics(df, instance)
    vc = float(instance["VC"])
    crossing = df.loc[df["Caja"] >= vc, "t"]
    expected = int(crossing.iloc[0]) if not crossing.empty else None
    assert metrics["payback_month"] == expected


def test_runway_nan_when_profitable():
    df = pd.DataFrame({"Caja": [100.0, 200.0, 300.0], "EBITDA": [-50.0, 40.0, -20.0]})
    runway = compute_runway(df)
    assert runway[0] == pytest.approx(100.0 / 50.0)
    assert np.isnan(runway[1])          # EBITDA > 0 -> NaN
    assert runway[2] == pytest.approx(300.0 / 20.0)


def test_legacy_regression():
    # Phase 5 is post-solve only: it must not change EV / EBITDA / Caja.
    instance, df, solution = _solve(load_config("configs/demo-complex.yaml"))
    ebitda_before = float(df["EBITDA"].sum())
    cash_before = float(df["Caja"].iloc[-1])
    compute_unit_economics_metrics(df, instance)
    assert solution["status"] == "Optimal"
    assert float(df["EBITDA"].sum()) == pytest.approx(ebitda_before)
    assert float(df["Caja"].iloc[-1]) == pytest.approx(cash_before)

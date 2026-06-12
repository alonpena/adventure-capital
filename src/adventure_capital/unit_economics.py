"""Unit economics calculations.

All unit-economics metrics are ANNUAL and post-solve (no MILP variables). Service
lines are SUMMED, never averaged. LTV uses annual revenue and annual churn; CAC uses
the cumulative per-user cost from the CAC traceability columns (Phase 3).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _annual_frequency(service: dict[str, Any]) -> float:
    """Purchases per year. ``frecuencia`` is months between repurchases."""
    freq = service["frecuencia"]
    return 12.0 / freq if freq > 0 else 0.0


def _gross_margin(service: dict[str, Any]) -> float:
    ticket = service["ticket"]
    return 1.0 - service["c_u"] / ticket if ticket > 0 else 0.0


def annual_revenue_per_customer(services: list[dict[str, Any]]) -> float:
    """Sum (not average) of ticket * annual frequency across service lines."""
    return float(sum(s["ticket"] * _annual_frequency(s) for s in services))


def annual_gross_profit_per_customer(services: list[dict[str, Any]]) -> float:
    """Sum of annual unit gross profit across service lines."""
    return float(sum((s["ticket"] - s["c_u"]) * _annual_frequency(s) for s in services))


def annual_ltv(services: list[dict[str, Any]]) -> float:
    """Annual LTV summed over service lines: Σ ticket·(12/freq)·gm / annual_churn."""
    total = 0.0
    for s in services:
        annual_churn = float(s["churn_anual"][0])
        if annual_churn <= 0:
            continue
        total += s["ticket"] * _annual_frequency(s) * _gross_margin(s) / annual_churn
    return float(total)


def _cumulative_cac(df: pd.DataFrame) -> float:
    """Annual CAC per user = Σ total_acquisition_cost / Σ new_customers."""
    if "cumulative_cac_per_user" in df.columns and len(df):
        value = float(df["cumulative_cac_per_user"].iloc[-1])
        if not pd.isna(value):
            return value
    total_acq = float(df["Adq_clientes"].sum())
    return float(df["CAC"].sum() / total_acq) if total_acq > 0 else 0.0


def compute_runway(df: pd.DataFrame) -> np.ndarray:
    """Months of survival at current burn; NaN where EBITDA >= 0 (profitable)."""
    cash = df["Caja"].to_numpy(dtype=float)
    ebitda = df["EBITDA"].to_numpy(dtype=float)
    burning = ebitda < 0
    return np.where(burning, cash / np.where(burning, np.abs(ebitda), 1.0), np.nan)


def compute_unit_economics_metrics(
    df: pd.DataFrame, instance: dict[str, Any], dcf: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Post-solve annual unit-economics metrics + breakeven/payback/runway diagnostics."""
    services = instance["servicios"]
    vc = float(instance["VC"])

    ltv = annual_ltv(services)
    cac = _cumulative_cac(df)
    ltv_cac = ltv / cac if cac > 0 and not pd.isna(ltv) else float("nan")

    gross_profit_per_customer = annual_gross_profit_per_customer(services)
    contribution = gross_profit_per_customer - cac

    year_one = df[df["Año"] == 1]
    annual_fixed_costs = float(year_one["G_adm"].sum() + year_one["RRHH"].sum())
    breakeven_customers = annual_fixed_costs / contribution if contribution > 0 else float("nan")
    payback_customers = vc / contribution if contribution > 0 else float("nan")

    # Payback month: first period where the original VC ticket is recovered (Caja >= VC).
    recovered = df.loc[df["Caja"] >= vc, "t"]
    payback_month = int(recovered.iloc[0]) if not recovered.empty else None

    return {
        "annual_ltv": ltv,
        "annual_revenue_per_customer": annual_revenue_per_customer(services),
        "annual_gross_profit_per_customer": gross_profit_per_customer,
        "cac_per_customer": cac,
        "ltv_cac": ltv_cac,
        "annual_contribution_per_customer": contribution,
        "annual_fixed_costs": annual_fixed_costs,
        "breakeven_customers": breakeven_customers,
        "payback_customers": payback_customers,
        "payback_month": payback_month,
        "runway_months": compute_runway(df).tolist(),
    }


def calculate_unit_economics(
    df: pd.DataFrame,
    instance: dict[str, Any],
    dcf: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Calculate unit economics table from monthly results and optional DCF."""
    services = instance["servicios"]
    parameters = instance.get("parametros", instance.get("params", {}))
    working_capital = float(instance["VC"])

    total_acquisition = float(df["Adq_clientes"].sum())
    total_revenue = float(df["Ingresos"].sum())
    total_operational_cost = float(df["Costo_operacional"].sum())
    total_cac = float(df["CAC"].sum())
    total_negative_ebitda = float(-df.loc[df["EBITDA"] < 0, "EBITDA"].sum())

    average_ticket = float(np.mean([service["ticket"] for service in services]))
    average_frequency = float(np.mean([service["frecuencia"] for service in services]))
    monthly_recurrence = 1 / average_frequency if average_frequency > 0 else 0.0
    annual_churn = float(np.mean([service["churn_anual"][0] for service in services]))
    average_cac = total_cac / total_acquisition if total_acquisition > 0 else 0.0

    recurring_revenue = (
        float(df["Ingresos_recurrentes_proxy"].sum())
        if "Ingresos_recurrentes_proxy" in df.columns
        else 0.0
    )
    arr_pct = recurring_revenue / total_revenue if total_revenue > 0 else 0.0
    gross_profit = 1 - (total_operational_cost / total_revenue) if total_revenue > 0 else 0.0

    average_active_clients = float(df["Clientes_activos"].mean())
    arpu = total_revenue / (average_active_clients * len(df)) if average_active_clients > 0 else 0.0

    daily_cash_burn_rate = total_negative_ebitda / 360
    operating_cycle = float(parameters.get("ciclo_op", [30])[0])
    working_capital_need = daily_cash_burn_rate * operating_cycle
    bootstrapping = max(working_capital, working_capital_need)

    # Annual LTV summed over service lines (Phase 5): Σ ticket·(12/freq)·gm / annual_churn.
    ltv = annual_ltv(services)
    cumulative_cac = _cumulative_cac(df)

    npv = dcf["VAN"] if dcf is not None and "VAN" in dcf else np.nan
    ltv_2 = npv / total_acquisition if total_acquisition > 0 and not pd.isna(npv) else np.nan
    # LTV/CAC uses the cumulative (annual) CAC per user, not a period-blended average.
    ltv_cac = ltv / cumulative_cac if cumulative_cac > 0 and not pd.isna(ltv) else 0.0
    monetized_clients = total_acquisition * arr_pct

    year_one = df[df["Año"] == 1]
    year_one_acquisition = float(year_one["Adq_clientes"].sum()) if not year_one.empty else 0.0
    base_acquisition = float(year_one["Adq_clientes"].iloc[0]) if not year_one.empty else np.nan
    mom_growth = (
        (year_one_acquisition / base_acquisition) ** (1 / 11) - 1
        if base_acquisition and base_acquisition > 0
        else np.nan
    )

    return pd.DataFrame(
        [
            {
                "Unit Economic": "Adquisición",
                "Definición": "Clientes nuevos captados en el horizonte",
                "Fórmula / Fuente": "Σ Adquisición mensual",
                "Valor": total_acquisition,
                "Unidad": "# clientes",
            },
            {
                "Unit Economic": "MoM Growth",
                "Definición": "Crecimiento mensual equivalente de adquisición",
                "Fórmula / Fuente": "(Σ Adq. año 1 / base)^(1/11) - 1",
                "Valor": mom_growth,
                "Unidad": "%",
            },
            {
                "Unit Economic": "CHURN",
                "Definición": "Porcentaje de clientes perdidos en un año",
                "Fórmula / Fuente": "Parámetro promedio año 1",
                "Valor": annual_churn,
                "Unidad": "%",
            },
            {
                "Unit Economic": "CAC",
                "Definición": "Costo de adquisición por cliente",
                "Fórmula / Fuente": "Σ CAC / Σ Adquisición",
                "Valor": average_cac,
                "Unidad": "USD/cliente",
            },
            {
                "Unit Economic": "Ticket promedio",
                "Definición": "Precio promedio por servicio",
                "Fórmula / Fuente": "Parámetro configurado",
                "Valor": average_ticket,
                "Unidad": "USD",
            },
            {
                "Unit Economic": "Recurrencia mensual",
                "Definición": "Veces que compra cada cliente al mes",
                "Fórmula / Fuente": "1 / frecuencia promedio",
                "Valor": monthly_recurrence,
                "Unidad": "veces/mes",
            },
            {
                "Unit Economic": "ARR",
                "Definición": "Porcentaje de ingresos recurrentes sobre total",
                "Fórmula / Fuente": "Ingresos recurrentes / Total ingresos",
                "Valor": arr_pct,
                "Unidad": "%",
            },
            {
                "Unit Economic": "Gross Profit (GP)",
                "Definición": "Margen bruto operacional",
                "Fórmula / Fuente": "1 - Costos operacionales / Ingresos",
                "Valor": gross_profit,
                "Unidad": "%",
            },
            {
                "Unit Economic": "ARPU",
                "Definición": "Ingreso promedio por usuario",
                "Fórmula / Fuente": "Ingresos totales / clientes activos promedio * horizonte",
                "Valor": arpu,
                "Unidad": "USD/cliente",
            },
            {
                "Unit Economic": "Cash Burn Rate",
                "Definición": "Dinero consumido por día",
                "Fórmula / Fuente": "Σ EBITDA negativo / 360",
                "Valor": daily_cash_burn_rate,
                "Unidad": "USD/día",
            },
            {
                "Unit Economic": "Bootstrapping",
                "Definición": "Capital de trabajo hasta punto de equilibrio",
                "Fórmula / Fuente": "max(VC, CBR × ciclo operacional)",
                "Valor": bootstrapping,
                "Unidad": "USD",
            },
            {
                "Unit Economic": "LTV",
                "Definición": "Valor anual estimado que genera cada cliente (suma de líneas)",
                "Fórmula / Fuente": "Σ_servicio (ticket × frecuencia anual × margen) / churn anual",
                "Valor": ltv,
                "Unidad": "USD/cliente",
            },
            {
                "Unit Economic": "LTV(2)",
                "Definición": "Valor por cliente medido por VAN",
                "Fórmula / Fuente": "VAN / Σ adquisición",
                "Valor": ltv_2,
                "Unidad": "USD/cliente",
            },
            {
                "Unit Economic": "LTV/CAC",
                "Definición": "Eficiencia del capital de adquisición",
                "Fórmula / Fuente": "LTV / CAC",
                "Valor": ltv_cac,
                "Unidad": "ratio",
            },
            {
                "Unit Economic": "Clientes monetizados",
                "Definición": "Clientes que compran recurrentemente",
                "Fórmula / Fuente": "Adquisición × ARR",
                "Valor": monetized_clients,
                "Unidad": "# clientes",
            },
        ]
    )


# Legacy Spanish API alias.
def calcular_unit_economics(
    df: pd.DataFrame,
    inst: dict[str, Any],
    resultados_dcf: dict[str, Any] | None = None,
) -> pd.DataFrame:
    return calculate_unit_economics(df, inst, resultados_dcf)

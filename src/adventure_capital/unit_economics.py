"""Unit economics calculations."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


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

    first_service = services[0]
    first_year_monthly_churn = 1 - (1 - first_service["churn_anual"][0]) ** (1 / 12)
    first_service_marginal_gp = 1 - first_service["c_u"] / first_service["ticket"]
    ltv = (
        (average_ticket * first_service_marginal_gp) / first_year_monthly_churn
        if first_year_monthly_churn > 0
        else np.nan
    )

    npv = dcf["VAN"] if dcf is not None and "VAN" in dcf else np.nan
    ltv_2 = npv / total_acquisition if total_acquisition > 0 and not pd.isna(npv) else np.nan
    ltv_cac = ltv / average_cac if average_cac > 0 and not pd.isna(ltv) else 0.0
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
                "Definición": "Valor total estimado que genera cada cliente",
                "Fórmula / Fuente": "(Ticket × margen bruto marginal) / churn mensual",
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

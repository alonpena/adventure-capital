"""Deterministic fixed-period financial model."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


FIXED_ACQUISITION_MONTHS = 12


def build_fixed_period_financial_model(instance: dict[str, Any]) -> pd.DataFrame:
    """Build first 12 monthly cashflow rows from configured base acquisition.

    No solver required. Uses same cohort, recurrence, revenue, CAC, operational cost,
    EBITDA, and cash formulas as optimization model for fixed acquisition months.
    """
    services = instance["servicios"]
    rows: list[dict[str, float]] = []
    previous_cash = float(instance["VC"])

    channels = instance.get("channels", {})
    sf_active = channels.get("salesforce", {}).get("active", True)
    ad_active = channels.get("advertising", {}).get("active", False)
    ad_params = channels.get("advertising", {}) if ad_active else {}

    for t in instance["T_base"]:
        year = (t - 1) // 12 + 1
        month_in_year = (t - 1) % 12 + 1
        total_acquisition = sum(instance["A_base"][(s, t)] for s in range(instance["S"]))
        if sf_active:
            sellers = math.ceil(total_acquisition / instance["meta"]) if total_acquisition > 0 else 0
            leaders = math.ceil(sellers / instance["sup"]) if sellers > 0 else 0
        else:
            sellers = 0
            leaders = 0

        row: dict[str, float] = {
            "t": t,
            "Año": year,
            "Mes": month_in_year,
            "Vendedores": sellers,
            "Lideres": leaders,
            "RRHH": instance["RRHH"][t],
            "G_adm": instance["g_adm"],
        }

        cac_commissions = 0.0
        for s, service in enumerate(services):
            name = service["nombre"]
            acquisition = instance["A_base"][(s, t)]
            active_clients = sum(
                instance["phi"].get((s, cohort, t), 0.0) * instance["A_base"][(s, cohort)]
                for cohort in instance["T_base"]
                if cohort <= t
            )
            recurring_sales = sum(
                instance["delta"].get((s, cohort, t), 0)
                * instance["phi"].get((s, cohort, t), 0.0)
                * instance["alpha"].get((s, t), 0.0)
                * instance["A_base"][(s, cohort)]
                for cohort in instance["T_base"]
                if cohort < t
            )
            total_services = acquisition + recurring_sales
            revenue = service["ticket"] * total_services
            op_steps = math.ceil(total_services / service["u_max"]) if total_services > 0 else 0
            operational_cost = max(service["c_u"] * total_services, service["c_min"] * op_steps)

            row[f"A_{name}"] = acquisition
            row[f"C_{name}"] = active_clients
            row[f"R_{name}"] = recurring_sales
            row[f"Q_{name}"] = total_services
            row[f"I_{name}"] = revenue
            row[f"Cost_op_{name}"] = operational_cost
            row[f"m_op_{name}"] = op_steps

            cac_commissions += (instance["com_v"] + instance["com_l"]) * service["ticket"] * acquisition

        if not sf_active:
            cac_commissions = 0.0

        advertising_cac_cost = 0.0
        if ad_active:
            if not sf_active:
                # Advertising-only: the exogenous year-1 acquisition flows through the
                # advertising recta; implied investment = (A_ad_total - a) / b.
                advertising_cac_cost = max(
                    (total_acquisition - ad_params["a"]) / ad_params["b"], 0.0
                )
            row["advertising_cac_cost"] = advertising_cac_cost

        row["salesforce_cac_cost"] = (
            instance["rem_v"] * sellers + instance["rem_l"] * leaders + cac_commissions
        )
        row["third_party_cost"] = 0.0
        row["CAC"] = (
            row["salesforce_cac_cost"]
            + advertising_cac_cost
            + row["third_party_cost"]
        )
        row["total_acquisition_cost"] = row["CAC"]

        service_names = [service["nombre"] for service in services]
        row["Adq_clientes"] = sum(row[f"A_{name}"] for name in service_names)
        row["Clientes_activos"] = sum(row[f"C_{name}"] for name in service_names)
        row["Ventas_recurrentes"] = sum(row[f"R_{name}"] for name in service_names)
        row["Servicios_totales"] = sum(row[f"Q_{name}"] for name in service_names)
        row["Ingresos"] = sum(row[f"I_{name}"] for name in service_names)
        row["Costo_operacional"] = sum(row[f"Cost_op_{name}"] for name in service_names)
        row["Costos_totales_sin_CAC"] = row["Costo_operacional"] + row["G_adm"] + row["RRHH"]
        row["Egresos_totales"] = row["Costo_operacional"] + row["CAC"] + row["G_adm"] + row["RRHH"]
        row["EBITDA"] = row["Ingresos"] - row["Egresos_totales"]
        previous_cash += row["EBITDA"]
        row["Caja"] = previous_cash
        rows.append(row)

    df = pd.DataFrame(rows)
    df["new_customers"] = df["Adq_clientes"]
    df["period_cac_per_user"] = np.where(
        df["new_customers"] > 0, df["total_acquisition_cost"] / df["new_customers"].where(df["new_customers"] > 0, 1.0), np.nan
    )
    df["cumulative_cac_per_user"] = np.where(
        df["new_customers"].cumsum() > 0,
        df["total_acquisition_cost"].cumsum() / df["new_customers"].cumsum().where(df["new_customers"].cumsum() > 0, 1.0),
        np.nan,
    )
    df["EBITDA_acum"] = df["EBITDA"].cumsum()
    df["MoM_adq"] = df["Adq_clientes"].pct_change().replace([np.inf, -np.inf], np.nan)
    df["MoM_ingresos"] = df["Ingresos"].pct_change().replace([np.inf, -np.inf], np.nan)

    df["Ingresos_recurrentes_proxy"] = 0.0
    for service in services:
        name = service["nombre"]
        df["Ingresos_recurrentes_proxy"] += df[f"R_{name}"] * service["ticket"]
    df["ARR_pct"] = np.where(df["Ingresos"] > 0, df["Ingresos_recurrentes_proxy"] / df["Ingresos"], 0)

    return df


# Public alias from API docs.
def build_financial_model(instance: dict[str, Any]) -> pd.DataFrame:
    return build_fixed_period_financial_model(instance)

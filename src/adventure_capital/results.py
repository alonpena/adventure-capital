"""Solver result extraction."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pulp


def _value(variable: Any) -> float:
    value = pulp.value(variable)
    return 0.0 if value is None else float(value)


def _safe_div(numerator: Any, denominator: Any) -> Any:
    """Element-wise division returning NaN where the denominator is zero."""
    numerator = np.asarray(numerator, dtype=float)
    denominator = np.asarray(denominator, dtype=float)
    return np.where(denominator > 0, numerator / np.where(denominator > 0, denominator, 1.0), np.nan)


def extract_results(instance: dict[str, Any], solution: dict[str, Any] | dict[str, Any]) -> pd.DataFrame:
    """Convert PuLP variables into monthly results DataFrame."""
    variables = solution.get("variables", solution)
    services = instance["servicios"]
    rows: list[dict[str, float]] = []

    for t in instance["T"]:
        row: dict[str, float] = {
            "t": t,
            "Año": (t - 1) // 12 + 1,
            "Mes": (t - 1) % 12 + 1,
            "Vendedores": _value(variables["V"][t]),
            "Lideres": _value(variables["L"][t]),
            "CAC": _value(variables["CAC"][t]),
            "EBITDA": _value(variables["EBITDA"][t]),
            "Caja": _value(variables["Caja"][t]),
            "RRHH": instance["RRHH"][t],
            "G_adm": instance["g_adm"],
        }

        for s, service in enumerate(services):
            name = service["nombre"]
            row[f"A_{name}"] = _value(variables["A"][(s, t)])
            row[f"C_{name}"] = _value(variables["C"][(s, t)])
            row[f"R_{name}"] = _value(variables["R"][(s, t)])
            row[f"Q_{name}"] = _value(variables["Q"][(s, t)])
            row[f"I_{name}"] = _value(variables["I"][(s, t)])
            row[f"Cost_op_{name}"] = _value(variables["Cost_op"][(s, t)])
            row[f"m_op_{name}"] = _value(variables["m_op"][(s, t)])

        rows.append(row)

    df = pd.DataFrame(rows)
    names = [service["nombre"] for service in services]

    log_ceiling = instance.get("log_ceiling", {})
    if log_ceiling:
        ceiling_slack = instance.get("ceiling_slack", 0.0)
        df["Log_ceiling"] = df["t"].map(log_ceiling).astype(float)
        df["Log_ceiling_slack"] = df["Log_ceiling"] * (1 + ceiling_slack)

    df["Adq_clientes"] = df[[f"A_{name}" for name in names]].sum(axis=1)
    df["Clientes_activos"] = df[[f"C_{name}" for name in names]].sum(axis=1)
    df["Ventas_recurrentes"] = df[[f"R_{name}" for name in names]].sum(axis=1)
    df["Servicios_totales"] = df[[f"Q_{name}" for name in names]].sum(axis=1)
    df["Ingresos"] = df[[f"I_{name}" for name in names]].sum(axis=1)
    df["Costo_operacional"] = df[[f"Cost_op_{name}" for name in names]].sum(axis=1)

    channels = instance.get("channels", {})
    if channels.get("any_split"):
        service_count = len(services)
        acq_sf = variables.get("A_sf", {})
        acq_ad = variables.get("A_ad", {})
        acq_tp = variables.get("A_tp", {})
        adv_cost = variables.get("advertising_cac_cost", {})
        ad_invest = variables.get("I_ad", {})
        sf_tot, ad_tot, tp_tot, advc, iad = [], [], [], [], []
        for t in instance["T"]:
            sf_tot.append(sum(_value(acq_sf[(s, t)]) for s in range(service_count)))
            ad_tot.append(
                sum(_value(acq_ad[(s, t)]) for s in range(service_count)) if acq_ad else 0.0
            )
            tp_tot.append(
                sum(_value(acq_tp[(s, t)]) for s in range(service_count)) if acq_tp else 0.0
            )
            advc.append(_value(adv_cost[t]) if adv_cost else 0.0)
            iad.append(_value(ad_invest[t]) if ad_invest else 0.0)
        df["A_salesforce"] = sf_tot
        df["A_advertising"] = ad_tot
        df["A_third_party"] = tp_tot
        df["advertising_cac_cost"] = advc
        # Named to avoid the "I_" revenue-column prefix used by consistency checks.
        df["advertising_investment"] = iad
        total = df["Adq_clientes"]
        df["share_salesforce"] = np.where(total > 0, df["A_salesforce"] / total, 0.0)
        df["share_advertising"] = np.where(total > 0, df["A_advertising"] / total, 0.0)
        df["share_third_party"] = np.where(total > 0, df["A_third_party"] / total, 0.0)

    # CAC traceability (Phase 3). Cost components come from the MILP; all per-user
    # ratios are computed here post-solve and never enter the optimization.
    cac_component_vars = {
        "salesforce_cac_cost": variables.get("salesforce_cac_cost", {}),
        "third_party_cost": variables.get("third_party_cost", {}),
        "total_acquisition_cost": variables.get("total_acquisition_cost", {}),
    }
    for col, var_map in cac_component_vars.items():
        if var_map:
            df[col] = [_value(var_map[t]) for t in instance["T"]]
    if "third_party_cost" not in df.columns:
        df["third_party_cost"] = 0.0
    if "total_acquisition_cost" not in df.columns:
        df["total_acquisition_cost"] = df["CAC"]
    df["new_customers"] = df["Adq_clientes"]
    df["period_cac_per_user"] = _safe_div(df["total_acquisition_cost"], df["new_customers"])
    df["cumulative_cac_per_user"] = _safe_div(
        df["total_acquisition_cost"].cumsum(), df["new_customers"].cumsum()
    )

    working_capital = instance.get("parametros", {}).get("working_capital", {})
    if working_capital.get("enabled", False):
        floor = -float(instance["VC"])
        df["working_capital_floor"] = floor
        df["floor_slack"] = df["Caja"] - floor
        df["floor_hit"] = df["floor_slack"].abs() <= 1e-6
        shortfall_vars = variables.get("cash_shortfall", {})
        if shortfall_vars:
            df["diagnostic_cash_shortfall"] = [_value(shortfall_vars[t]) for t in instance["T"]]
            df["diagnostic_financing_gap"] = df["diagnostic_cash_shortfall"]

    df["Costos_totales_sin_CAC"] = df["Costo_operacional"] + df["G_adm"] + df["RRHH"]
    df["Egresos_totales"] = df["Costo_operacional"] + df["CAC"] + df["G_adm"] + df["RRHH"]
    df["EBITDA_acum"] = df["EBITDA"].cumsum()
    df["MoM_adq"] = df["Adq_clientes"].pct_change().replace([np.inf, -np.inf], np.nan)
    df["MoM_ingresos"] = df["Ingresos"].pct_change().replace([np.inf, -np.inf], np.nan)

    df["Ingresos_recurrentes_proxy"] = 0.0
    for service in services:
        name = service["nombre"]
        df["Ingresos_recurrentes_proxy"] += df[f"R_{name}"] * service["ticket"]

    df["ARR_pct"] = np.where(df["Ingresos"] > 0, df["Ingresos_recurrentes_proxy"] / df["Ingresos"], 0)
    return df


def summarize_results(df: pd.DataFrame) -> dict[str, float]:
    """Return MVP summary metrics."""
    return {
        "total_acquisition": float(df["Adq_clientes"].sum()),
        "total_revenue": float(df["Ingresos"].sum()),
        "total_ebitda": float(df["EBITDA"].sum()),
        "final_cash": float(df["Caja"].iloc[-1]),
        "minimum_cash": float(df["Caja"].min()),
        "max_sellers": float(df["Vendedores"].max()),
        "max_leaders": float(df["Lideres"].max()),
    }


# Legacy Spanish API alias.
def extraer_resultados(inst: dict[str, Any], vars_dict: dict[str, Any]) -> pd.DataFrame:
    return extract_results(inst, vars_dict)

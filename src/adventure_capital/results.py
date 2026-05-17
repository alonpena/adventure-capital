"""Solver result extraction."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pulp


def _value(variable: Any) -> float:
    value = pulp.value(variable)
    return 0.0 if value is None else float(value)


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

    df["Adq_clientes"] = df[[f"A_{name}" for name in names]].sum(axis=1)
    df["Clientes_activos"] = df[[f"C_{name}" for name in names]].sum(axis=1)
    df["Ventas_recurrentes"] = df[[f"R_{name}" for name in names]].sum(axis=1)
    df["Servicios_totales"] = df[[f"Q_{name}" for name in names]].sum(axis=1)
    df["Ingresos"] = df[[f"I_{name}" for name in names]].sum(axis=1)
    df["Costo_operacional"] = df[[f"Cost_op_{name}" for name in names]].sum(axis=1)

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

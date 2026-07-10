"""Annual aggregation tables for the standard valuation report.

Each builder returns a structured dict with:
- ``columns``: list of column headers (the first column is the row label)
- ``rows``: list of row tuples (label + numeric values per year)
- ``totals``: optional totals row
- ``unit``: display unit hint (e.g. "USD", "#", "%")

Numeric values stay as ``float`` so the renderer can decide formatting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

YEAR_LABEL = "Año"
TOTAL_LABEL = "Total"


def _service_columns(df: pd.DataFrame, prefix: str) -> list[str]:
    return [col for col in df.columns if col.startswith(prefix)]


def _service_names(services: list[dict[str, Any]] | None, columns: list[str], prefix: str) -> list[str]:
    if services:
        return [str(service.get("nombre", col[len(prefix):])) for service, col in zip(services, columns)]
    return [col[len(prefix):] for col in columns]


def _annual_sum(df: pd.DataFrame, column: str) -> pd.Series:
    return df.groupby(YEAR_LABEL)[column].sum()


def _annual_last(df: pd.DataFrame, column: str) -> pd.Series:
    return df.groupby(YEAR_LABEL)[column].last()


def _to_table(
    columns: list[str],
    rows: list[tuple[Any, ...]],
    *,
    totals: tuple[Any, ...] | None = None,
    unit: str = "",
    note: str = "",
) -> dict[str, Any]:
    return {"columns": columns, "rows": rows, "totals": totals, "unit": unit, "note": note}


def build_clients_table(optimized: pd.DataFrame, services: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Adquisición, churn promedio, stock fin de año, crecimiento del stock."""
    a_cols = _service_columns(optimized, "A_")
    c_cols = _service_columns(optimized, "C_")
    names = _service_names(services, a_cols, "A_")

    years = sorted(optimized[YEAR_LABEL].unique())
    columns = [YEAR_LABEL, "Adquisición", "Stock fin de año", "Churn anual (prom)", "Crecimiento stock (%)"]
    rows: list[tuple[Any, ...]] = []
    prev_stock: float | None = None
    for year in years:
        year_df = optimized[optimized[YEAR_LABEL] == year]
        acq = float(year_df[a_cols].to_numpy().sum())
        stock = float(year_df.iloc[-1][c_cols].to_numpy().sum())
        if services:
            churn_idx = min(int(year) - 1, len(services[0].get("churn_anual", [])) - 1)
            churn = float(
                np.mean([float(svc["churn_anual"][churn_idx]) for svc in services if svc.get("churn_anual")])
            )
        else:
            churn = float("nan")
        growth = ((stock / prev_stock) - 1) if prev_stock and prev_stock > 0 else float("nan")
        rows.append((f"Año {int(year)}", acq, stock, churn, growth))
        prev_stock = stock

    total_acq = float(optimized[a_cols].to_numpy().sum())
    final_stock = float(optimized.iloc[-1][c_cols].to_numpy().sum())
    totals = (TOTAL_LABEL, total_acq, final_stock, None, None)

    detail_columns = [YEAR_LABEL, *[f"Adq. {name}" for name in names]]
    detail_rows: list[tuple[Any, ...]] = []
    for year in years:
        year_df = optimized[optimized[YEAR_LABEL] == year]
        values = tuple(float(year_df[col].sum()) for col in a_cols)
        detail_rows.append((f"Año {int(year)}", *values))
    detail_totals = (TOTAL_LABEL, *[float(optimized[col].sum()) for col in a_cols])

    return {
        "summary": _to_table(columns, rows, totals=totals, unit="#"),
        "by_service": _to_table(detail_columns, detail_rows, totals=detail_totals, unit="#"),
        "services": names,
    }


def build_services_table(optimized: pd.DataFrame, services: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Servicios totales: ventas nuevas vs recurrentes por servicio y año."""
    q_cols = _service_columns(optimized, "Q_")
    a_cols = _service_columns(optimized, "A_")
    r_cols = _service_columns(optimized, "R_")
    names = _service_names(services, q_cols, "Q_")

    years = sorted(optimized[YEAR_LABEL].unique())
    columns = [YEAR_LABEL, "Servicios nuevos", "Servicios recurrentes", "Total servicios", "% Recurrencia"]
    rows: list[tuple[Any, ...]] = []
    for year in years:
        year_df = optimized[optimized[YEAR_LABEL] == year]
        nuevos = float(year_df[a_cols].to_numpy().sum())
        recurrentes = float(year_df[r_cols].to_numpy().sum())
        totales = float(year_df[q_cols].to_numpy().sum())
        pct_rec = (recurrentes / totales) if totales > 0 else float("nan")
        rows.append((f"Año {int(year)}", nuevos, recurrentes, totales, pct_rec))

    total_nuevos = float(optimized[a_cols].to_numpy().sum())
    total_rec = float(optimized[r_cols].to_numpy().sum())
    total_servicios = float(optimized[q_cols].to_numpy().sum())
    totals = (TOTAL_LABEL, total_nuevos, total_rec, total_servicios, None)

    detail_columns = [YEAR_LABEL, *names]
    detail_rows: list[tuple[Any, ...]] = []
    for year in years:
        year_df = optimized[optimized[YEAR_LABEL] == year]
        values = tuple(float(year_df[col].sum()) for col in q_cols)
        detail_rows.append((f"Año {int(year)}", *values))
    detail_totals = (TOTAL_LABEL, *[float(optimized[col].sum()) for col in q_cols])

    params_rows: list[tuple[Any, ...]] = []
    if services:
        params_columns = ["Servicio", "Ticket (USD)", "Frecuencia (meses)", "α repetición", "Churn año 1 (%)"]
        for svc, name in zip(services, names):
            params_rows.append(
                (
                    name,
                    float(svc.get("ticket", 0.0)),
                    float(svc.get("frecuencia", 0.0)),
                    float(svc.get("alpha", 0.0)),
                    float(svc.get("churn_anual", [float("nan")])[0]),
                )
            )
        params = _to_table(params_columns, params_rows)
    else:
        params = _to_table([], [])

    return {
        "summary": _to_table(columns, rows, totals=totals, unit="#"),
        "by_service": _to_table(detail_columns, detail_rows, totals=detail_totals, unit="#"),
        "parameters": params,
        "services": names,
    }


def build_revenue_table(optimized: pd.DataFrame, services: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Ingresos anuales por servicio + recurrente (ARR) vs nuevo."""
    i_cols = _service_columns(optimized, "I_")
    names = _service_names(services, i_cols, "I_")
    years = sorted(optimized[YEAR_LABEL].unique())

    columns = [YEAR_LABEL, *names, TOTAL_LABEL, "Recurrentes (proxy)", "ARR (%)"]
    rows: list[tuple[Any, ...]] = []
    for year in years:
        year_df = optimized[optimized[YEAR_LABEL] == year]
        per_service = tuple(float(year_df[col].sum()) for col in i_cols)
        total = float(sum(per_service))
        recurrente = float(year_df["Ingresos_recurrentes_proxy"].sum()) if "Ingresos_recurrentes_proxy" in year_df else 0.0
        arr_pct = (recurrente / total) if total > 0 else float("nan")
        rows.append((f"Año {int(year)}", *per_service, total, recurrente, arr_pct))

    totals = (
        TOTAL_LABEL,
        *(float(optimized[col].sum()) for col in i_cols),
        float(optimized[i_cols].to_numpy().sum()),
        float(optimized["Ingresos_recurrentes_proxy"].sum()) if "Ingresos_recurrentes_proxy" in optimized else 0.0,
        None,
    )
    return {"summary": _to_table(columns, rows, totals=totals, unit="USD"), "services": names}


def build_cac_table(optimized: pd.DataFrame, parameters: dict[str, Any], services: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Decomposición CAC en fuerza de venta vs comisiones, por año."""
    years = sorted(optimized[YEAR_LABEL].unique())
    rem_v = float(parameters.get("rem_v", 0.0))
    rem_l = float(parameters.get("rem_l", 0.0))
    com_v = float(parameters.get("com_v", 0.0))
    com_l = float(parameters.get("com_l", 0.0))

    a_cols = _service_columns(optimized, "A_")
    tickets: dict[str, float] = {col: 0.0 for col in a_cols}
    if services:
        for service, col in zip(services, a_cols):
            tickets[col] = float(service.get("ticket", 0.0))
    base_df = optimized.copy()
    base_df["_ticket_x_acq"] = sum(base_df[col] * tickets[col] for col in a_cols) if a_cols else 0.0

    columns = [
        YEAR_LABEL,
        "Fuerza venta (USD)",
        "Líderes (USD)",
        "Comisión vendedor (USD)",
        "Comisión líder (USD)",
        "CAC total (USD)",
        "Adquisición (#)",
        "CAC por cliente (USD)",
    ]
    rows: list[tuple[Any, ...]] = []
    components_totals = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for year in years:
        year_df = base_df[base_df[YEAR_LABEL] == year]
        sales_force = float(year_df["Vendedores"].sum()) * rem_v
        leaders = float(year_df["Lideres"].sum()) * rem_l
        ticket_x_acq = float(year_df["_ticket_x_acq"].sum())
        com_vendor = ticket_x_acq * com_v
        com_leader = ticket_x_acq * com_l
        cac_total = float(year_df["CAC"].sum())
        acq = float(year_df["Adq_clientes"].sum())
        per_client = (cac_total / acq) if acq > 0 else float("nan")
        rows.append((f"Año {int(year)}", sales_force, leaders, com_vendor, com_leader, cac_total, acq, per_client))
        for idx, val in enumerate([sales_force, leaders, com_vendor, com_leader, cac_total, acq]):
            components_totals[idx] += val

    overall_acq = components_totals[5]
    overall_cac = components_totals[4]
    overall_per_client = (overall_cac / overall_acq) if overall_acq > 0 else float("nan")
    totals = (TOTAL_LABEL, *components_totals[:5], overall_acq, overall_per_client)
    return {"summary": _to_table(columns, rows, totals=totals, unit="USD")}


def build_op_cost_table(optimized: pd.DataFrame, services: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Costos operacionales anuales por servicio."""
    cost_cols = _service_columns(optimized, "Cost_op_")
    names = _service_names(services, cost_cols, "Cost_op_")
    years = sorted(optimized[YEAR_LABEL].unique())

    columns = [YEAR_LABEL, *names, TOTAL_LABEL, "Ingresos", "Gross Profit (%)"]
    rows: list[tuple[Any, ...]] = []
    for year in years:
        year_df = optimized[optimized[YEAR_LABEL] == year]
        per_service = tuple(float(year_df[col].sum()) for col in cost_cols)
        total = float(sum(per_service))
        revenue = float(year_df["Ingresos"].sum())
        gp = (1 - total / revenue) if revenue > 0 else float("nan")
        rows.append((f"Año {int(year)}", *per_service, total, revenue, gp))
    totals = (
        TOTAL_LABEL,
        *(float(optimized[col].sum()) for col in cost_cols),
        float(optimized[cost_cols].to_numpy().sum()),
        float(optimized["Ingresos"].sum()),
        None,
    )

    params_rows: list[tuple[Any, ...]] = []
    if services:
        params_columns = ["Servicio", "Costo variable c_u (USD)", "Costo mínimo c_min (USD)", "Capacidad u_max"]
        for svc, name in zip(services, names):
            params_rows.append(
                (
                    name,
                    float(svc.get("c_u", 0.0)),
                    float(svc.get("c_min", 0.0)),
                    float(svc.get("u_max", 0.0)),
                )
            )
        params = _to_table(params_columns, params_rows)
    else:
        params = _to_table([], [])
    return {"summary": _to_table(columns, rows, totals=totals, unit="USD"), "parameters": params}


def build_admin_table(optimized: pd.DataFrame, parameters: dict[str, Any]) -> dict[str, Any]:
    """Gastos administrativos por año."""
    years = sorted(optimized[YEAR_LABEL].unique())
    columns = [YEAR_LABEL, "Mensual (USD)", "Anual (USD)", "% Ingresos"]
    rows: list[tuple[Any, ...]] = []
    total_amount = 0.0
    for year in years:
        year_df = optimized[optimized[YEAR_LABEL] == year]
        annual = float(year_df["G_adm"].sum())
        monthly = annual / max(len(year_df), 1)
        revenue = float(year_df["Ingresos"].sum())
        pct = (annual / revenue) if revenue > 0 else float("nan")
        rows.append((f"Año {int(year)}", monthly, annual, pct))
        total_amount += annual
    totals = (TOTAL_LABEL, None, total_amount, None)
    return {"summary": _to_table(columns, rows, totals=totals, unit="USD")}


def build_hr_table(optimized: pd.DataFrame, parameters: dict[str, Any]) -> dict[str, Any]:
    """Planilla anual de RR.HH. no comercial.

    La fuerza comercial pertenece al CAC del modelo y se reporta en la sección
    CAC; aquí se muestra solo la planilla base para evitar doble lectura.
    """
    years = sorted(optimized[YEAR_LABEL].unique())
    rrhh_monthly_cfg = list(parameters.get("RRHH_mensual", []))

    columns = [
        YEAR_LABEL,
        "RR.HH. base mensual (USD)",
        "RR.HH. base anual (USD)",
        "% de ingresos",
    ]
    rows: list[tuple[Any, ...]] = []
    total_planilla = 0.0
    total_revenue = 0.0
    for idx, year in enumerate(years):
        year_df = optimized[optimized[YEAR_LABEL] == year]
        idx_clipped = min(idx, max(len(rrhh_monthly_cfg) - 1, 0)) if rrhh_monthly_cfg else 0
        monthly_base = float(rrhh_monthly_cfg[idx_clipped]) if rrhh_monthly_cfg else float(year_df["RRHH"].mean())
        annual_base = float(year_df["RRHH"].sum())
        revenue = float(year_df["Ingresos"].sum()) if "Ingresos" in year_df else 0.0
        pct = annual_base / revenue if revenue > 0 else float("nan")
        rows.append((f"Año {int(year)}", monthly_base, annual_base, pct))
        total_planilla += annual_base
        total_revenue += revenue
    totals = (TOTAL_LABEL, None, total_planilla, total_planilla / total_revenue if total_revenue > 0 else None)
    return {"summary": _to_table(columns, rows, totals=totals, unit="USD")}


def build_pnl_table(annual: pd.DataFrame) -> dict[str, Any]:
    """Estructura P&L anual."""
    if YEAR_LABEL not in annual.columns:
        return {"summary": _to_table([], [])}
    years = sorted(annual[YEAR_LABEL].unique())
    columns = [
        "Concepto",
        *[f"Año {int(y)}" for y in years],
        TOTAL_LABEL,
    ]
    def row(label: str, getter, sign: int = 1) -> tuple[Any, ...]:
        values = [sign * float(annual.loc[annual[YEAR_LABEL] == y, getter].iloc[0]) for y in years]
        return (label, *values, sum(values))

    rows = [
        row("Ingresos", "Ingresos"),
        row("(-) Costo operacional", "Costo_operacional", -1),
        row("Gross Profit", "GP", 1) if "GP" in annual.columns else _derived_row("Gross Profit", annual, years, ["Ingresos", "Costo_operacional"], signs=[1, -1]),
        row("(-) G. Administración", "G_adm", -1),
        row("(-) RR.HH.", "RRHH", -1),
        row("(-) CAC", "CAC", -1),
        row("EBITDA", "EBITDA"),
        row("(-) Impuesto", "Impuesto", -1),
        row("Flujo neto", "FC_neto"),
        row("Flujo descontado", "FC_desc"),
    ]
    return {"summary": _to_table(columns, rows, unit="USD")}


def _derived_row(label: str, annual: pd.DataFrame, years: list[float], columns: list[str], signs: list[int]) -> tuple[Any, ...]:
    values: list[float] = []
    for y in years:
        year_row = annual.loc[annual[YEAR_LABEL] == y].iloc[0]
        value = sum(s * float(year_row[col]) for s, col in zip(signs, columns))
        values.append(value)
    return (label, *values, sum(values))


def build_valuation_table(
    multiples: pd.DataFrame,
    dcf_summary: pd.DataFrame,
    document: dict[str, Any],
    base_wacc: float,
    final_cash: float,
    valuation_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resumen de valorización DCF (excluyendo múltiplos)."""
    columns = ["Componente de Valorización", "Métrica de base", "Valor (USD)"]
    rows: list[tuple[Any, ...]] = []

    val_sum = valuation_summary or {}
    vp_flujos = val_sum.get("vp_flujos") or (float(dcf_summary["FC_desc"].sum()) if "FC_desc" in dcf_summary.columns else 0.0)
    vr_nominal = val_sum.get("vr_nominal") or val_sum.get("valor_desecho_nominal") or 0.0
    vr_pv = val_sum.get("vr_pv") or val_sum.get("valor_desecho_vp") or 0.0
    vc_invested = val_sum.get("vc_invested") or 0.0
    van = val_sum.get("van") or (vp_flujos + vr_pv - vc_invested)

    rows.append(("Valor Presente de Flujos Descontados (VP)", "Flujos del horizonte", vp_flujos))
    rows.append(("Valor Residual (nominal)", "1x EBITDA anualizado", vr_nominal))
    rows.append(("Valor Residual Descontado (VP)", "Descontado a WACC", vr_pv))
    rows.append(("Capital Invertido (Caja inicial)", "Bootstrapping / VC", vc_invested))
    rows.append(("Valor Actual Neto (VAN)", "VP Flujos + VP Residual - Inversión", van))

    wacc_columns = ["Componente", "Valor"]
    wacc_rows = []
    return {
        "summary": _to_table(columns, rows, unit="USD"),
        "wacc": _to_table(wacc_columns, wacc_rows),
    }


def build_unit_economics_table(unit_economics: pd.DataFrame, optimized: pd.DataFrame, parameters: dict[str, Any]) -> dict[str, Any]:
    """Detalle de unit economics + agregación anual."""
    detail_columns = ["Unit Economic", "Definición", "Valor", "Unidad"]
    detail_rows: list[tuple[Any, ...]] = []
    if not unit_economics.empty:
        for _, row in unit_economics.iterrows():
            valor = row.get("Valor")
            unidad = str(row.get("Unidad", ""))
            if pd.notna(valor):
                val_f = float(valor)
                if "%" in unidad:
                    valor_str = f"{val_f * 100:.1f}%"
                elif "usd/cliente" in unidad.lower():
                    valor_str = f"USD {val_f:,.0f}"
                elif "usd/día" in unidad.lower():
                    valor_str = f"USD {val_f:,.0f}"
                elif "usd" in unidad.lower():
                    if val_f >= 1_000_000:
                        valor_str = f"USD {val_f / 1_000_000:.2f}M"
                    elif val_f >= 1_000:
                        valor_str = f"USD {val_f / 1_000:.1f}K"
                    else:
                        valor_str = f"USD {val_f:,.0f}"
                elif "veces/mes" in unidad:
                    valor_str = f"{val_f:.2f}"
                elif "ratio" in unidad.lower() or "x" in unidad.lower() or "×" in unidad.lower():
                    valor_str = f"{val_f:.2f}×"
                elif "clientes" in unidad:
                    valor_str = f"{int(val_f):,}"
                else:
                    valor_str = f"{val_f:,.2f}" if val_f % 1 != 0 else f"{int(val_f):,}"
            else:
                valor_str = "—"

            detail_rows.append(
                (
                    str(row.get("Unit Economic", "")),
                    str(row.get("Definición", "")),
                    valor_str,
                    unidad,
                )
            )

    years = sorted(optimized[YEAR_LABEL].unique())
    annual_columns = [YEAR_LABEL, "Adquisición", "Ingresos (USD)", "EBITDA (USD)", "Margen EBITDA (%)", "CAC promedio (USD)", "Caja fin de año (USD)"]
    annual_rows: list[tuple[Any, ...]] = []
    for year in years:
        year_df = optimized[optimized[YEAR_LABEL] == year]
        acq = float(year_df["Adq_clientes"].sum())
        rev = float(year_df["Ingresos"].sum())
        ebitda = float(year_df["EBITDA"].sum())
        margin = (ebitda / rev) if rev > 0 else float("nan")
        cac_total = float(year_df["CAC"].sum())
        avg_cac = (cac_total / acq) if acq > 0 else float("nan")
        cash_end = float(year_df["Caja"].iloc[-1])
        annual_rows.append((f"Año {int(year)}", acq, rev, ebitda, margin, avg_cac, cash_end))

    return {
        "detail": _to_table(detail_columns, detail_rows),
        "annual": _to_table(annual_columns, annual_rows),
    }


def build_sensitivity_tables(
    wacc_matrix: pd.DataFrame,
    variables: pd.DataFrame,
    breakeven: pd.DataFrame,
) -> dict[str, Any]:
    """Heatmap WACC×múltiplo, tornado y breakeven en formato tabla."""
    wacc_table: dict[str, Any] = {"columns": [], "rows": []}
    if not wacc_matrix.empty:
        clean = wacc_matrix[~wacc_matrix.get("is_ltv_cac_reference", False).astype(bool)] if "is_ltv_cac_reference" in wacc_matrix.columns else wacc_matrix
        pivot = clean.pivot_table(index="wacc", columns="ebitda_multiple", values="enterprise_value", aggfunc="mean").sort_index()
        wacc_table["columns"] = ["WACC", *[f"{c:.2f}×" for c in pivot.columns]]
        wacc_table["rows"] = [
            (f"{idx:.1%}", *[float(v) if pd.notna(v) else None for v in row.values])
            for idx, row in pivot.iterrows()
        ]
        wacc_table["unit"] = "USD"

    var_table: dict[str, Any] = {"columns": [], "rows": []}
    if not variables.empty:
        var_table["columns"] = ["Variable", "EBITDA base (USD)", "EBITDA resultante (USD)", "Efecto (%)"]
        var_table["rows"] = [
            (
                str(row["variable"]),
                float(row["baseline_ebitda"]) if pd.notna(row["baseline_ebitda"]) else None,
                float(row["result_value"]) if pd.notna(row["result_value"]) else None,
                float(row["effect_pct"]) if pd.notna(row["effect_pct"]) else None,
            )
            for _, row in variables.iterrows()
        ]
        var_table["unit"] = "USD"

    breakeven_table: dict[str, Any] = {"columns": [], "rows": []}
    if not breakeven.empty:
        breakeven_table["columns"] = ["Variable", "Valor actual", "Valor breakeven", "Variación tolerable (%)"]
        breakeven_table["rows"] = [
            (
                str(row["variable"]),
                float(row["current_value"]) if pd.notna(row["current_value"]) else None,
                float(row["breakeven_value"]) if pd.notna(row["breakeven_value"]) else None,
                float(row["variation_pct"]) if pd.notna(row["variation_pct"]) else None,
            )
            for _, row in breakeven.iterrows()
        ]

    return {"wacc": wacc_table, "variables": var_table, "breakeven": breakeven_table}


def build_all_tables(
    output_dir: str | Path,
    document: dict[str, Any],
    instance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the complete annual aggregation table set used by the report."""
    out = Path(output_dir)
    optimized = pd.read_csv(out / "optimized_results.csv")
    annual = pd.read_csv(out / "dcf_annual_summary.csv")
    multiples = pd.read_csv(out / "multiples_valuation.csv")
    unit_econ = pd.read_csv(out / "unit_economics.csv")

    wacc_matrix = pd.read_csv(out / "sensitivity_wacc_multiple.csv") if (out / "sensitivity_wacc_multiple.csv").exists() else pd.DataFrame()
    variables = pd.read_csv(out / "sensitivity_variables.csv") if (out / "sensitivity_variables.csv").exists() else pd.DataFrame()
    breakeven = pd.read_csv(out / "breakeven_variables.csv") if (out / "breakeven_variables.csv").exists() else pd.DataFrame()

    services = (instance or {}).get("servicios")
    parameters = (instance or {}).get("parametros", (instance or {}).get("params", {}))
    if not parameters:
        parameters = {k: v for k, v in (instance or {}).items() if not isinstance(v, list) and k != "servicios"}

    base_wacc = _document_wacc(document)
    final_cash = float(optimized["Caja"].iloc[-1])

    val_sum_path = out / "valuation_summary.json"
    val_sum = None
    if val_sum_path.exists():
        try:
            with val_sum_path.open("r", encoding="utf-8") as f:
                val_sum = json.load(f)
        except Exception:
            pass

    return {
        "clientes": build_clients_table(optimized, services),
        "servicios": build_services_table(optimized, services),
        "ingresos": build_revenue_table(optimized, services),
        "cac": build_cac_table(optimized, parameters, services),
        "costos_operacionales": build_op_cost_table(optimized, services),
        "administracion": build_admin_table(optimized, parameters),
        "rrhh": build_hr_table(optimized, parameters),
        "pnl": build_pnl_table(annual),
        "valorizacion": build_valuation_table(multiples, annual, document, base_wacc=base_wacc, final_cash=final_cash, valuation_summary=val_sum),
        "unit_economics": build_unit_economics_table(unit_econ, optimized, parameters),
        "sensibilidad": build_sensitivity_tables(wacc_matrix, variables, breakeven),
        "wacc_base": base_wacc,
    }


def _document_wacc(document: dict[str, Any]) -> float:
    dcf = document.get("dcf", {})
    if "tasa_descuento" in dcf:
        return float(dcf["tasa_descuento"])
    beta_capm = float(dcf.get("beta_capm", 1.0))
    rf = float(dcf.get("Rf_us", dcf.get("Rf_local", 0.0)))
    rm = float(dcf.get("Rm", 0.0))
    country_risk = float(dcf.get("country_risk", 0.0))
    risk_penalty = float(dcf.get("castigo_riesgo", 0.0))
    return rf + beta_capm * (rm - rf) + country_risk + risk_penalty

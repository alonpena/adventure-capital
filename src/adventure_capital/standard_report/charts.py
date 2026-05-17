"""Composition-aware figure catalog for the standard valuation report.

Each plot is designed to make the structure of a financial flow legible at a
glance: stacked compositions, annual totals labeled inline, decompositions of
CAC and gross margin, P&L cascade, and a sensibility view that no longer
collapses under outlier LTV/CAC reference values.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Dark theme palette aligned with the report template.
BG = "#0B1020"
PANEL = "#111827"
GRID = "#2A3344"
TEXT = "#E5E7EB"
MUTED = "#9CA3AF"
AMBER = "#F59E0B"
CYAN = "#22D3EE"
RED = "#EF4444"
GREEN = "#10B981"
PURPLE = "#A855F7"
BLUE = "#60A5FA"
PINK = "#F472B6"

SERVICE_COLORS = [AMBER, CYAN, GREEN, PURPLE, PINK, BLUE]

FIGURE_NAMES = [
    "acquisition_year1",
    "clients_evolution_36m",
    "services_new_vs_recurrent",
    "revenue_breakdown_3y",
    "revenue_monthly_composition",
    "cac_components",
    "op_cost_composition",
    "gross_margin_progression",
    "cashflow_monthly",
    "pnl_waterfall",
    "valuation_methods",
    "unit_economics_grid",
    "mapvalue_diagram",
    "sensitivity_heatmap",
    "sensitivity_tornado",
    "breakeven_chart",
    "client_revenue_36m",
]


def _style_ax(ax, title: str = "", *, ylabel: str = "", xlabel: str = "") -> None:
    if title:
        ax.set_title(title, color=TEXT, fontsize=14, fontweight="bold", pad=14)
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=MUTED, labelsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED, fontsize=11)
    if xlabel:
        ax.set_xlabel(xlabel, color=MUTED, fontsize=11)
    for spine_name, spine in ax.spines.items():
        if spine_name in {"top", "right"}:
            spine.set_visible(False)
        else:
            spine.set_color(GRID)
    ax.grid(color=GRID, alpha=0.4, axis="y", linestyle="--", linewidth=0.6)


def _save(fig, path: Path) -> None:
    fig.patch.set_facecolor(BG)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _service_columns(df: pd.DataFrame, prefix: str) -> list[str]:
    return [col for col in df.columns if col.startswith(prefix)]


def _format_money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f}K"
    return f"{value:,.0f}"


def _format_pct(value: float) -> str:
    return f"{value * 100:.0f}%"


# ---------- Clientes ----------

def _plot_acquisition_year1(df: pd.DataFrame, path: Path) -> None:
    year1 = df[df["Año"] == 1]
    cols = _service_columns(year1, "A_")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    colors = SERVICE_COLORS[: len(cols)]
    months = year1["Mes"].to_numpy()
    series = [year1[col].to_numpy() for col in cols]
    ax.stackplot(months, series, labels=[c[2:] for c in cols], colors=colors, alpha=0.92, edgecolor=BG)
    totals = np.sum(series, axis=0)
    for x, y in zip(months, totals):
        if y > 0:
            ax.text(x, y + 0.4, f"{int(y)}", ha="center", va="bottom", color=TEXT, fontsize=9)
    _style_ax(ax, "Adquisición Año 1 por servicio", ylabel="Clientes nuevos/mes", xlabel="Mes")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, loc="upper left", fontsize=10, ncol=len(cols))
    _save(fig, path)


def _plot_clients_evolution(df: pd.DataFrame, path: Path) -> None:
    cols = _service_columns(df, "C_")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    colors = SERVICE_COLORS[: len(cols)]
    months = df["t"].to_numpy()
    series = [df[col].to_numpy() for col in cols]
    ax.stackplot(months, series, labels=[c[2:] for c in cols], colors=colors, alpha=0.9, edgecolor=BG)
    total = df["Clientes_activos"].to_numpy()
    ax.plot(months, total, color=TEXT, linewidth=1.5, linestyle="--", alpha=0.6)
    # Year boundaries
    year_ends = df.groupby("Año")["t"].max().to_list()
    for ye in year_ends:
        ax.axvline(ye + 0.5, color=GRID, linestyle=":", linewidth=0.8)
    # Annotate stock at year end
    for ye in year_ends:
        stock = float(df.loc[df["t"] == ye, "Clientes_activos"].iloc[0])
        ax.text(ye, stock + 8, f"{stock:.0f}", color=TEXT, fontsize=9, ha="center", fontweight="bold")
    _style_ax(ax, "Evolución de stock de clientes por servicio", ylabel="Clientes activos", xlabel="Mes")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, loc="upper left", fontsize=10, ncol=len(cols))
    _save(fig, path)


def _plot_client_revenue(df: pd.DataFrame, path: Path) -> None:
    """Kept name for backward compatibility — repurposed to clients & revenue dual."""
    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    ax1.fill_between(df["t"], df["Clientes_activos"], color=CYAN, alpha=0.2)
    ax1.plot(df["t"], df["Clientes_activos"], color=CYAN, linewidth=2.4, label="Clientes activos")
    ax1.set_ylabel("Clientes activos", color=CYAN, fontsize=11)
    ax1.tick_params(axis="y", colors=CYAN)
    ax2 = ax1.twinx()
    ax2.plot(df["t"], df["Ingresos"], color=AMBER, linewidth=2.4, label="Ingresos USD")
    ax2.set_ylabel("Ingresos (USD)", color=AMBER, fontsize=11)
    ax2.tick_params(axis="y", colors=AMBER)
    for spine in ax2.spines.values():
        spine.set_visible(False)
    _style_ax(ax1, "Clientes activos vs ingresos mensuales", xlabel="Mes")
    _save(fig, path)


# ---------- Servicios ----------

def _plot_services_new_vs_recurrent(df: pd.DataFrame, path: Path) -> None:
    a_cols = _service_columns(df, "A_")
    r_cols = _service_columns(df, "R_")
    annual_new = df.groupby("Año")[a_cols].sum().sum(axis=1)
    annual_rec = df.groupby("Año")[r_cols].sum().sum(axis=1)
    years = annual_new.index.astype(int)
    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars_new = ax.bar(x, annual_new.values, color=AMBER, label="Servicios nuevos", edgecolor=BG)
    bars_rec = ax.bar(x, annual_rec.values, bottom=annual_new.values, color=CYAN, label="Servicios recurrentes", edgecolor=BG)
    totals = annual_new.values + annual_rec.values
    for xi, total, n, r in zip(x, totals, annual_new.values, annual_rec.values):
        ax.text(xi, total + max(totals) * 0.02, f"{int(total)}", ha="center", color=TEXT, fontsize=11, fontweight="bold")
        if n > 0:
            ax.text(xi, n / 2, f"{int(n)}", ha="center", va="center", color=BG, fontsize=10, fontweight="bold")
        if r > 0:
            ax.text(xi, n + r / 2, f"{int(r)}", ha="center", va="center", color=BG, fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Año {y}" for y in years])
    _style_ax(ax, "Servicios anuales: nuevos vs recurrentes", ylabel="Servicios entregados", xlabel="")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, loc="upper left")
    _save(fig, path)


# ---------- Ingresos ----------

def _plot_revenue_breakdown(df: pd.DataFrame, path: Path) -> None:
    cols = _service_columns(df, "I_")
    annual = df.groupby("Año")[cols].sum()
    years = annual.index.astype(int)
    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(11, 5.5))
    totals = annual.sum(axis=1).values
    max_total = max(totals) if len(totals) else 0
    threshold = max_total * 0.04
    n_years = len(years)
    n_layers = len(cols)
    # Identify topmost segment per bar (last layer above threshold)
    bottom = np.zeros(n_years)
    top_indices = np.full(n_years, -1, dtype=int)
    for li, col in enumerate(cols):
        for yi, v in enumerate(annual[col].values):
            if v > threshold:
                top_indices[yi] = li
        bottom += annual[col].values
    bottom = np.zeros(n_years)
    colors = SERVICE_COLORS[: len(cols)]
    for li, (col, color) in enumerate(zip(cols, colors)):
        values = annual[col].values
        ax.bar(x, values, bottom=bottom, color=color, label=col[2:], edgecolor=BG, linewidth=0.5)
        for xi, v, b, yi in zip(x, values, bottom, range(n_years)):
            if v > threshold:
                offset = v * 0.35 if top_indices[yi] == li else v / 2
                ax.text(xi, b + offset, _format_money(v), ha="center", va="center",
                        color=BG, fontsize=9, fontweight="bold")
        bottom += values
    ax.set_ylim(0, max_total * 1.18)
    for xi, t in zip(x, totals):
        ax.text(xi, t + max_total * 0.04, _format_money(t), ha="center", color=TEXT, fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Año {y}" for y in years])
    _style_ax(ax, "Ingresos anuales por servicio", ylabel="USD")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, loc="upper center",
              ncol=len(cols), bbox_to_anchor=(0.5, -0.10))
    _save(fig, path)


def _plot_revenue_monthly_composition(df: pd.DataFrame, path: Path) -> None:
    cols = _service_columns(df, "I_")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    months = df["t"].to_numpy()
    colors = SERVICE_COLORS[: len(cols)]
    series = [df[col].to_numpy() for col in cols]
    ax.stackplot(months, series, labels=[c[2:] for c in cols], colors=colors, alpha=0.92, edgecolor=BG)
    year_ends = df.groupby("Año")["t"].max().to_list()
    for ye in year_ends:
        ax.axvline(ye + 0.5, color=GRID, linestyle=":", linewidth=0.8)
    _style_ax(ax, "Ingresos mensuales por servicio (36 meses)", ylabel="USD/mes", xlabel="Mes")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, loc="upper left", ncol=len(cols))
    _save(fig, path)


# ---------- CAC ----------

def _plot_cac_components(df: pd.DataFrame, parameters: dict[str, Any], services: list[dict[str, Any]] | None, path: Path) -> None:
    rem_v = float(parameters.get("rem_v", 0.0))
    rem_l = float(parameters.get("rem_l", 0.0))
    com_v = float(parameters.get("com_v", 0.0))
    com_l = float(parameters.get("com_l", 0.0))

    a_cols = _service_columns(df, "A_")
    tickets = {col: 0.0 for col in a_cols}
    if services:
        for service, col in zip(services, a_cols):
            tickets[col] = float(service.get("ticket", 0.0))
    df = df.copy()
    df["_ticket_x_acq"] = sum(df[col] * tickets[col] for col in a_cols) if a_cols else 0.0

    annual = df.groupby("Año").agg({"Vendedores": "sum", "Lideres": "sum", "_ticket_x_acq": "sum", "CAC": "sum"})
    annual["fuerza_v"] = annual["Vendedores"] * rem_v
    annual["fuerza_l"] = annual["Lideres"] * rem_l
    annual["com_v"] = annual["_ticket_x_acq"] * com_v
    annual["com_l"] = annual["_ticket_x_acq"] * com_l

    years = annual.index.astype(int)
    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(11, 5.5))
    layers = [
        ("Fuerza venta", annual["fuerza_v"].values, AMBER),
        ("Líderes", annual["fuerza_l"].values, CYAN),
        ("Comisión vendedor", annual["com_v"].values, GREEN),
        ("Comisión líder", annual["com_l"].values, PURPLE),
    ]
    totals = annual["CAC"].values
    max_total = max(totals) if len(totals) else 0
    label_threshold = max_total * 0.04
    # Track the top of each segment to find which is topmost per bar.
    n_years = len(years)
    n_layers = len(layers)
    bottom = np.zeros(n_years)
    top_indices = np.full(n_years, -1, dtype=int)
    for li, (label, values, color) in enumerate(layers):
        for yi, v in enumerate(values):
            if v > label_threshold:
                top_indices[yi] = li
        bottom += values
    # Reset and draw with labels, skipping the topmost segment per bar to avoid total collision.
    bottom = np.zeros(n_years)
    for li, (label, values, color) in enumerate(layers):
        ax.bar(x, values, bottom=bottom, color=color, label=label, edgecolor=BG, linewidth=0.5)
        for xi, v, b, yi in zip(x, values, bottom, range(n_years)):
            if v > label_threshold and top_indices[yi] != li:
                ax.text(xi, b + v / 2, _format_money(v), ha="center", va="center",
                        color=BG, fontsize=9, fontweight="bold")
            elif v > label_threshold and top_indices[yi] == li:
                # Place topmost segment label nearer to its bottom so it stays inside the segment
                ax.text(xi, b + v * 0.35, _format_money(v), ha="center", va="center",
                        color=BG, fontsize=9, fontweight="bold")
        bottom += values
    ax.set_ylim(0, max_total * 1.25)
    for xi, t in zip(x, totals):
        ax.text(xi, t + max_total * 0.06, _format_money(t), ha="center",
                color=TEXT, fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Año {y}" for y in years])
    _style_ax(ax, "Componentes del CAC anual", ylabel="USD")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, loc="upper center",
              ncol=4, bbox_to_anchor=(0.5, -0.10))
    _save(fig, path)


# ---------- Costos operacionales ----------

def _plot_op_cost_composition(df: pd.DataFrame, path: Path) -> None:
    cols = _service_columns(df, "Cost_op_")
    annual = df.groupby("Año")[cols].sum()
    years = annual.index.astype(int)
    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(11, 5.5))
    bottom = np.zeros(len(years))
    colors = SERVICE_COLORS[: len(cols)]
    for col, color in zip(cols, colors):
        values = annual[col].values
        ax.bar(x, values, bottom=bottom, color=color, label=col.replace("Cost_op_", ""), edgecolor=BG, linewidth=0.5)
        bottom += values
    totals = annual.sum(axis=1).values
    max_total = max(totals) if len(totals) else 0
    ax.set_ylim(0, max_total * 1.18)
    for xi, t in zip(x, totals):
        ax.text(xi, t + max_total * 0.04, _format_money(t), ha="center", color=TEXT, fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Año {y}" for y in years])
    _style_ax(ax, "Costos operacionales por servicio (anual)", ylabel="USD")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, loc="upper center",
              ncol=len(cols), bbox_to_anchor=(0.5, -0.10))
    _save(fig, path)


def _plot_gross_margin_cascade(df: pd.DataFrame, path: Path) -> None:
    annual = df.groupby("Año").agg({"Ingresos": "sum", "Costo_operacional": "sum"})
    annual["GP"] = annual["Ingresos"] - annual["Costo_operacional"]
    years = annual.index.astype(int)
    x = np.arange(len(years))
    width = 0.28
    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars_rev = ax.bar(x - width, annual["Ingresos"].values, width, color=AMBER, label="Ingresos", edgecolor=BG)
    bars_cost = ax.bar(x, annual["Costo_operacional"].values, width, color=RED, label="Costo operacional", edgecolor=BG)
    bars_gp = ax.bar(x + width, annual["GP"].values, width, color=GREEN, label="Gross Profit", edgecolor=BG)
    for bars in (bars_rev, bars_cost, bars_gp):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + max(annual["Ingresos"].values) * 0.015,
                    _format_money(h), ha="center", color=TEXT, fontsize=9, fontweight="bold")
    # GP% annotation
    for xi, gp, rev in zip(x, annual["GP"].values, annual["Ingresos"].values):
        if rev > 0:
            ax.text(xi + width, gp + max(annual["Ingresos"].values) * 0.05, f"GP {gp / rev * 100:.1f}%",
                    ha="center", color=GREEN, fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Año {y}" for y in years])
    _style_ax(ax, "Cascada de margen bruto anual", ylabel="USD")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, loc="upper left", ncol=3)
    _save(fig, path)


# ---------- Cashflow / P&L ----------

def _plot_cashflow(df: pd.DataFrame, path: Path) -> None:
    """Stacked composition of monthly cashflow: revenue vs all costs + EBITDA + cumulative cash."""
    months = df["t"].to_numpy()
    ingresos = df["Ingresos"].to_numpy()
    cost_op = -df["Costo_operacional"].to_numpy()
    cac = -df["CAC"].to_numpy()
    gadm = -df["G_adm"].to_numpy()
    rrhh = -df["RRHH"].to_numpy()
    impuesto = -df["Impuesto"].to_numpy() if "Impuesto" in df.columns else np.zeros(len(df))
    ebitda = df["EBITDA"].to_numpy()
    fc_acum = np.cumsum(df["FC_neto"].to_numpy()) if "FC_neto" in df.columns else np.cumsum(ebitda)

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(months, ingresos, color=GREEN, label="Ingresos", edgecolor=BG, linewidth=0.3)
    # Stacked negatives
    bottom = np.zeros(len(df))
    for label, values, color in [
        ("Costo operacional", cost_op, "#7F1D1D"),
        ("CAC", cac, RED),
        ("G. administrativo", gadm, "#F472B6"),
        ("RR.HH.", rrhh, "#A855F7"),
        ("Impuesto", impuesto, "#FB923C"),
    ]:
        ax1.bar(months, values, bottom=bottom, color=color, label=label, edgecolor=BG, linewidth=0.3)
        bottom += values
    ax1.plot(months, ebitda, color=AMBER, linewidth=2.4, label="EBITDA")
    ax1.axhline(0, color=TEXT, linewidth=0.8, alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(months, fc_acum, color=CYAN, linewidth=2.2, linestyle="--", label="FC neto acumulado")
    ax2.set_ylabel("FC neto acumulado (USD)", color=CYAN, fontsize=11)
    ax2.tick_params(axis="y", colors=CYAN)
    for spine in ax2.spines.values():
        spine.set_visible(False)

    _style_ax(ax1, "Cashflow mensual: composición de ingresos y egresos", ylabel="USD/mes", xlabel="Mes")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, facecolor=PANEL, labelcolor=TEXT,
               edgecolor=GRID, loc="upper left", fontsize=9, ncol=4)
    _save(fig, path)


def _plot_pnl_waterfall(annual: pd.DataFrame, path: Path) -> None:
    last = annual.iloc[-1]
    items = [
        ("Ingresos", float(last["Ingresos"]), GREEN),
        ("Costo op.", -float(last["Costo_operacional"]), RED),
        ("G. Admin", -float(last["G_adm"]), "#F472B6"),
        ("RR.HH.", -float(last["RRHH"]), PURPLE),
        ("CAC", -float(last["CAC"]), "#FB923C"),
    ]
    ebitda = float(last["EBITDA"])
    impuesto = -float(last["Impuesto"]) if "Impuesto" in annual.columns else 0.0
    fc = float(last["FC_neto"]) if "FC_neto" in annual.columns else ebitda

    fig, ax = plt.subplots(figsize=(11, 5.5))
    running = 0.0
    positions = []
    heights = []
    bottoms = []
    colors = []
    labels = []
    for name, value, color in items:
        positions.append(name)
        if value >= 0:
            bottoms.append(running)
            heights.append(value)
        else:
            bottoms.append(running + value)
            heights.append(-value)
        colors.append(color)
        running += value
        labels.append(value)
    # EBITDA totalizer
    positions.append("EBITDA")
    bottoms.append(0)
    heights.append(ebitda)
    colors.append(AMBER)
    labels.append(ebitda)

    if "Impuesto" in annual.columns:
        positions.append("Impuesto")
        bottoms.append(ebitda + impuesto)
        heights.append(-impuesto)
        colors.append(RED)
        labels.append(impuesto)
        positions.append("FC neto")
        bottoms.append(0)
        heights.append(fc)
        colors.append(CYAN)
        labels.append(fc)

    x = np.arange(len(positions))
    bars = ax.bar(x, heights, bottom=bottoms, color=colors, edgecolor=BG)
    for bar, label_value in zip(bars, labels):
        h = bar.get_height() + bar.get_y()
        ax.text(bar.get_x() + bar.get_width() / 2, h + max(heights) * 0.02,
                _format_money(label_value), ha="center", color=TEXT, fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(positions, rotation=20, ha="right")
    _style_ax(ax, f"Cascada P&L Año {int(last['Año'])}", ylabel="USD")
    _save(fig, path)


# ---------- Valoración ----------

def _plot_valuation_methods(multiples: pd.DataFrame, dcf_summary: pd.DataFrame, final_cash: float, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    methods: list[tuple[str, float, str]] = []
    if not multiples.empty:
        for _, row in multiples.iterrows():
            methods.append((str(row["Método"]), float(row["Valorización"]), AMBER))
    pv_flows = float(dcf_summary["FC_desc"].sum()) if "FC_desc" in dcf_summary.columns else 0.0
    methods.append(("VAN flujos descontados", pv_flows, CYAN))
    methods.append(("VAN + caja final", pv_flows + final_cash, GREEN))

    labels = [m[0] for m in methods]
    values = [m[1] for m in methods]
    colors = [m[2] for m in methods]
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=colors, edgecolor=BG)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + max(values) * 0.02,
                _format_money(value), ha="center", color=TEXT, fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    _style_ax(ax, "Valorización por método", ylabel="USD")
    _save(fig, path)


# ---------- Unit Economics ----------

def _plot_unit_grid(df: pd.DataFrame, path: Path) -> None:
    rows = df.head(12).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(13, 7.5))
    ax.axis("off")
    cols = 3
    rows_n = (len(rows) + cols - 1) // cols
    pad = 0.02
    cell_w = (1 - (cols + 1) * pad) / cols
    cell_h = (1 - (rows_n + 1) * pad) / rows_n
    for idx, row in rows.iterrows():
        c = idx % cols
        r = idx // cols
        x = pad + c * (cell_w + pad)
        y = 1 - pad - (r + 1) * cell_h - r * pad
        ax.add_patch(plt.Rectangle((x, y), cell_w, cell_h, color=PANEL, ec=GRID))
        ax.text(x + 0.015, y + cell_h - 0.04, str(row["Unit Economic"]), color=AMBER, fontsize=11, fontweight="bold")
        valor = row["Valor"]
        valor_str = "—" if pd.isna(valor) else f"{float(valor):,.2f}"
        ax.text(x + 0.015, y + cell_h * 0.45, valor_str, color=TEXT, fontsize=18, fontweight="bold")
        ax.text(x + 0.015, y + 0.02, str(row["Unidad"]), color=MUTED, fontsize=9)
    ax.set_title("Dashboard de unit economics", color=TEXT, fontsize=15, fontweight="bold", pad=14)
    fig.patch.set_facecolor(BG)
    _save(fig, path)


# ---------- MapValue ----------

def _plot_mapvalue(path: Path, mapvalue_path: Path) -> None:
    data = json.loads(mapvalue_path.read_text(encoding="utf-8"))
    layers = data.get("layers", {})
    layer_labels = {
        "input_variables": "Variables\nde entrada",
        "operating_flows": "Flujos\noperativos",
        "financial_results": "Resultados\nfinancieros",
        "valuation": "Valorización",
    }
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.axis("off")
    fig.patch.set_facecolor(BG)
    layer_keys = list(layer_labels.keys())
    x_positions = [0.02, 0.27, 0.52, 0.77]
    width = 0.21
    height = 0.78

    def _format_layer_value(key: str, value: Any) -> str:
        if isinstance(value, (int, float)):
            if "cash" in key or "revenue" in key or "ebitda" in key or "ltv" in key or "cac" in key or "investment" in key:
                return _format_money(float(value))
            if isinstance(value, float):
                return f"{value:,.2f}"
            return f"{value:,}"
        return str(value) if value is not None else "—"

    for x, key in zip(x_positions, layer_keys):
        ax.add_patch(plt.Rectangle((x, 0.10), width, height, color=PANEL, ec=AMBER, lw=1.5))
        ax.text(x + width / 2, 0.83, layer_labels[key], color=AMBER, fontsize=13, fontweight="bold",
                ha="center", va="center")
        items = layers.get(key, {}) or {}
        y_cursor = 0.72
        for inner_key, value in items.items():
            label = inner_key.replace("_", " ").capitalize()
            ax.text(x + 0.01, y_cursor, label, color=MUTED, fontsize=9)
            ax.text(x + width - 0.01, y_cursor, _format_layer_value(inner_key, value),
                    color=TEXT, fontsize=10, fontweight="bold", ha="right")
            y_cursor -= 0.07
    # Arrows
    for i in range(len(layer_keys) - 1):
        x_start = x_positions[i] + width
        x_end = x_positions[i + 1]
        ax.annotate("", xy=(x_end, 0.5), xytext=(x_start, 0.5),
                    arrowprops={"arrowstyle": "->", "color": CYAN, "lw": 2.4})
    ax.set_title("MapValue: variables → flujos → resultados → valorización",
                 color=TEXT, fontsize=15, fontweight="bold", pad=14)
    _save(fig, path)


# ---------- Sensibilidad ----------

def _plot_heatmap(df: pd.DataFrame, base_wacc: float | None, path: Path) -> None:
    clean = df.copy()
    if "is_ltv_cac_reference" in clean.columns:
        clean = clean[~clean["is_ltv_cac_reference"].astype(bool)]
    pivot = clean.pivot_table(index="wacc", columns="ebitda_multiple", values="enterprise_value", aggfunc="mean").sort_index()
    pivot = pivot.sort_index(ascending=True)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    im = ax.imshow(pivot.values / 1_000_000, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{c:.2f}×" for c in pivot.columns], rotation=30, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([f"{i:.1%}" for i in pivot.index])
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            value = pivot.values[i, j] / 1_000_000
            ax.text(j, i, f"{value:.2f}M", ha="center", va="center", color=TEXT, fontsize=9, fontweight="bold")
    if base_wacc is not None and len(pivot.index) > 0:
        index_values = np.asarray(pivot.index, dtype=float)
        closest_row = int(np.argmin(np.abs(index_values - float(base_wacc))))
        ax.axhline(closest_row, color=AMBER, linewidth=1.3, alpha=0.6)
    _style_ax(ax, "Sensibilidad WACC × múltiplo EBITDA (USD MM)", ylabel="WACC", xlabel="Múltiplo EBITDA")
    cbar = fig.colorbar(im, ax=ax)
    cbar.ax.tick_params(colors=MUTED)
    cbar.outline.set_edgecolor(GRID)
    cbar.set_label("Enterprise value (USD MM)", color=MUTED)
    _save(fig, path)


def _plot_sensitivity_tornado(df: pd.DataFrame, path: Path) -> None:
    if df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.axis("off")
        ax.text(0.5, 0.5, "Sin datos de sensibilidad", color=TEXT, ha="center", va="center", fontsize=14)
        _save(fig, path)
        return
    plot_df = df[df["variable"] != "Referencia LTV/CAC"].copy()
    plot_df = plot_df.sort_values("effect_pct", key=lambda s: s.abs(), ascending=True)
    values = plot_df["effect_pct"].fillna(0).values * 100
    colors = [GREEN if v >= 0 else RED for v in values]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    y = np.arange(len(plot_df))
    bars = ax.barh(y, values, color=colors, edgecolor=BG)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["variable"].tolist(), color=TEXT)
    span = max(abs(values).max() if values.size else 1.0, 1.0)
    pad = span * 0.06
    ax.set_xlim(-span * 1.25, span * 1.25)
    for bar, pct in zip(bars, values):
        if pct >= 0:
            ax.text(bar.get_width() + pad, bar.get_y() + bar.get_height() / 2,
                    f"{pct:+.1f}%", va="center", ha="left",
                    color=TEXT, fontsize=10, fontweight="bold")
        else:
            ax.text(bar.get_width() - pad, bar.get_y() + bar.get_height() / 2,
                    f"{pct:+.1f}%", va="center", ha="right",
                    color=TEXT, fontsize=10, fontweight="bold")
    ax.axvline(0, color=TEXT, linewidth=0.8, alpha=0.5)
    _style_ax(ax, "Tornado: efecto sobre EBITDA total (%)", xlabel="Variación %")
    _save(fig, path)


def _plot_breakeven(df: pd.DataFrame, path: Path) -> None:
    if df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.axis("off")
        ax.text(0.5, 0.5, "Sin datos de breakeven", color=TEXT, ha="center", va="center", fontsize=14)
        _save(fig, path)
        return
    variables = df["variable"].tolist()
    current = df["current_value"].astype(float).values
    breakeven = df["breakeven_value"].astype(float).values
    variations = df["variation_pct"].astype(float).values
    x = np.arange(len(variables))
    width = 0.36
    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars_current = ax.bar(x - width / 2, current, width, color=AMBER, label="Valor actual", edgecolor=BG)
    bars_break = ax.bar(x + width / 2, breakeven, width, color=CYAN, label="Valor breakeven", edgecolor=BG)
    max_v = max(np.max(current) if len(current) else 0, np.max(breakeven) if len(breakeven) else 0)
    ax.set_ylim(0, max_v * 1.35)
    for bar, v in list(zip(bars_current, current)) + list(zip(bars_break, breakeven)):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_v * 0.02,
                _format_money(v), ha="center", color=TEXT, fontsize=9, fontweight="bold")
    for xi, c_, b_, variation in zip(x, current, breakeven, variations):
        ax.text(xi, max_v * 1.22, f"{variation * 100:+.1f}%", ha="center",
                color=GREEN if variation >= 0 else RED, fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(variables)
    _style_ax(ax, "Variables para EBITDA = 0", ylabel="USD")
    ax.legend(facecolor=PANEL, labelcolor=TEXT, edgecolor=GRID, loc="upper center",
              ncol=2, bbox_to_anchor=(0.5, -0.06))
    _save(fig, path)


def generate_figures(output_dir: str | Path, *, instance: dict[str, Any] | None = None, base_wacc: float | None = None) -> dict[str, Path]:
    """Generate composition-aware figure catalog for the standard report."""
    out = Path(output_dir)
    figures = out / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    optimized = pd.read_csv(out / "optimized_results.csv")
    dcf = pd.read_csv(out / "dcf_cashflow.csv")
    annual = pd.read_csv(out / "dcf_annual_summary.csv")
    unit = pd.read_csv(out / "unit_economics.csv")
    multiples = pd.read_csv(out / "multiples_valuation.csv")
    sensitivity = pd.read_csv(out / "sensitivity_wacc_multiple.csv") if (out / "sensitivity_wacc_multiple.csv").exists() else pd.DataFrame()
    variables = pd.read_csv(out / "sensitivity_variables.csv") if (out / "sensitivity_variables.csv").exists() else pd.DataFrame()
    breakeven = pd.read_csv(out / "breakeven_variables.csv") if (out / "breakeven_variables.csv").exists() else pd.DataFrame()

    parameters: dict[str, Any] = {}
    if instance:
        parameters = instance.get("parametros", instance.get("params", {})) or {}
        if not parameters:
            parameters = {k: v for k, v in instance.items() if not isinstance(v, list) and k != "servicios"}

    paths = {name: figures / f"{name}.png" for name in FIGURE_NAMES}
    _plot_acquisition_year1(optimized, paths["acquisition_year1"])
    _plot_clients_evolution(optimized, paths["clients_evolution_36m"])
    _plot_services_new_vs_recurrent(optimized, paths["services_new_vs_recurrent"])
    _plot_revenue_breakdown(optimized, paths["revenue_breakdown_3y"])
    _plot_revenue_monthly_composition(optimized, paths["revenue_monthly_composition"])
    services = (instance or {}).get("servicios") if instance else None
    _plot_cac_components(optimized, parameters, services, paths["cac_components"])
    _plot_op_cost_composition(optimized, paths["op_cost_composition"])
    _plot_gross_margin_cascade(optimized, paths["gross_margin_progression"])
    _plot_cashflow(dcf, paths["cashflow_monthly"])
    _plot_pnl_waterfall(annual, paths["pnl_waterfall"])
    final_cash = float(optimized["Caja"].iloc[-1])
    _plot_valuation_methods(multiples, annual, final_cash, paths["valuation_methods"])
    _plot_unit_grid(unit, paths["unit_economics_grid"])
    _plot_mapvalue(paths["mapvalue_diagram"], out / "mapvalue.json")
    if not sensitivity.empty:
        _plot_heatmap(sensitivity, base_wacc, paths["sensitivity_heatmap"])
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.axis("off")
        ax.text(0.5, 0.5, "Sin matriz de sensibilidad", color=TEXT, ha="center", va="center", fontsize=14)
        _save(fig, paths["sensitivity_heatmap"])
    _plot_sensitivity_tornado(variables, paths["sensitivity_tornado"])
    _plot_breakeven(breakeven, paths["breakeven_chart"])
    _plot_client_revenue(optimized, paths["client_revenue_36m"])
    return paths

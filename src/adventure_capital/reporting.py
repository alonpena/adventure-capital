"""Business-facing report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


CSV_OUTPUTS = {
    "fixed_cashflow": "fixed_cashflow.csv",
    "optimized_results": "optimized_results.csv",
    "dcf_cashflow": "dcf_cashflow.csv",
    "dcf_annual_summary": "dcf_annual_summary.csv",
    "multiples_valuation": "multiples_valuation.csv",
    "unit_economics": "unit_economics.csv",
}


def _money(value: float) -> str:
    return f"USD {value:,.0f}"


def _number(value: float) -> str:
    return f"{value:,.0f}"


def write_core_csv_outputs(result: dict[str, Any], output_dir: str | Path) -> dict[str, Path]:
    """Write core CSV outputs consumed by reports and downstream analysis."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = {
        "fixed_cashflow": out / CSV_OUTPUTS["fixed_cashflow"],
        "optimized_results": out / CSV_OUTPUTS["optimized_results"],
        "dcf_cashflow": out / CSV_OUTPUTS["dcf_cashflow"],
        "dcf_annual_summary": out / CSV_OUTPUTS["dcf_annual_summary"],
        "multiples_valuation": out / CSV_OUTPUTS["multiples_valuation"],
        "unit_economics": out / CSV_OUTPUTS["unit_economics"],
    }

    result["fixed_cashflow"].to_csv(paths["fixed_cashflow"], index=False)
    result["optimized_results"].to_csv(paths["optimized_results"], index=False)
    result["dcf"]["df_flujo_caja"].to_csv(paths["dcf_cashflow"], index=False)
    result["dcf"]["resumen_anual_dcf"].to_csv(paths["dcf_annual_summary"])
    result["multiples_valuation"]["df_multiplos"].to_csv(paths["multiples_valuation"], index=False)
    result["unit_economics"].to_csv(paths["unit_economics"], index=False)

    import json
    summary_data = {
        "vc_invested": float(result["instance"]["VC"]),
        "van": float(result["dcf"]["VAN"]),
        "vr_nominal": float(result["dcf"]["vr_nominal"]),
        "vr_pv": float(result["dcf"]["vr_pv"]),
        "valor_desecho_nominal": float(result["dcf"]["valor_desecho_nominal"]),
        "valor_desecho_vp": float(result["dcf"]["valor_desecho_vp"]),
        "beta_anual": float(result["dcf"]["beta_anual"]),
        "beta_mensual": float(result["dcf"]["beta_mensual"]),
        "ebitda_ultimo_mes": float(result["dcf"]["ebitda_ultimo_mes"]),
        "ebitda_anualizado": float(result["dcf"]["ebitda_anualizado"]),
    }
    (out / "summary.json").write_text(json.dumps(summary_data, indent=2, ensure_ascii=False), encoding="utf-8")

    return paths


def generate_dashboard(result: dict[str, Any], output_dir: str | Path, filename: str = "dashboard.png") -> Path:
    """Generate dashboard PNG from optimization results."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename

    df: pd.DataFrame = result["optimized_results"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    fig.suptitle("Dashboard financiero", fontsize=16, fontweight="bold")

    axes[0, 0].plot(df["t"], df["Ingresos"], label="Ingresos", color="#2E86AB")
    axes[0, 0].plot(df["t"], df["EBITDA"], label="EBITDA", color="#A23B72")
    axes[0, 0].set_title("Ingresos y EBITDA mensual")
    axes[0, 0].set_xlabel("Mes")
    axes[0, 0].set_ylabel("USD")
    axes[0, 0].legend()
    axes[0, 0].grid(alpha=0.3)

    axes[0, 1].plot(df["t"], df["Caja"], color="#F18F01")
    axes[0, 1].axhline(0, color="black", linewidth=0.8)
    axes[0, 1].set_title("Caja acumulada")
    axes[0, 1].set_xlabel("Mes")
    axes[0, 1].set_ylabel("USD")
    axes[0, 1].grid(alpha=0.3)

    axes[1, 0].bar(df["t"], df["Adq_clientes"], color="#3B7A57")
    axes[1, 0].set_title("Adquisición de clientes")
    axes[1, 0].set_xlabel("Mes")
    axes[1, 0].set_ylabel("Clientes")
    axes[1, 0].grid(axis="y", alpha=0.3)

    axes[1, 1].plot(df["t"], df["Vendedores"], label="Vendedores", color="#6A4C93")
    axes[1, 1].plot(df["t"], df["Lideres"], label="Líderes", color="#1982C4")
    axes[1, 1].set_title("Dotación comercial")
    axes[1, 1].set_xlabel("Mes")
    axes[1, 1].set_ylabel("Personas")
    axes[1, 1].legend()
    axes[1, 1].grid(alpha=0.3)

    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _markdown_table(df: pd.DataFrame) -> str:
    headers = list(df.columns)
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in df.iterrows():
        values = []
        for value in row:
            if isinstance(value, float):
                values.append(f"{value:,.2f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def generate_markdown_report(result: dict[str, Any], output_dir: str | Path, filename: str = "financial_report.md") -> Path:
    """Generate Spanish Markdown financial report."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename

    summary = result["summary"]
    dcf = result["dcf"]
    multiples = result["multiples_valuation"]
    solution = result["solution"]
    unit_economics: pd.DataFrame = result["unit_economics"]

    key_metrics = _markdown_table(unit_economics[["Unit Economic", "Valor", "Unidad"]].head(8))

    content = f"""# Reporte financiero Adventure Capital

## Resumen ejecutivo

- Estado solver: **{solution.get("status", "N/A")}**
- Adquisición total: **{_number(summary["total_acquisition"])} clientes**
- Ingresos totales: **{_money(summary["total_revenue"])}**
- EBITDA total: **{_money(summary["total_ebitda"])}**
- Caja final: **{_money(summary["final_cash"])}**
- Caja mínima: **{_money(summary["minimum_cash"])}**

## Valorización

- VAN DCF: **{_money(dcf["VAN"])}**
- VP flujos: **{_money(dcf["vp_flujos"])}**
- Valor de desecho VP: **{_money(dcf["valor_desecho_vp"])}**
- Valor por múltiplo de ingresos: **{_money(multiples["valor_por_ingresos"])}**
- Valor por múltiplo de EBITDA: **{_money(multiples["valor_por_ebitda"])}**

## Unit economics principales

{key_metrics}

## Archivos generados

- `financial_report.md`
- `dashboard.png`
- `fixed_cashflow.csv`
- `optimized_results.csv`
- `dcf_cashflow.csv`
- `dcf_annual_summary.csv`
- `multiples_valuation.csv`
- `unit_economics.csv`
"""

    path.write_text(content, encoding="utf-8")
    return path


def generate_report(result: dict[str, Any], output_dir: str | Path) -> dict[str, Path]:
    """Generate Markdown report, dashboard PNG, and core CSV outputs."""
    paths = write_core_csv_outputs(result, output_dir)
    paths["dashboard"] = generate_dashboard(result, output_dir)
    paths["financial_report"] = generate_markdown_report(result, output_dir)
    return paths

"""Business-facing report generation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
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


def _active_channels(instance: dict[str, Any]) -> list[str]:
    channels = instance.get("channels", {}) or {}
    return [name for name in ("salesforce", "advertising", "third_party") if channels.get(name, {}).get("active")]


def _stringify_tuple_map(values: dict[Any, Any]) -> dict[str, Any]:
    """Return JSON-safe keys for tuple-indexed instance parameters."""
    output: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(key, tuple):
            out_key = "|".join(str(part) for part in key)
        else:
            out_key = str(key)
        output[out_key] = value
    return output


def _unit_economics_lookup(df: pd.DataFrame) -> dict[str, float]:
    if "Unit Economic" not in df.columns or "Valor" not in df.columns:
        return {}
    return {
        str(row["Unit Economic"]): float(row["Valor"])
        for _, row in df.iterrows()
        if pd.notna(row.get("Valor"))
    }


def _build_model_instance_artifact(instance: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "H": int(instance["H"]),
        "T": list(instance["T"]),
        "T_base": list(instance["T_base"]),
        "S": int(instance["S"]),
        "services": instance["servicios"],
        "A_base": _stringify_tuple_map(instance.get("A_base", {})),
        "discount_assumptions": {
            "beta_anual": float(instance["beta_anual"]),
            "beta_mensual": float(instance["beta"]),
            "descuento": {str(k): float(v) for k, v in instance.get("descuento", {}).items()},
        },
        "channels": instance.get("channels", {}),
        "acquisition_ceiling": {
            "log_ceiling": {str(k): float(v) for k, v in instance.get("log_ceiling", {}).items()},
            "ceiling_slack": float(instance.get("ceiling_slack", 0.0)),
        },
    }


def _build_growth_plan_summary(result: dict[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    solution = result["solution"]
    return {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "solver_status": solution.get("status"),
        "objective_value": solution.get("objective"),
        "total_acquisition": float(summary["total_acquisition"]),
        "total_revenue": float(summary["total_revenue"]),
        "total_ebitda": float(summary["total_ebitda"]),
        "final_cash": float(summary["final_cash"]),
        "minimum_cash": float(summary["minimum_cash"]),
        "max_sellers": float(summary["max_sellers"]),
        "max_leaders": float(summary["max_leaders"]),
        "enabled_channels": _active_channels(result["instance"]),
    }


def _build_valuation_summary(result: dict[str, Any]) -> dict[str, Any]:
    dcf = result["dcf"]
    multiples = result["multiples_valuation"]
    unit = _unit_economics_lookup(result["unit_economics"])
    parameters = result["instance"].get("parametros", {})
    return {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "dcf",
        "vc_invested": float(result["instance"]["VC"]),
        "van": float(dcf["VAN"]),
        "vp_flujos": float(dcf.get("vp_flujos", 0.0)),
        "vr_nominal": float(dcf.get("vr_nominal", 0.0)),
        "vr_pv": float(dcf.get("vr_pv", 0.0)),
        "valor_desecho_nominal": float(dcf.get("valor_desecho_nominal", 0.0)),
        "valor_desecho_vp": float(dcf.get("valor_desecho_vp", 0.0)),
        "beta_anual": float(dcf["beta_anual"]),
        "beta_mensual": float(dcf["beta_mensual"]),
        "tax": float(dcf.get("tax", parameters.get("tax", result["instance"].get("tax", 0.0)))),
        "terminal_value_method": parameters.get("valor_residual_metodo", "none"),
        "ebitda_ultimo_mes": float(dcf["ebitda_ultimo_mes"]),
        "ebitda_anualizado": float(dcf["ebitda_anualizado"]),
        "multiples_reference": {
            "status": "implemented_reference",
            "methodological_note": "Configurable multiples; not market-calibrated comparables unless evidence is supplied.",
            "valor_por_ingresos": float(multiples.get("valor_por_ingresos", 0.0)),
            "valor_por_ebitda": float(multiples.get("valor_por_ebitda", 0.0)),
            "mult_ingresos": float(multiples.get("mult_ingresos", 0.0)),
            "mult_ebitda": float(multiples.get("mult_ebitda", 0.0)),
        },
        "unit_economics": unit,
        "formula_refs": ["DCF-001", "DCF-002", "DCF-003", "UE-001", "UE-002", "UE-003"],
    }


def _build_formula_trace() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formulas": [
            {
                "id": "DCF-001",
                "name": "Impuesto",
                "expression": "max(EBITDA * tax, 0)",
                "source_fields": ["optimized_results.EBITDA", "startup.yaml.tax"],
                "output_fields": ["dcf_cashflow.Impuesto"],
                "assumptions": ["Tax applies only when EBITDA is positive."],
                "limitations": ["No deferred tax assets are modeled."],
                "implementation_status": "implemented",
            },
            {
                "id": "DCF-002",
                "name": "FC_neto",
                "expression": "EBITDA - Impuesto",
                "source_fields": ["dcf_cashflow.EBITDA", "dcf_cashflow.Impuesto"],
                "output_fields": ["dcf_cashflow.FC_neto"],
                "assumptions": ["EBITDA is used as operating cashflow proxy."],
                "limitations": ["Working-capital timing beyond modeled cash balance is simplified."],
                "implementation_status": "implemented",
            },
            {
                "id": "DCF-003",
                "name": "VAN",
                "expression": "-VC + sum_t(FC_neto_t / (1 + beta_mensual)^t) + terminal_value_pv",
                "source_fields": ["startup.yaml.VC", "dcf_cashflow.FC_neto", "startup.yaml.beta"],
                "output_fields": ["valuation_summary.van", "summary.json.van"],
                "assumptions": ["Annual WACC is converted to monthly discount factor."],
                "limitations": ["Terminal value depends on configured method; default may be none."],
                "implementation_status": "implemented",
            },
            {
                "id": "UE-001",
                "name": "Annual LTV",
                "expression": "sum_s(ticket_s * (12 / frecuencia_s) * (1 - c_u_s / ticket_s) / churn_anual_s[0])",
                "source_fields": ["startup.yaml.servicios"],
                "output_fields": ["unit_economics.LTV"],
                "assumptions": ["Annual, service-summed; first-year churn used."],
                "limitations": ["Not cohort-specific by acquisition month."],
                "implementation_status": "implemented",
            },
            {
                "id": "UE-002",
                "name": "CAC per customer",
                "expression": "sum(total_acquisition_cost) / sum(new_customers)",
                "source_fields": ["optimized_results.total_acquisition_cost", "optimized_results.new_customers"],
                "output_fields": ["unit_economics.CAC"],
                "assumptions": ["CAC component columns reconcile to CAC alias."],
                "limitations": ["Ratio is horizon aggregate, not cohort-level CAC."],
                "implementation_status": "implemented",
            },
            {
                "id": "UE-003",
                "name": "LTV/CAC",
                "expression": "Annual LTV / cumulative CAC per user",
                "source_fields": ["unit_economics.LTV", "optimized_results.cumulative_cac_per_user"],
                "output_fields": ["unit_economics.LTV/CAC"],
                "assumptions": ["Uses cumulative CAC when available."],
                "limitations": ["High values may reflect calibration artifact and require DD interpretation."],
                "implementation_status": "implemented",
            },
            {
                "id": "MULT-001",
                "name": "Multiples reference",
                "expression": "reference_year_metric * configured_multiple",
                "source_fields": ["dcf_annual_summary", "startup.yaml.mult_ingresos", "startup.yaml.mult_ebitda"],
                "output_fields": ["multiples_valuation.Valorización"],
                "assumptions": ["Multiples are configurable references."],
                "limitations": ["Not market-calibrated comparable-company analysis unless external evidence is supplied."],
                "implementation_status": "methodological_reference",
            },
        ],
    }


def write_core_csv_outputs(result: dict[str, Any], output_dir: str | Path) -> dict[str, Path]:
    """Write core CSV/JSON outputs consumed by reports and downstream analysis."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = {
        "fixed_cashflow": out / CSV_OUTPUTS["fixed_cashflow"],
        "optimized_results": out / CSV_OUTPUTS["optimized_results"],
        "dcf_cashflow": out / CSV_OUTPUTS["dcf_cashflow"],
        "dcf_annual_summary": out / CSV_OUTPUTS["dcf_annual_summary"],
        "multiples_valuation": out / CSV_OUTPUTS["multiples_valuation"],
        "unit_economics": out / CSV_OUTPUTS["unit_economics"],
        "summary": out / "summary.json",
        "model_instance": out / "model_instance.json",
        "growth_plan_summary": out / "growth_plan_summary.json",
        "valuation_summary": out / "valuation_summary.json",
        "formula_trace": out / "formula_trace.json",
        "growth_suggestions": out / "growth_suggestions.json",
    }

    result["fixed_cashflow"].to_csv(paths["fixed_cashflow"], index=False)
    result["optimized_results"].to_csv(paths["optimized_results"], index=False)
    result["dcf"]["df_flujo_caja"].to_csv(paths["dcf_cashflow"], index=False)
    result["dcf"]["resumen_anual_dcf"].to_csv(paths["dcf_annual_summary"])
    result["multiples_valuation"]["df_multiplos"].to_csv(paths["multiples_valuation"], index=False)
    result["unit_economics"].to_csv(paths["unit_economics"], index=False)

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
    paths["summary"].write_text(json.dumps(summary_data, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["model_instance"].write_text(
        json.dumps(_build_model_instance_artifact(result["instance"]), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    paths["growth_plan_summary"].write_text(
        json.dumps(_build_growth_plan_summary(result), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    paths["valuation_summary"].write_text(
        json.dumps(_build_valuation_summary(result), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    paths["formula_trace"].write_text(
        json.dumps(_build_formula_trace(), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    # Growth commitment g-suggestions (ADR 0014, plan §3): always computed and
    # reported — regardless of whether growth_commitment is enabled — since
    # this is a calibration aid, never an auto-selected default. Uses the
    # instance's own parametros (raw config), not the built instance dict.
    from adventure_capital.instance import compute_growth_suggestions

    raw_config = result["instance"].get("parametros", {})
    try:
        suggestions = compute_growth_suggestions(raw_config)
    except Exception:
        suggestions = {"schema_version": "1.0", "error": "could not compute growth suggestions"}
    paths["growth_suggestions"].write_text(
        json.dumps(suggestions, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

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

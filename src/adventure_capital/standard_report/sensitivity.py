"""Derived report artifacts for Phase 5B."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _unit_value(unit_df: pd.DataFrame, name: str, default: float | None = None) -> float | None:
    if "Unit Economic" not in unit_df.columns or "Valor" not in unit_df.columns:
        return default
    rows = unit_df[unit_df["Unit Economic"] == name]
    if rows.empty:
        return default
    value = rows.iloc[0]["Valor"]
    return None if pd.isna(value) else float(value)


def _base_wacc(document: dict[str, Any]) -> float:
    dcf = document.get("dcf", {})
    beta_capm = float(dcf.get("beta_capm", 1.0))
    rf = float(dcf.get("Rf_us", dcf.get("Rf_local", 0.0)))
    rm = float(dcf.get("Rm", 0.0))
    country_risk = float(dcf.get("country_risk", 0.0))
    risk_penalty = float(dcf.get("castigo_riesgo", 0.0))
    return rf + beta_capm * (rm - rf) + country_risk + risk_penalty


def _monthly_rate(annual_rate: float) -> float:
    return (1 + annual_rate) ** (1 / 12) - 1


def calculate_wacc_multiple_sensitivity(output_dir: str | Path, document: dict[str, Any]) -> pd.DataFrame:
    """Calculate WACC x EBITDA multiple sensitivity without re-optimizing."""
    out = Path(output_dir)
    cashflow = pd.read_csv(out / "dcf_cashflow.csv")
    unit = pd.read_csv(out / "unit_economics.csv")
    sensitivity = document.get("sensitivity", {})

    if sensitivity.get("method", "calculation") != "calculation":
        raise ValueError("Only sensitivity.method=calculation is implemented.")

    base_wacc = _base_wacc(document)
    wacc_values = [max(base_wacc + float(delta), 0.0001) for delta in sensitivity.get("wacc_range", [0])]
    multiples = [float(value) for value in sensitivity.get("ebitda_multiple_range", [1.0])]

    ltv_cac = _unit_value(unit, "LTV/CAC")
    if sensitivity.get("include_ltv_cac_reference", False) and ltv_cac is not None and ltv_cac > 0:
        multiples = sorted(set([*multiples, round(ltv_cac, 4)]))

    fc_neto = cashflow["FC_neto"].astype(float)
    periods = cashflow["t"].astype(int)
    last_ebitda = float(cashflow["EBITDA"].iloc[-1])
    rows: list[dict[str, float | str]] = []

    for wacc in wacc_values:
        monthly = _monthly_rate(wacc)
        pv_flows = float((fc_neto / ((1 + monthly) ** periods)).sum())
        for multiple in multiples:
            terminal = max(last_ebitda * 12 * multiple, 0.0)
            terminal_pv = float(terminal / ((1 + monthly) ** int(periods.iloc[-1])))
            rows.append(
                {
                    "method": "calculation",
                    "wacc": wacc,
                    "ebitda_multiple": multiple,
                    "pv_cashflows": pv_flows,
                    "terminal_value_pv": terminal_pv,
                    "enterprise_value": pv_flows + terminal_pv,
                    "is_ltv_cac_reference": bool(ltv_cac is not None and abs(multiple - ltv_cac) < 1e-4),
                }
            )
    return pd.DataFrame(rows)


def calculate_variable_sensitivity(output_dir: str | Path, document: dict[str, Any]) -> pd.DataFrame:
    """Calculate MVP operational sensitivity from existing outputs."""
    out = Path(output_dir)
    optimized = pd.read_csv(out / "optimized_results.csv")
    unit = pd.read_csv(out / "unit_economics.csv")
    baseline_ebitda = float(optimized["EBITDA"].sum())
    baseline_revenue = float(optimized["Ingresos"].sum())
    baseline_cac = float(optimized["CAC"].sum())
    baseline_cost = float(optimized["Costo_operacional"].sum())
    ltv_cac = _unit_value(unit, "LTV/CAC", 0.0)

    scenarios = [
        ("Ingresos +10%", baseline_ebitda + baseline_revenue * 0.10),
        ("Ingresos -10%", baseline_ebitda - baseline_revenue * 0.10),
        ("CAC +10%", baseline_ebitda - baseline_cac * 0.10),
        ("CAC -10%", baseline_ebitda + baseline_cac * 0.10),
        ("Costo operacional +10%", baseline_ebitda - baseline_cost * 0.10),
        ("Costo operacional -10%", baseline_ebitda + baseline_cost * 0.10),
    ]
    if ltv_cac is not None:
        scenarios.append(("Referencia LTV/CAC", float(ltv_cac)))

    rows = []
    for name, value in scenarios:
        rows.append(
            {
                "method": document.get("sensitivity", {}).get("method", "calculation"),
                "variable": name,
                "baseline_ebitda": baseline_ebitda,
                "result_value": float(value),
                "effect_pct": ((float(value) - baseline_ebitda) / abs(baseline_ebitda)) if baseline_ebitda else np.nan,
            }
        )
    return pd.DataFrame(rows)


def calculate_breakeven_variables(output_dir: str | Path, document: dict[str, Any]) -> pd.DataFrame:
    """Estimate variable values needed for total EBITDA = 0 from existing outputs."""
    out = Path(output_dir)
    optimized = pd.read_csv(out / "optimized_results.csv")
    revenue = float(optimized["Ingresos"].sum())
    ebitda = float(optimized["EBITDA"].sum())
    cac = float(optimized["CAC"].sum())
    op_cost = float(optimized["Costo_operacional"].sum())

    def ratio_needed(base: float, delta_sign: float) -> float | None:
        if base == 0:
            return None
        return 1 + ((-ebitda) / (delta_sign * base))

    rows = [
        {"method": "calculation", "variable": "Ingresos", "current_value": revenue, "breakeven_value": revenue * ratio_needed(revenue, 1) if ratio_needed(revenue, 1) is not None else None},
        {"method": "calculation", "variable": "CAC", "current_value": cac, "breakeven_value": cac * ratio_needed(cac, -1) if ratio_needed(cac, -1) is not None else None},
        {"method": "calculation", "variable": "Costo operacional", "current_value": op_cost, "breakeven_value": op_cost * ratio_needed(op_cost, -1) if ratio_needed(op_cost, -1) is not None else None},
    ]
    for row in rows:
        current = row["current_value"]
        breakeven = row["breakeven_value"]
        row["variation_pct"] = ((breakeven - current) / abs(current)) if current and breakeven is not None else None
    return pd.DataFrame(rows)


def build_mapvalue(output_dir: str | Path, document: dict[str, Any]) -> dict[str, Any]:
    """Build MapValue 4-layer snapshot."""
    out = Path(output_dir)
    optimized = pd.read_csv(out / "optimized_results.csv")
    unit = pd.read_csv(out / "unit_economics.csv")
    annual = pd.read_csv(out / "dcf_annual_summary.csv")

    return {
        "schema_version": "1.0",
        "layers": {
            "input_variables": {
                "company": document.get("empresa", {}).get("nombre"),
                "sensitivity_method": document.get("sensitivity", {}).get("method", "calculation"),
                "investment_total": document.get("inversion", {}).get("total"),
            },
            "operating_flows": {
                "total_acquisition": float(optimized["Adq_clientes"].sum()),
                "total_services_sold": float(optimized["Servicios_totales"].sum()),
                "active_clients_final": float(optimized["Clientes_activos"].iloc[-1]),
            },
            "financial_results": {
                "total_revenue": float(optimized["Ingresos"].sum()),
                "total_ebitda": float(optimized["EBITDA"].sum()),
                "final_cash": float(optimized["Caja"].iloc[-1]),
                "last_year_ebitda": float(annual["EBITDA"].iloc[-1]) if "EBITDA" in annual else None,
            },
            "valuation": {
                "ltv_cac": _unit_value(unit, "LTV/CAC"),
                "cac": _unit_value(unit, "CAC"),
                "ltv": _unit_value(unit, "LTV"),
            },
        },
    }


def write_derived_artifacts(output_dir: str | Path, document: dict[str, Any]) -> dict[str, Path]:
    """Write Phase 5B derived artifacts."""
    out = Path(output_dir)
    wacc = calculate_wacc_multiple_sensitivity(out, document)
    variables = calculate_variable_sensitivity(out, document)
    breakeven = calculate_breakeven_variables(out, document)
    mapvalue = build_mapvalue(out, document)

    paths = {
        "sensitivity_wacc_multiple": out / "sensitivity_wacc_multiple.csv",
        "sensitivity_variables": out / "sensitivity_variables.csv",
        "breakeven_variables": out / "breakeven_variables.csv",
        "mapvalue": out / "mapvalue.json",
    }
    wacc.to_csv(paths["sensitivity_wacc_multiple"], index=False)
    variables.to_csv(paths["sensitivity_variables"], index=False)
    breakeven.to_csv(paths["breakeven_variables"], index=False)
    paths["mapvalue"].write_text(json.dumps(mapvalue, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return paths

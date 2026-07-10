"""
Módulo de auditoría de consistencia matemática entre artefactos del pipeline.
Todas las identidades deben cerrar dentro de TOLERANCE_PCT = 0.005 (0.5%).
"""
import json
import pathlib
import pandas as pd
import yaml

TOLERANCE_PCT = 0.005


def check_consistency(output_dir: str | pathlib.Path, instance_path: str | pathlib.Path) -> dict:
    """
    Ejecuta 5 checks de identidad matemática sobre los outputs del pipeline.
    Retorna dict con resultados y escribe consistency_report.json en output_dir.

    Args:
        output_dir: directorio con artifacts del pipeline (optimized_results.csv, etc.)
        instance_path: ruta al documento YAML del reporte o de la instancia

    Returns:
        {
          "all_passed": bool,
          "checks": [{"name": str, "passed": bool, "lhs": float, "rhs": float, "diff_pct": float}]
        }
    """
    output_dir = pathlib.Path(output_dir)
    results = []

    # --- Cargar datos ---
    monthly = pd.read_csv(output_dir / "optimized_results.csv")
    annual  = pd.read_csv(output_dir / "dcf_annual_summary.csv")
    ue      = pd.read_csv(output_dir / "unit_economics.csv")

    try:
        params = yaml.safe_load(pathlib.Path(instance_path).read_text(encoding="utf-8")) or {}
    except Exception:
        params = {}

    # ---------------------------------------------------------------
    # CHECK 1: revenue_monthly_eq_annual
    # Identidad: Σ(revenue mensual) == Σ(revenue anual)
    # Fuente matemática: agregación temporal es consistente
    # ---------------------------------------------------------------
    lhs = float(monthly["Ingresos"].sum())
    rhs = float(annual["Ingresos"].sum())
    results.append(_make_check("revenue_monthly_eq_annual", lhs, rhs))

    # ---------------------------------------------------------------
    # CHECK 2: revenue_decomposition_by_service
    # Identidad: revenue_total == Σ(revenue por servicio)
    # ---------------------------------------------------------------
    service_cols = [c for c in monthly.columns if c.startswith("I_")]
    if service_cols:
        lhs = float(monthly["Ingresos"].sum())
        rhs = float(monthly[service_cols].sum().sum())
        results.append(_make_check("revenue_decomposition_by_service", lhs, rhs))
    else:
        results.append(_make_check_skipped("revenue_decomposition_by_service",
                                           "No se encontraron columnas I_<servicio>"))

    # ---------------------------------------------------------------
    # CHECK 3: ebitda_definition
    # Identidad: EBITDA == Ingresos - Costo_op - CAC - G_adm - RRHH
    # ---------------------------------------------------------------
    required_cols = ["Ingresos", "Costo_operacional", "CAC", "G_adm", "RRHH", "EBITDA"]
    if all(c in monthly.columns for c in required_cols):
        lhs = float(monthly["EBITDA"].sum())
        rhs = float((monthly["Ingresos"] - monthly["Costo_operacional"] - monthly["CAC"]
                     - monthly["G_adm"] - monthly["RRHH"]).sum())
        results.append(_make_check("ebitda_definition", lhs, rhs))
    else:
        missing = [c for c in required_cols if c not in monthly.columns]
        results.append(_make_check_skipped("ebitda_definition",
                                           f"Columnas faltantes: {missing}"))

    # ---------------------------------------------------------------
    # CHECK 4: cash_accumulation
    # Caja final = VC_invertido + Σ(EBITDA)
    # ---------------------------------------------------------------
    vc_invested = _get_vc_invested(params, output_dir)
    lhs = float(monthly["Caja"].iloc[-1])
    rhs = vc_invested + float(monthly["EBITDA"].sum())
    result = _make_check("cash_accumulation", lhs, rhs)
    result["note"] = "Caja final comparada con VC + suma de EBITDA"
    results.append(result)

    # ---------------------------------------------------------------
    # CHECK 5: gp_consistency_ue_vs_pnl
    # GP de Unit Economics (margen bruto operacional) == Margen bruto P&L
    # ---------------------------------------------------------------
    gp_rows = ue[ue["Unit Economic"] == "Gross Profit (GP)"]
    if not gp_rows.empty:
        gp_ue = float(gp_rows.iloc[0]["Valor"])
        # Margen bruto desde P&L
        margen_pnl = 1 - float(monthly["Costo_operacional"].sum()) / float(monthly["Ingresos"].sum()) if monthly["Ingresos"].sum() > 0 else 0.0
        result = _make_check("gp_consistency_ue_vs_pnl", gp_ue, margen_pnl)
        result["note"] = "Consistencia entre GP unit economics y margen bruto P&L"
        results.append(result)
    else:
        results.append(_make_check_skipped("gp_consistency_ue_vs_pnl",
                                           "Métrica 'Gross Profit (GP)' no disponible en unit economics"))

    # --- Compilar resultado ---
    all_passed = all(r["passed"] for r in results if not r.get("skipped", False))
    report = {"all_passed": all_passed, "tolerance_pct": TOLERANCE_PCT, "checks": results}

    out_path = output_dir / "consistency_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return report


# ---------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------

def _make_check(name: str, lhs: float, rhs: float) -> dict:
    diff_pct = abs(lhs - rhs) / max(abs(rhs), 1e-9)
    return {
        "name": name,
        "passed": diff_pct <= TOLERANCE_PCT,
        "lhs": round(float(lhs), 2),
        "rhs": round(float(rhs), 2),
        "diff_pct": round(diff_pct * 100, 4),
        "skipped": False
    }

def _make_check_skipped(name: str, reason: str) -> dict:
    return {"name": name, "passed": True, "skipped": True, "reason": reason}

def _get_vc_invested(params: dict, output_dir: pathlib.Path) -> float:
    """Lee VC invertido desde el YAML o desde artifacts del pipeline."""
    if params.get("inversion", {}).get("total"):
        return float(params["inversion"]["total"])
    # Fallback: buscar en el config del modelo
    summary_path = output_dir / "config.yaml"
    if summary_path.exists():
        try:
            summary = yaml.safe_load(summary_path.read_text(encoding="utf-8")) or {}
            if "VC" in summary:
                return float(summary["VC"])
        except Exception:
            pass
    # Fallback 2: check base YAML or summary
    summary_json_path = output_dir / "summary.json"
    if summary_json_path.exists():
        try:
            summary = json.loads(summary_json_path.read_text(encoding="utf-8"))
            return float(summary.get("vc_invested", 100000.0))
        except Exception:
            pass
    return 100000.0

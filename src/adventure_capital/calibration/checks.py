"""Calibration checks C01–C12 for the Adventure Capital model.

Each ``run_*`` function returns a ``CheckResult``. The orchestrator in
``report.py`` aggregates them and emits a verdict.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from adventure_capital.standard_report.validation import validate_report_inputs


@dataclass
class CheckResult:
    id: str
    name: str
    severity: str  # "error" | "warning" | "info"
    passed: bool
    value: dict[str, Any] = field(default_factory=dict)
    threshold: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    skipped: bool = False
    formula: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity,
            "passed": self.passed,
            "skipped": self.skipped,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "formula": self.formula,
        }


def _skipped(check_id: str, name: str, severity: str, reason: str) -> CheckResult:
    return CheckResult(
        id=check_id, name=name, severity=severity, passed=True, skipped=True,
        message=f"Cheque deshabilitado: {reason}",
    )


def _read_optimized(output_dir: Path) -> pd.DataFrame | None:
    path = output_dir / "optimized_results.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


# C01 --------------------------------------------------------------

def check_solver_status(config: dict[str, Any], status: str | None) -> CheckResult:
    accepted = list(config.get("accepted_statuses", ["Optimal"]))
    actual = status or "Unknown"
    passed = actual in accepted
    return CheckResult(
        id="C01", name="solver_status",
        severity=config.get("severity", "error"),
        passed=passed,
        value={"status": actual},
        threshold={"accepted_statuses": accepted},
        message=(
            f"Solver retornó estado **{actual}**."
            if passed
            else f"Solver retornó **{actual}** (esperado: {', '.join(accepted)}). La optimización no convergió."
        ),
        formula="solution.status ∈ accepted_statuses",
    )


# C02 --------------------------------------------------------------

def check_seller_capacity(config: dict[str, Any], optimized: pd.DataFrame, instance: dict[str, Any]) -> CheckResult:
    meta = float(instance.get("meta", 0.0))
    start_month = int(config.get("start_month", 13))
    saturation_slack = float(config.get("saturation_slack", 0.5))
    max_pct = float(config.get("max_pct_saturated", 0.70))
    severity = config.get("severity", "warning")

    horizon = optimized[optimized["t"] >= start_month]
    if horizon.empty or meta <= 0:
        return CheckResult(
            id="C02", name="seller_capacity_saturation", severity=severity,
            passed=True, skipped=True, message="No hay datos optimizados suficientes.",
        )
    capacity = meta * horizon["Vendedores"].astype(float)
    slack = capacity - horizon["Adq_clientes"].astype(float)
    saturated_mask = slack < saturation_slack
    pct_saturated = float(saturated_mask.mean())
    passed = pct_saturated <= max_pct
    return CheckResult(
        id="C02", name="seller_capacity_saturation", severity=severity,
        passed=passed,
        value={
            "pct_saturado": pct_saturated,
            "meses_saturados": int(saturated_mask.sum()),
            "meses_evaluados": int(len(horizon)),
            "slack_promedio": float(slack.mean()),
            "meta": meta,
            "vendedores_max": float(horizon["Vendedores"].max()),
            "vendedores_min": float(horizon["Vendedores"].min()),
        },
        threshold={"max_pct_saturated": max_pct, "saturation_slack": saturation_slack},
        message=(
            f"Capacidad comercial saturada {pct_saturated:.0%} de los meses optimizados "
            f"({int(saturated_mask.sum())}/{len(horizon)}). El modelo no representa un plan de aceleración."
            if not passed
            else f"Capacidad saturada {pct_saturated:.0%} — dentro del umbral {max_pct:.0%}."
        ),
        formula="slack[t] = meta × Vendedores[t] − Adq_clientes[t]",
    )


# C03 --------------------------------------------------------------

def check_sellers_no_growth(config: dict[str, Any], optimized: pd.DataFrame, instance: dict[str, Any]) -> CheckResult:
    meta = float(instance.get("meta", 0.0))
    start_month = int(config.get("start_month", 13))
    saturation_slack = float(config.get("saturation_slack", 0.5))
    min_saturation_pct = float(config.get("min_saturation_pct", 0.50))
    severity = config.get("severity", "warning")

    horizon = optimized[optimized["t"] >= start_month]
    if horizon.empty or meta <= 0:
        return CheckResult(
            id="C03", name="sellers_no_growth_with_saturation", severity=severity,
            passed=True, skipped=True, message="No hay datos optimizados suficientes.",
        )
    capacity = meta * horizon["Vendedores"].astype(float)
    slack = capacity - horizon["Adq_clientes"].astype(float)
    saturated_pct = float((slack < saturation_slack).mean())
    sellers_max = float(horizon["Vendedores"].max())
    sellers_min = float(horizon["Vendedores"].min())
    sellers_flat = abs(sellers_max - sellers_min) < 1e-3
    passed = not (sellers_flat and saturated_pct >= min_saturation_pct)

    return CheckResult(
        id="C03", name="sellers_no_growth_with_saturation", severity=severity,
        passed=passed,
        value={
            "vendedores_min": sellers_min,
            "vendedores_max": sellers_max,
            "sellers_flat": sellers_flat,
            "saturated_pct": saturated_pct,
        },
        threshold={"min_saturation_pct": min_saturation_pct, "saturation_slack": saturation_slack},
        message=(
            f"Vendedores fijos en {sellers_max:.1f} con {saturated_pct:.0%} de meses saturados. "
            "El optimizador prefiere no contratar — revisar costos vs ticket marginal."
            if not passed
            else "Vendedores muestran variación o no hay saturación crítica."
        ),
        formula="max(Vendedores) == min(Vendedores) AND saturated_pct ≥ threshold",
    )


# C04 --------------------------------------------------------------

def check_cash_floor(
    config: dict[str, Any], optimized: pd.DataFrame, instance: dict[str, Any] | None = None
) -> CheckResult:
    severity = config.get("severity", "error")
    minimum_cash = float(config.get("minimum_cash", 0.0))
    # Working-capital floor (Phase 4) supersedes the hard-zero default: cash may fall to -VC.
    # ``instance`` may be the generated instance (with "parametros") or the raw config.
    if instance is not None:
        params = instance.get("parametros", instance)
        working_capital = params.get("working_capital", {})
        if working_capital.get("enabled", False):
            minimum_cash = -float(params.get("VC", instance.get("VC", 0.0)))
    min_cash = float(optimized["Caja"].min())
    passed = min_cash >= minimum_cash
    return CheckResult(
        id="C04", name="cash_floor", severity=severity, passed=passed,
        value={"min_cash": min_cash, "min_month": int(optimized.loc[optimized["Caja"].idxmin(), "t"])},
        threshold={"minimum_cash": minimum_cash},
        message=(
            f"Caja mínima USD {min_cash:,.0f} cae bajo el piso USD {minimum_cash:,.0f}. "
            "El plan requiere financiamiento intermedio."
            if not passed
            else f"Caja mínima USD {min_cash:,.0f} ≥ piso configurado."
        ),
        formula="min(Caja[t]) ≥ minimum_cash",
    )


# C05 --------------------------------------------------------------

def check_total_ebitda(config: dict[str, Any], optimized: pd.DataFrame) -> CheckResult:
    severity = config.get("severity", "error")
    minimum_total = float(config.get("minimum_total", 0.0))
    total = float(optimized["EBITDA"].sum())
    passed = total >= minimum_total
    return CheckResult(
        id="C05", name="total_ebitda", severity=severity, passed=passed,
        value={"total_ebitda": total},
        threshold={"minimum_total": minimum_total},
        message=(
            f"EBITDA total USD {total:,.0f} bajo umbral USD {minimum_total:,.0f}. "
            "El plan no genera utilidad operacional acumulada."
            if not passed
            else f"EBITDA total USD {total:,.0f} ≥ umbral."
        ),
        formula="Σ EBITDA[t] ≥ minimum_total",
    )


# C06 --------------------------------------------------------------

def check_npv(config: dict[str, Any], output_dir: Path) -> CheckResult:
    severity = config.get("severity", "error")
    minimum_npv = float(config.get("minimum_npv", 0.0))
    annual_path = output_dir / "dcf_annual_summary.csv"
    cashflow_path = output_dir / "dcf_cashflow.csv"
    if not cashflow_path.exists() and not annual_path.exists():
        return CheckResult(
            id="C06", name="npv", severity=severity,
            passed=False, skipped=True,
            message="No se encontró archivo DCF para evaluar VAN.",
        )
    npv = float("nan")
    if cashflow_path.exists():
        df = pd.read_csv(cashflow_path)
        if "FC_desc" in df.columns:
            npv = float(df["FC_desc"].sum())
    if math.isnan(npv) and annual_path.exists():
        df = pd.read_csv(annual_path)
        if "FC_desc" in df.columns:
            npv = float(df["FC_desc"].sum())
    if math.isnan(npv):
        return CheckResult(
            id="C06", name="npv", severity=severity, passed=False, skipped=True,
            message="No se pudo calcular VAN (columna FC_desc ausente).",
        )
    passed = npv >= minimum_npv
    return CheckResult(
        id="C06", name="npv", severity=severity, passed=passed,
        value={"npv": npv},
        threshold={"minimum_npv": minimum_npv},
        message=(
            f"VAN USD {npv:,.0f} es negativo o bajo umbral. La valorización DCF no soporta el plan."
            if not passed
            else f"VAN USD {npv:,.0f} ≥ umbral."
        ),
        formula="Σ FC_desc[t] ≥ minimum_npv",
    )


# C07 --------------------------------------------------------------

def check_gross_margin(config: dict[str, Any], optimized: pd.DataFrame) -> CheckResult:
    severity = config.get("severity", "warning")
    min_gp = float(config.get("min_gp", 0.30))
    max_gp = float(config.get("max_gp", 0.92))
    revenue = float(optimized["Ingresos"].sum())
    cost = float(optimized["Costo_operacional"].sum())
    gp = 1 - cost / revenue if revenue > 0 else float("nan")
    passed = (not math.isnan(gp)) and (min_gp <= gp <= max_gp)
    message = (
        f"Gross profit {gp:.1%} fuera de banda [{min_gp:.0%}, {max_gp:.0%}]. "
        + ("`c_u`/`c_min` subestimados o costos no modelados." if gp > max_gp else "margen muy bajo para perfil VC.")
    ) if not passed else f"Gross profit {gp:.1%} dentro de banda."
    return CheckResult(
        id="C07", name="gross_margin", severity=severity, passed=passed,
        value={"gross_profit": gp, "revenue": revenue, "cost": cost},
        threshold={"min_gp": min_gp, "max_gp": max_gp},
        message=message,
        formula="gp = 1 − Σ Costo_operacional / Σ Ingresos",
    )


# C08 --------------------------------------------------------------

def check_ltv_cac(config: dict[str, Any], output_dir: Path) -> CheckResult:
    severity = config.get("severity", "warning")
    min_ratio = float(config.get("min_ratio", 1.0))
    max_ratio = float(config.get("max_ratio", 20.0))
    unit_path = output_dir / "unit_economics.csv"
    if not unit_path.exists():
        return CheckResult(
            id="C08", name="ltv_cac", severity=severity,
            passed=False, skipped=True,
            message="No se encontró unit_economics.csv.",
        )
    unit = pd.read_csv(unit_path)
    rows = unit[unit["Unit Economic"] == "LTV/CAC"]
    if rows.empty:
        return CheckResult(
            id="C08", name="ltv_cac", severity=severity,
            passed=False, skipped=True,
            message="Falta métrica LTV/CAC en unit_economics.csv.",
        )
    ratio = float(rows.iloc[0]["Valor"])
    passed = min_ratio <= ratio <= max_ratio
    return CheckResult(
        id="C08", name="ltv_cac", severity=severity, passed=passed,
        value={"ltv_cac": ratio},
        threshold={"min_ratio": min_ratio, "max_ratio": max_ratio},
        message=(
            f"LTV/CAC {ratio:.1f}× fuera de banda [{min_ratio}, {max_ratio}]. "
            + ("Artefacto de fórmula — usar ARPU ponderado y margen por servicio." if ratio > max_ratio else "Adquisición no rentable.")
            if not passed
            else f"LTV/CAC {ratio:.1f}× dentro de banda."
        ),
        formula="unit_economics['LTV/CAC']",
    )


# C09 --------------------------------------------------------------

def check_mix_concentration(config: dict[str, Any], optimized: pd.DataFrame) -> CheckResult:
    severity = config.get("severity", "warning")
    max_concentration = float(config.get("max_concentration", 0.85))
    a_cols = [c for c in optimized.columns if c.startswith("A_") and c != "A_base"]
    if not a_cols:
        return CheckResult(
            id="C09", name="mix_concentration", severity=severity,
            passed=False, skipped=True,
            message="No se encontraron columnas A_*.",
        )
    totals = {c: float(optimized[c].sum()) for c in a_cols}
    grand = sum(totals.values())
    if grand <= 0:
        return CheckResult(
            id="C09", name="mix_concentration", severity=severity,
            passed=False, skipped=True,
            message="Adquisición total nula.",
        )
    top_service, top_value = max(totals.items(), key=lambda kv: kv[1])
    pct = top_value / grand
    passed = pct <= max_concentration
    return CheckResult(
        id="C09", name="mix_concentration", severity=severity, passed=passed,
        value={"top_service": top_service.replace("A_", ""), "top_pct": pct, "totals": totals},
        threshold={"max_concentration": max_concentration},
        message=(
            f"{pct:.0%} de la adquisición se concentra en '{top_service.replace('A_', '')}'. "
            "Considerar simplificar el mix."
            if not passed
            else f"Concentración máxima {pct:.0%} dentro del umbral."
        ),
        formula="max_s(Σ A[s]) / Σ A",
    )


# C10 --------------------------------------------------------------

def check_retention(config: dict[str, Any], optimized: pd.DataFrame) -> CheckResult:
    severity = config.get("severity", "warning")
    min_ratio = float(config.get("min_retention_ratio", 0.20))
    total_acq = float(optimized["Adq_clientes"].sum())
    final_stock = float(optimized["Clientes_activos"].iloc[-1])
    if total_acq <= 0:
        return CheckResult(
            id="C10", name="retention", severity=severity,
            passed=False, skipped=True,
            message="Adquisición total nula.",
        )
    ratio = final_stock / total_acq
    passed = ratio >= min_ratio
    return CheckResult(
        id="C10", name="retention", severity=severity, passed=passed,
        value={"final_stock": final_stock, "total_acquisition": total_acq, "ratio": ratio},
        threshold={"min_retention_ratio": min_ratio},
        message=(
            f"Stock final {final_stock:.0f} sobre {total_acq:.0f} adquiridos = "
            f"{ratio:.0%}. Churn demasiado alto para la frecuencia configurada."
            if not passed
            else f"Retención agregada {ratio:.0%} ≥ umbral."
        ),
        formula="Clientes_activos[H] / Σ Adq_clientes",
    )


# C11 --------------------------------------------------------------

def check_document_completeness(
    config: dict[str, Any], output_dir: Path, document_path: str | Path, schema_path: str | Path
) -> CheckResult:
    severity = config.get("severity", "error")
    try:
        validation = validate_report_inputs(output_dir, document_path, schema_path)
    except Exception as exc:  # malformed YAML, missing schema, etc.
        return CheckResult(
            id="C11", name="document_completeness", severity=severity, passed=False,
            value={"error": str(exc)},
            message=f"No se pudo validar el documento: {exc}",
            formula="validate_report_inputs(...)",
        )
    passed = validation.valid
    return CheckResult(
        id="C11", name="document_completeness", severity=severity, passed=passed,
        value={
            "missing_document_fields": validation.missing_document_fields,
            "missing_core_artifacts": validation.missing_core_artifacts,
        },
        threshold={},
        message=(
            "Documento y artifacts completos."
            if passed
            else (
                "Documento o artifacts incompletos. "
                f"Faltan campos: {', '.join(validation.missing_document_fields) or '—'}. "
                f"Faltan archivos: {', '.join(validation.missing_core_artifacts) or '—'}."
            )
        ),
        formula="schema-driven required fields + core artifact presence",
    )


# Orchestration helper ---------------------------------------------

def collect_checks(
    output_dir: Path,
    instance: dict[str, Any],
    document_path: str | Path,
    schema_path: str | Path,
    thresholds: dict[str, Any],
    solver_status: str | None,
) -> list[CheckResult]:
    """Run all enabled checks and return their results."""
    optimized = _read_optimized(output_dir)
    if optimized is None:
        return [
            CheckResult(
                id="C00", name="missing_optimized_results", severity="error",
                passed=False, message="optimized_results.csv no encontrado. Correr el pipeline primero.",
            )
        ]
    results: list[CheckResult] = []
    registry: list[tuple[str, callable]] = [
        ("C01_solver_status", lambda c: check_solver_status(c, solver_status)),
        ("C02_seller_capacity", lambda c: check_seller_capacity(c, optimized, instance)),
        ("C03_sellers_no_growth", lambda c: check_sellers_no_growth(c, optimized, instance)),
        ("C04_cash_floor", lambda c: check_cash_floor(c, optimized, instance)),
        ("C05_total_ebitda", lambda c: check_total_ebitda(c, optimized)),
        ("C06_npv", lambda c: check_npv(c, output_dir)),
        ("C07_gross_margin", lambda c: check_gross_margin(c, optimized)),
        ("C08_ltv_cac", lambda c: check_ltv_cac(c, output_dir)),
        ("C09_mix_concentration", lambda c: check_mix_concentration(c, optimized)),
        ("C10_retention", lambda c: check_retention(c, optimized)),
        (
            "C11_document_completeness",
            lambda c: check_document_completeness(c, output_dir, document_path, schema_path),
        ),
    ]
    for key, runner in registry:
        cfg = thresholds.get(key, {}) or {}
        if cfg.get("enabled", True) is False:
            results.append(_skipped(key.split("_")[0], key, cfg.get("severity", "info"), "disabled"))
            continue
        try:
            results.append(runner(cfg))
        except Exception as exc:  # defensive — never let a bug break the gate
            results.append(
                CheckResult(
                    id=key.split("_")[0], name=key, severity="error",
                    passed=False, message=f"Excepción durante la evaluación: {exc}",
                )
            )
    return results

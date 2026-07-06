"""Due Diligence rule registry.

Due Diligence is an iterative assess -> recommend -> rerun workflow, not a hard
gate. DD owns new logic only: pre-rules over the raw instance, startup-eligibility
and synthesis rules over deterministic outputs, and a liquidity diagnostic.
Post-model financial checks (NPV, LTV/CAC, margin, cash floor, EBITDA, retention,
solver status) are consumed from ``calibration`` via :func:`map_calibration_findings`,
not reimplemented.

Severity classes, worst-first:
    structural -> rejected_for_stochastic       (instance cannot be modeled)
    major      -> requires_major_adjustment     (not yet venture-scale eligible)
    minor      -> requires_minor_adjustment      (fixable business/liquidity risk)
    warning    -> passed_with_warnings
    ok         -> (no effect)

Only ``structural`` blocks the stochastic valuation. Liquidity issues (negative
cash, funding gap, runway) are diagnostic and never structural.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from adventure_capital.config import validate_config

STRUCTURAL = "structural"
MAJOR = "major"
MINOR = "minor"
WARNING = "warning"
OK = "ok"

DEFAULT_THRESHOLDS: dict[str, float] = {
    "churn_warn": 0.6,
    "churn_major": 0.95,           # extreme churn -> not scalable (major)
    "breakeven_warn_month": 24,
    "runway_minor": 6,             # cash negative on/before this month -> minor
    "gap_warn": 0.5,               # working-capital trough as fraction of VC -> warning
    "gap_minor": 5.0,              # working-capital trough as multiple of VC -> minor
    "ebitda_regime_year": 3,       # annual EBITDA must be positive by this year
    "revenue_growth_min_multiple": 1.5,  # final-year revenue / first-year revenue
    "exit_roi_min": 3.0,           # exit value / minimum post-money (VC 3x rule)
}


@dataclass
class Finding:
    """One Due Diligence rule outcome."""

    id: str
    name: str
    severity_class: str  # STRUCTURAL | MAJOR | MINOR | WARNING | OK
    passed: bool
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    source: str = "due_diligence"  # "due_diligence" | "calibration"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "severity_class": self.severity_class,
            "passed": self.passed,
            "message": self.message,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "source": self.source,
        }


def _ok(rule_id: str, name: str, message: str) -> Finding:
    return Finding(id=rule_id, name=name, severity_class=OK, passed=True, message=message)


# ----- Pre-rules (raw instance, structural) -------------------------------


def _rule_instance_valid(config: dict[str, Any]) -> Finding:
    try:
        validate_config(config)
    except Exception as exc:
        return Finding(
            id="DD01", name="instance_valid", severity_class=STRUCTURAL, passed=False,
            message=f"Instancia inválida o incompleta: {exc}",
            evidence={"error": str(exc)},
            recommendation="Completar/corregir los inputs esenciales del config antes de modelar.",
        )
    return _ok("DD01", "instance_valid", "Config válido y completo.")


def _rule_unit_margin_positive(config: dict[str, Any]) -> Finding:
    offenders = [
        s.get("nombre", str(i))
        for i, s in enumerate(config.get("servicios", []))
        if float(s.get("ticket", 0.0)) <= float(s.get("c_u", 0.0))
    ]
    if offenders:
        return Finding(
            id="DD02", name="unit_margin_positive", severity_class=STRUCTURAL, passed=False,
            message=f"Servicios con ticket <= costo unitario (economía unitaria no computable): {', '.join(offenders)}.",
            evidence={"servicios": offenders},
            recommendation="Subir `ticket` o bajar `c_u` para que el margen unitario sea positivo.",
        )
    return _ok("DD02", "unit_margin_positive", "Todos los servicios tienen margen unitario positivo.")


def _rule_financing_present(config: dict[str, Any]) -> Finding:
    vc = float(config.get("VC", 0.0))
    if vc <= 0:
        # Operating-company exemption: an already-operating company can enter
        # with VC = 0 (working capital covered by its own margin). Declared
        # explicitly in the instance YAML — never inferred.
        if bool(config.get("operating_company", False)):
            return Finding(
                id="DD03", name="financing_present", severity_class=WARNING, passed=False,
                message="`VC` = 0 con `operating_company: true` — empresa operando sin ticket "
                        "inicial; el plan debe autofinanciarse (piso de caja 0).",
                evidence={"VC": vc, "operating_company": True},
                recommendation="Verificar que la caja del plan nunca sea negativa; si lo es, "
                               "el caso sí requiere un ticket.",
            )
        return Finding(
            id="DD03", name="financing_present", severity_class=STRUCTURAL, passed=False,
            message="Falta input esencial: `VC` <= 0 (sin capital de trabajo inicial para ejecutar el plan).",
            evidence={"VC": vc},
            recommendation="Definir un `VC` (capital de trabajo inicial) > 0, o declarar "
                           "`operating_company: true` si la empresa ya opera sin ticket.",
        )
    return _ok("DD03", "financing_present", f"Financiamiento inicial VC={vc:,.0f}.")


def _rule_churn_valid(config: dict[str, Any]) -> Finding:
    bad = [
        s.get("nombre", str(i))
        for i, s in enumerate(config.get("servicios", []))
        if any(not (0.0 <= float(v) <= 1.0) for v in s.get("churn_anual", []))
    ]
    if bad:
        return Finding(
            id="DD04", name="churn_valid", severity_class=STRUCTURAL, passed=False,
            message=f"Config inválido: `churn_anual` fuera de [0,1] en {', '.join(bad)}.",
            evidence={"servicios": bad},
            recommendation="Expresar churn anual como fracción en [0,1].",
        )
    return _ok("DD04", "churn_valid", "Churn anual dentro de [0,1].")


# ----- Startup-eligibility / synthesis rules (deterministic outputs) -------


def _rule_churn_severity(config: dict[str, Any], thresholds: dict[str, float]) -> Finding:
    services = config.get("servicios", [])
    max_churn = max((max(s.get("churn_anual", [0.0])) for s in services), default=0.0)
    major = float(thresholds["churn_major"])
    warn = float(thresholds["churn_warn"])
    evidence = {"max_annual_churn": max_churn, "warn": warn, "major": major}
    if max_churn >= major:
        return Finding(
            id="DD05", name="churn_severity", severity_class=MAJOR, passed=False,
            message=f"Churn anual máximo {max_churn:.0%} extremo — retención incompatible con escalamiento.",
            evidence=evidence,
            recommendation="Replantear retención/recurrencia; reducir `churn_anual` o aumentar `frecuencia`.",
        )
    if max_churn >= warn:
        return Finding(
            id="DD05", name="churn_severity", severity_class=WARNING, passed=False,
            message=f"Churn anual máximo {max_churn:.0%} alto — riesgo de retención.",
            evidence=evidence,
            recommendation="Validar churn con datos; considerar mejoras de retención.",
        )
    return _ok("DD05", "churn_severity", f"Churn anual máximo {max_churn:.0%} en rango aceptable.")


def _rule_breakeven(optimized: pd.DataFrame, thresholds: dict[str, float]) -> Finding:
    cumulative = optimized["EBITDA"].cumsum()
    positive = optimized.loc[cumulative >= 0, "t"]
    warn_month = float(thresholds["breakeven_warn_month"])
    if positive.empty:
        return Finding(
            id="DD06", name="breakeven_within_horizon", severity_class=MAJOR, passed=False,
            message="El EBITDA acumulado nunca llega a cero — sin régimen de EBITDA creíble en el horizonte.",
            evidence={"breakeven_month": None, "horizon": int(optimized["t"].max())},
            recommendation="Extender horizonte `H`, mejorar margen, o reducir costos fijos (`g_adm`/`RRHH`).",
        )
    month = int(positive.iloc[0])
    if month > warn_month:
        return Finding(
            id="DD06", name="breakeven_within_horizon", severity_class=WARNING, passed=False,
            message=f"Breakeven tardío en el mes {month} (> {int(warn_month)}).",
            evidence={"breakeven_month": month, "warn_month": warn_month},
            recommendation="Acelerar adquisición rentable o reducir estructura de costos.",
        )
    return _ok("DD06", "breakeven_within_horizon", f"Breakeven en el mes {month}.")


def _rule_ebitda_regime(optimized: pd.DataFrame, thresholds: dict[str, float]) -> Finding:
    target_year = int(thresholds["ebitda_regime_year"])
    available_years = sorted(optimized["Año"].unique())
    if target_year not in available_years:
        return _ok(
            "DD09", "ebitda_regime_by_year3",
            f"Horizonte no alcanza el año {target_year}; régimen de EBITDA no evaluado.",
        )
    annual_ebitda = float(optimized.loc[optimized["Año"] == target_year, "EBITDA"].sum())
    if annual_ebitda <= 0:
        return Finding(
            id="DD09", name="ebitda_regime_by_year3", severity_class=MAJOR, passed=False,
            message=f"EBITDA anual del año {target_year} no positivo ({annual_ebitda:,.0f}) — sin régimen de rentabilidad creíble.",
            evidence={"year": target_year, "annual_ebitda": annual_ebitda},
            recommendation="Revisar pricing, costos y velocidad de adquisición para alcanzar EBITDA positivo hacia el año 3.",
        )
    return _ok("DD09", "ebitda_regime_by_year3", f"EBITDA año {target_year} positivo ({annual_ebitda:,.0f}).")


def _rule_revenue_growth(optimized: pd.DataFrame, thresholds: dict[str, float]) -> Finding:
    by_year = optimized.groupby("Año")["Ingresos"].sum()
    if len(by_year) < 2:
        return _ok("DD10", "revenue_growth", "Horizonte insuficiente para evaluar crecimiento anual.")
    first_year = float(by_year.iloc[0])
    last_year = float(by_year.iloc[-1])
    multiple = last_year / first_year if first_year > 0 else float("inf")
    min_multiple = float(thresholds["revenue_growth_min_multiple"])
    evidence = {"first_year_revenue": first_year, "last_year_revenue": last_year, "multiple": multiple, "min_multiple": min_multiple}
    if multiple < min_multiple:
        return Finding(
            id="DD10", name="revenue_growth", severity_class=MAJOR, passed=False,
            message=f"Crecimiento de ingresos {multiple:.2f}× en el horizonte (< {min_multiple:.2f}×) — perfil tipo PYME, no escalable.",
            evidence=evidence,
            recommendation="Revisar supuestos de adquisición/recurrencia; el caso debe mostrar crecimiento tipo venture.",
        )
    return _ok("DD10", "revenue_growth", f"Crecimiento de ingresos {multiple:.2f}× en el horizonte.")


def rule_exit_roi(
    multiples: dict[str, Any],
    dcf: dict[str, Any],
    config: dict[str, Any],
    thresholds: dict[str, float],
) -> Finding:
    """VC 3x rule (reunión A. Maureira 2026-07-01): exit value (múltiplo de
    ingresos del último año) debe ser >= `exit_roi_min` veces el post-money
    mínimo (pre-money + VC invertido). Nunca estructural: es elegibilidad
    venture, no un problema de modelado."""
    exit_value = float(multiples.get("valor_por_ingresos", 0.0))
    van = float(dcf.get("VAN", 0.0))
    vc = float(config.get("VC", 0.0))
    # Post-money mínimo = pre-money + inversión; el pre-money no puede aportar
    # valor negativo a la caja (piso en 0).
    post_money_min = max(van, 0.0) + vc
    minimum = float(thresholds["exit_roi_min"])
    evidence = {
        "exit_value_revenue_multiple": exit_value,
        "pre_money_van": van,
        "vc": vc,
        "post_money_min": post_money_min,
        "exit_roi_min": minimum,
    }
    if post_money_min <= 0:
        return _ok("DD12", "exit_roi", "Sin post-money evaluable (VC=0 y VAN<=0); ROI de exit no aplica.")
    roi = exit_value / post_money_min
    evidence["exit_roi"] = roi
    if roi < minimum:
        return Finding(
            id="DD12", name="exit_roi", severity_class=WARNING, passed=False,
            message=f"ROI de exit {roi:.1f}× < {minimum:.0f}× (exit {exit_value:,.0f} vs "
                    f"post-money mínimo {post_money_min:,.0f}) — bajo el umbral que exige un venture capital.",
            evidence=evidence,
            recommendation="Mejorar la trayectoria de ingresos del año 3 o negociar entrada a un "
                           "post-money menor; con ROI < 3× la inversión no es venture-atractiva.",
        )
    return Finding(
        id="DD12", name="exit_roi", severity_class=OK, passed=True,
        message=f"ROI de exit {roi:.1f}× ≥ {minimum:.0f}× (exit {exit_value:,.0f}).",
        evidence=evidence,
    )


# ----- Growth commitment / hiring warnings (ADR 0014, plan §4) --------------
# W1-W5: always WARNING severity, never structural/major/minor — the commitment
# is an investment-thesis choice, not a modeling defect. Evaluated only when
# growth_commitment is present in the config (opt-in feature); absent/disabled
# config produces no findings (no-op).


def rule_growth_commitment_warnings(
    config: dict[str, Any], suggestions: dict[str, Any] | None
) -> list[Finding]:
    """W1-W5 growth-commitment/calibration warnings.

    ``suggestions`` is the dict returned by
    :func:`adventure_capital.instance.compute_growth_suggestions` (g_vc_minimum,
    g_plan_mom_stock, C12, etc). When ``growth_commitment`` is absent or
    disabled in ``config``, returns an empty list (strict no-op).
    """
    growth_commitment = config.get("growth_commitment", {}) or {}
    if not growth_commitment.get("enabled", False):
        return []

    findings: list[Finding] = []
    suggestions = suggestions or {}
    source = growth_commitment.get("source", "vc_minimum")
    g_vc_minimum = float(suggestions.get("g_vc_minimum", 0.0))
    g_plan_mom_stock = float(suggestions.get("g_plan_mom_stock", 0.0))
    c12 = float(suggestions.get("C12", 0.0))

    # W5: plan inconsistent — C12 ~ 0 or MoM not computable. Checked first: if
    # this fires, W1/W2 (which depend on g_plan_mom_stock) are not meaningful.
    plan_degenerate = c12 <= 1e-9
    if plan_degenerate:
        findings.append(
            Finding(
                id="DD15", name="growth_commitment_plan_inconsistent",
                severity_class=WARNING, passed=False,
                message="El plan consensuado no permite anclar el piso de crecimiento "
                        f"(C12≈{c12:.2f}, stock casi nulo o MoM no computable).",
                evidence={"C12": c12},
                recommendation="Revisar A_base y churn del año 1 antes de fijar un compromiso de crecimiento.",
            )
        )

    if source == "plan_mom" and not plan_degenerate:
        # W1: plan_mom suspiciously fast vs the VC-minimum benchmark.
        if g_vc_minimum > 0 and g_plan_mom_stock > 2.0 * g_vc_minimum:
            findings.append(
                Finding(
                    id="DD13", name="growth_commitment_plan_mom_suspicious",
                    severity_class=WARNING, passed=False,
                    message=f"El MoM del plan implica un crecimiento de stock de "
                            f"{g_plan_mom_stock:.1%}/año (> 2x el mínimo VC de {g_vc_minimum:.1%}/año) "
                            "— revisar con el cliente antes de usarlo como compromiso.",
                    evidence={"g_plan_mom_stock": g_plan_mom_stock, "g_vc_minimum": g_vc_minimum},
                    recommendation="Confirmar con el cliente que el MoM del plan es sostenible antes "
                                   "de fijarlo como piso de compromiso; considerar `vc_minimum` en su lugar.",
                )
            )
        # W2: plan grows below the VC thesis.
        elif g_plan_mom_stock < g_vc_minimum:
            findings.append(
                Finding(
                    id="DD14", name="growth_commitment_plan_below_thesis",
                    severity_class=WARNING, passed=False,
                    message=f"El plan consensuado crece bajo la tesis ×{growth_commitment.get('multiple_3y', 3.0):.1f} "
                            f"({g_plan_mom_stock:.1%}/año < {g_vc_minimum:.1%}/año) — el compromiso exigirá "
                            "acelerar sobre el plan.",
                    evidence={"g_plan_mom_stock": g_plan_mom_stock, "g_vc_minimum": g_vc_minimum},
                    recommendation="Confirmar que el equipo comercial puede acelerar sobre el MoM histórico, "
                                   "o usar `vc_minimum`/`custom` con un piso más conservador.",
                )
            )

    # W4: custom source without a recorded justification.
    if source == "custom":
        justification = growth_commitment.get("custom_justification")
        if not justification or not str(justification).strip():
            findings.append(
                Finding(
                    id="DD16", name="growth_commitment_custom_unjustified",
                    severity_class=WARNING, passed=False,
                    message="Override experto (`custom`) sin justificación registrada "
                            "(`custom_justification` vacío o ausente).",
                    evidence={"source": source},
                    recommendation="Registrar `custom_justification` con el fundamento del experto (Alejandro) "
                                   "para el `custom_g_annual` elegido.",
                )
            )

    return findings


def rule_growth_commitment_infeasible(
    solver_status: str, config: dict[str, Any], diagnosis: dict[str, Any] | None = None
) -> Finding | None:
    """W3: solver Infeasible with growth_commitment enabled is a VALID business
    result ("this structure does not support the x3 thesis"), never an error.
    Attaches the structured diagnosis (plan §5) when available. Returns None
    when growth_commitment is not enabled (no-op) or the solve was not
    infeasible."""
    growth_commitment = config.get("growth_commitment", {}) or {}
    if not growth_commitment.get("enabled", False):
        return None
    if solver_status not in {"Infeasible", "Undefined"}:
        return None
    return Finding(
        id="DD17", name="growth_commitment_infeasible",
        severity_class=WARNING, passed=False,
        message=f"El solver reportó {solver_status} con growth_commitment activo — "
                "resultado válido de negocio: esta estructura no soporta la tesis de crecimiento declarada.",
        evidence={"solver_status": solver_status, "diagnosis": diagnosis or {}},
        recommendation="Revisar el diagnóstico de infactibilidad (scripts/diagnose_infeasibility.py) "
                       "para identificar qué palancas (contratación, canal, mix, churn, costo, caja, "
                       "o el propio múltiplo) restaurarían la factibilidad.",
    )


def rule_conservative_plan_diagnostic(config: dict[str, Any]) -> Finding | None:
    """DD18: parameter-sweep diagnostic for conservative committed growth.

    The sweep changes ``investment_thesis.multiple`` between solves. It never
    introduces ratio/M variables into the MILP and never calibrates VAN directly.
    """
    if not (config.get("growth_commitment") or {}).get("enabled", False):
        return None
    if not (config.get("acquisition_envelope") or {}).get("enabled", False):
        return None

    from adventure_capital.growth_diagnostics import compute_conservative_plan_diagnostic

    diagnostic = compute_conservative_plan_diagnostic(config, max_iterations=8)
    classification = diagnostic.get("classification")
    evidence = {
        "classification": classification,
        "target_multiple": diagnostic.get("target_multiple"),
        "M_star_feasible": diagnostic.get("M_star_feasible"),
        "upper_multiple": diagnostic.get("upper_multiple"),
        "upper_bound_hit": diagnostic.get("upper_bound_hit"),
        "thesis_gap": diagnostic.get("thesis_gap"),
        "van_at_probe": diagnostic.get("van_at_probe"),
    }
    if classification == "Infeasible":
        return Finding(
            id="DD18",
            name="conservative_plan_diagnostic",
            severity_class=WARNING,
            passed=False,
            message="La tesis declarada no es factible bajo el barrido conservador de M.",
            evidence=evidence,
            recommendation="Revisar el múltiplo de tesis, caja/costos o capacidad comercial antes de usar el plan como demo.",
        )
    if classification == "Conservative":
        cap_phrase = (
            " El barrido fue feasible up to tested cap; este valor es un límite "
            "probado, no un máximo de mercado."
            if evidence["upper_bound_hit"]
            else " El valor reportado es el mayor múltiplo factible encontrado por el barrido, no un máximo de mercado."
        )
        return Finding(
            id="DD18",
            name="conservative_plan_diagnostic",
            severity_class=OK,
            passed=True,
            message=(
                "El plan parece conservador: existe headroom factible para un múltiplo "
                "mayor y el VAN no disminuye en los probes superiores."
                + cap_phrase
            ),
            evidence=evidence,
            recommendation=(
                "Reportar el headroom como diagnóstico; no recalibrar VAN, solo decidir "
                "si la tesis de crecimiento declarada debe subir."
            ),
        )
    return Finding(
        id="DD18",
        name="conservative_plan_diagnostic",
        severity_class=OK,
        passed=True,
        message="La tesis de crecimiento está calibrada: sin headroom VAN-acretivo claro.",
        evidence=evidence,
    )


# ----- Liquidity diagnostic (reported, not pass/fail eligibility) ----------


def _rule_runway(optimized: pd.DataFrame, thresholds: dict[str, float]) -> Finding:
    negative = optimized.loc[optimized["Caja"] < 0, "t"]
    minor_month = float(thresholds["runway_minor"])
    if negative.empty:
        return _ok("DD07", "runway", "La caja nunca cae por debajo de cero.")
    first_negative = int(negative.iloc[0])
    evidence = {"first_cash_negative_month": first_negative, "runway_minor": minor_month}
    # Liquidity is diagnostic: minor (fixable) at worst, never structural.
    severity = MINOR if first_negative <= minor_month else WARNING
    return Finding(
        id="DD07", name="runway", severity_class=severity, passed=False,
        message=f"La caja se vuelve negativa en el mes {first_negative} — presión de capital de trabajo (diagnóstico).",
        evidence=evidence,
        recommendation="Aumentar `VC`, diferir contrataciones, o suavizar la aceleración de adquisición.",
    )


def _working_capital_floor(config: dict[str, Any]) -> float:
    working_capital = config.get("working_capital", {}) or {}
    if working_capital.get("enabled", False) and "VC" in config:
        return -float(config.get("VC", 0.0))
    return 0.0


def _rule_funding_gap(optimized: pd.DataFrame, config: dict[str, Any], thresholds: dict[str, float]) -> Finding:
    min_cash = float(optimized["Caja"].min())
    floor = _working_capital_floor(config)
    gap = max(0.0, floor - min_cash)
    vc = float(config.get("VC", 0.0)) or 1.0
    ratio = gap / vc
    warn = float(thresholds["gap_warn"])
    minor = float(thresholds["gap_minor"])
    evidence = {"funding_gap": gap, "vc": vc, "floor": floor, "gap_over_vc": ratio, "warn": warn, "minor": minor}
    if ratio >= minor:
        return Finding(
            id="DD08", name="funding_gap_severity", severity_class=MINOR, passed=False,
            message=f"Capital de trabajo requerido {gap:,.0f} = {ratio:.1f}× el VC — brecha alta (diagnóstico).",
            evidence=evidence,
            recommendation="Asegurar financiamiento intermedio o reestructurar el ritmo de gasto/adquisición.",
        )
    if ratio >= warn:
        return Finding(
            id="DD08", name="funding_gap_severity", severity_class=WARNING, passed=False,
            message=f"Capital de trabajo requerido {gap:,.0f} = {ratio:.1f}× el VC.",
            evidence=evidence,
            recommendation="Monitorear el colchón de caja; podría requerirse financiamiento puente.",
        )
    return _ok("DD08", "funding_gap_severity", f"Brecha de financiamiento moderada ({gap:,.0f}).")


def compute_liquidity_diagnostic(optimized: pd.DataFrame, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Liquidity trajectory summary — reported regardless of verdict."""
    cash = optimized["Caja"].astype(float)
    min_cash = float(cash.min())
    min_cash_month = int(optimized.loc[cash.idxmin(), "t"])
    floor = _working_capital_floor(config or {})
    gap_series = (floor - cash).clip(lower=0.0)
    max_gap = float(gap_series.max())
    max_gap_month = int(optimized.loc[gap_series.idxmax(), "t"]) if max_gap > 0 else None

    cumulative_ebitda = optimized["EBITDA"].cumsum()
    breakeven = optimized.loc[cumulative_ebitda >= 0, "t"]
    breakeven_month = int(breakeven.iloc[0]) if not breakeven.empty else None

    went_negative = bool((cash < 0).any())
    cash_recovers = bool(went_negative and float(cash.iloc[-1]) >= 0)

    return {
        "min_cash": min_cash,
        "min_cash_month": min_cash_month,
        "working_capital_floor": floor,
        "max_funding_gap": max_gap,
        "max_funding_gap_month": max_gap_month,
        "breakeven_month": breakeven_month,
        "cash_went_negative": went_negative,
        "cash_recovers": cash_recovers,
        "final_cash": float(cash.iloc[-1]),
    }


# ----- Calibration mapping -------------------------------------------------


def map_calibration_findings(
    calibration: Any,
    *,
    blocking_ids: list[str] | None = None,
    major_ids: list[str] | None = None,
    overrides: dict[str, str] | None = None,
) -> list[Finding]:
    """Map calibration ``CheckResult``s into DD findings (no logic duplicated).

    Severity: ids in ``blocking_ids`` -> structural; ids in ``major_ids`` ->
    major; other failing errors -> minor; warnings -> warning. ``overrides``
    forces a specific class per check id. Passing/skipped checks are ignored.
    """
    if calibration is None:
        return []
    blocking = set(blocking_ids or ["C01"])
    major = set(major_ids or [])
    overrides = overrides or {}

    findings: list[Finding] = []
    for check in getattr(calibration, "checks", []):
        if check.passed or check.skipped:
            continue
        if check.id in overrides:
            severity = overrides[check.id]
        elif check.id in blocking:
            severity = STRUCTURAL
        elif check.id in major:
            severity = MAJOR
        elif check.severity == "error":
            severity = MINOR
        else:
            severity = WARNING
        findings.append(
            Finding(
                id=check.id, name=check.name, severity_class=severity, passed=False,
                message=check.message,
                evidence={"value": check.value, "threshold": check.threshold},
                source="calibration",
            )
        )
    return findings


# ----- Orchestration helpers ----------------------------------------------


def evaluate_pre_rules(config: dict[str, Any], thresholds: dict[str, float]) -> list[Finding]:
    return [
        _rule_instance_valid(config),
        _rule_unit_margin_positive(config),
        _rule_financing_present(config),
        _rule_churn_valid(config),
        _rule_churn_severity(config, thresholds),
    ]


def evaluate_synthesis_rules(
    optimized: pd.DataFrame | None, config: dict[str, Any], thresholds: dict[str, float]
) -> list[Finding]:
    if optimized is None or optimized.empty:
        return [
            Finding(
                id="DD00", name="synthesis_unavailable", severity_class=STRUCTURAL, passed=False,
                message="No hay resultados optimizados para evaluar reglas de síntesis.",
                recommendation="Verificar que el modelo determinista corrió y produjo resultados.",
            )
        ]
    return [
        _rule_breakeven(optimized, thresholds),
        _rule_ebitda_regime(optimized, thresholds),
        _rule_revenue_growth(optimized, thresholds),
        _rule_runway(optimized, thresholds),
        _rule_funding_gap(optimized, config, thresholds),
    ]


def resolve_thresholds(dd_config: dict[str, Any] | None) -> dict[str, float]:
    merged = dict(DEFAULT_THRESHOLDS)
    if dd_config:
        merged.update(dd_config.get("thresholds", {}) or {})
    return merged

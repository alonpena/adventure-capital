"""Auto-suggestion engine for calibration warnings and failures.

Given a ``CheckResult`` plus the model instance, produce a single accionable
Spanish-language hint that names a parameter to tweak and an approximate
target value computed from the observed evidence.
"""

from __future__ import annotations

from typing import Any

from adventure_capital.calibration.checks import CheckResult


def _format_money(value: float | None) -> str:
    if value is None or value != value:
        return "—"
    if abs(value) >= 1_000_000:
        return f"USD {value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"USD {value / 1_000:.1f}K"
    return f"USD {value:,.0f}"


def _suggest_C01(result: CheckResult, instance: dict[str, Any]) -> str:
    return (
        "Inspeccionar restricciones del modelo: `liquidity_policy`, "
        "`commercial_productivity_lag`, monotonicidad de vendedores. "
        "Revisar también si `solver.time_limit` ({} s) es suficiente."
    ).format(instance.get("solver", {}).get("time_limit", "?"))


def _suggest_C02(result: CheckResult, instance: dict[str, Any]) -> str:
    value = result.value
    meta_actual = float(value.get("meta", 0.0)) or 1.0
    rem_v = float(instance.get("rem_v", 0.0))
    rem_l = float(instance.get("rem_l", 0.0))
    meta_sugerida = max(1, int(round(meta_actual / 2)))
    return (
        f"Reducir `meta` de {meta_actual:.0f} a ~{meta_sugerida} para forzar al optimizador a contratar más vendedores. "
        f"Alternativa: bajar `rem_v` actual ({rem_v:.0f}) o `rem_l` ({rem_l:.0f}) "
        "para que el costo marginal de un seller adicional sea económicamente viable. "
        "El plan actual representa cosecha sobre capacidad fija, no aceleración."
    )


def _suggest_C03(result: CheckResult, instance: dict[str, Any]) -> str:
    return (
        "El optimizador no contrata más vendedores aunque tenga demanda. "
        "Causas típicas: (a) `rem_v`/`rem_l` muy altos vs ticket marginal; "
        "(b) monotonicidad (`sellers[t] ≥ sellers[t-1]`) hace permanente cualquier hire; "
        "(c) WACC alto descuenta agresivamente el upside futuro. "
        "Verificar también si `meta` no permite ya saturar la demanda con 1 seller."
    )


def _suggest_C04(result: CheckResult, instance: dict[str, Any]) -> str:
    value = result.value
    min_cash = float(value.get("min_cash", 0.0))
    needed = -min_cash + 50_000
    vc_actual = float(instance.get("VC", 0.0))
    return (
        f"Caja mínima {_format_money(min_cash)} en mes {value.get('min_month', '?')}. "
        f"Subir `VC` actual ({_format_money(vc_actual)}) a al menos {_format_money(vc_actual + needed)} "
        "o activar `liquidity_policy.minimum_cash` para que el modelo respete un piso de caja."
    )


def _suggest_C05(result: CheckResult, instance: dict[str, Any]) -> str:
    return (
        "EBITDA acumulado negativo. Revisar (a) ticket por servicio vs `c_u` y `c_min` (margen unitario), "
        "(b) `g_adm`/`RRHH_mensual` vs ingresos esperados, (c) `meta` (puede estar limitando captación). "
        "Si el plan no llega a EBITDA positivo, el horizonte H actual es insuficiente o el modelo no es viable."
    )


def _suggest_C06(result: CheckResult, instance: dict[str, Any]) -> str:
    return (
        "VAN negativo: los flujos descontados no compensan la inversión. "
        "Probar (a) reducir WACC (si los componentes están sobre-estimados: `Rf`, `castigo_riesgo`), "
        "(b) extender horizonte `H`, "
        "(c) revisar terminal value/método de desecho. "
        "Si el modelo es correcto, el negocio no se valoriza positivamente con los parámetros actuales."
    )


def _suggest_C07(result: CheckResult, instance: dict[str, Any]) -> str:
    value = result.value
    gp = float(value.get("gross_profit", 0.0))
    revenue = float(value.get("revenue", 0.0))
    cost = float(value.get("cost", 0.0))
    services = instance.get("servicios", [])
    if gp > 0.92 and services:
        first = services[0]
        ticket = float(first.get("ticket", 0.0))
        c_u_actual = float(first.get("c_u", 0.0))
        suggested_c_u = max(round(ticket * 0.20, 0), c_u_actual + 50)
        return (
            f"Gross profit {gp:.1%} es muy alto. `c_u` (actual {c_u_actual:.0f}) "
            f"probablemente subestima el costo real de delivery. "
            f"Sugerencia: `c_u ≈ {suggested_c_u:.0f}` (≈20% del ticket) o activar `c_min` > 0 "
            "para reflejar costo fijo de capacidad. Servicios reales B2B rara vez superan 85% GP sostenido."
        )
    if gp < 0.30:
        return (
            f"Gross profit {gp:.1%} muy bajo para perfil VC. "
            "Revisar pricing (`ticket`) o reducir `c_u`/`c_min`. "
            "Sin gross profit > 30%, las economías de escala no llegan."
        )
    return "Gross profit fuera de banda — revisar costos y pricing."


def _suggest_C08(result: CheckResult, instance: dict[str, Any]) -> str:
    value = result.value
    ratio = float(value.get("ltv_cac", 0.0))
    if ratio > 20:
        return (
            f"LTV/CAC = {ratio:.0f}× es artefacto: la fórmula actual en `unit_economics.py` usa "
            "`ticket_promedio` aritmético y `marginal_gp` del primer servicio. "
            "Corrección recomendada: (a) calcular ARPU ponderado por adquisición real "
            "(Σ Ingresos / Σ adquisición), (b) usar `gross_profit` agregado en lugar del margen del primer servicio, "
            "(c) tratar `frecuencia` y `alpha` en el horizonte real (no a infinito). "
            "Una banda LTV/CAC realista B2B es 3×–10×."
        )
    return (
        f"LTV/CAC = {ratio:.1f}× < 1×: cada cliente genera menos valor del que cuesta adquirirlo. "
        "Subir ticket o bajar CAC (reducir `com_v`/`com_l` o `rem_v`/`rem_l`)."
    )


def _suggest_C09(result: CheckResult, instance: dict[str, Any]) -> str:
    value = result.value
    top = value.get("top_service", "?")
    pct = float(value.get("top_pct", 0.0))
    return (
        f"{pct:.0%} de la adquisición se concentra en '{top}'. "
        "El modelo prefiere ese plan ampliamente. Considerar (a) eliminar servicios con <10% del mix "
        "para simplificar el portafolio, (b) revisar tickets/c_u si la concentración no es deseada "
        "(quizás otros planes tienen margen unitario más bajo que el optimizador descarta)."
    )


def _suggest_C10(result: CheckResult, instance: dict[str, Any]) -> str:
    value = result.value
    ratio = float(value.get("ratio", 0.0))
    services = instance.get("servicios", [])
    avg_churn = (
        sum(float(s.get("churn_anual", [0.0])[0]) for s in services) / len(services)
        if services
        else 0.0
    )
    suggested_churn = max(0.10, round(avg_churn - 0.20, 2))
    return (
        f"Retención agregada {ratio:.0%} es baja. "
        f"Churn anual promedio actual: {avg_churn:.0%}. "
        f"Sugerencia: bajar `churn_anual` a {suggested_churn:.0%} si es factible operativamente, "
        "o aumentar `frecuencia` (más compras por año mejoran la retención efectiva). "
        "Sin retención, la economía recurrente del modelo no se materializa."
    )


def _suggest_C11(result: CheckResult, instance: dict[str, Any]) -> str:
    value = result.value
    missing_fields = value.get("missing_document_fields", [])
    missing_files = value.get("missing_core_artifacts", [])
    parts = []
    if missing_fields:
        parts.append(f"Completar campos en el YAML documental: {', '.join(missing_fields)}.")
    if missing_files:
        parts.append(f"Volver a correr el pipeline para producir: {', '.join(missing_files)}.")
    if not parts:
        parts.append("Revisar el schema en `reports/schema/valuation-document.schema.yaml`.")
    return " ".join(parts)


SUGGESTIONS = {
    "C01": _suggest_C01,
    "C02": _suggest_C02,
    "C03": _suggest_C03,
    "C04": _suggest_C04,
    "C05": _suggest_C05,
    "C06": _suggest_C06,
    "C07": _suggest_C07,
    "C08": _suggest_C08,
    "C09": _suggest_C09,
    "C10": _suggest_C10,
    "C11": _suggest_C11,
}


def build_suggestion(result: CheckResult, instance: dict[str, Any]) -> str:
    """Return an actionable Spanish suggestion for a failed check."""
    if result.passed or result.skipped:
        return ""
    builder = SUGGESTIONS.get(result.id)
    if not builder:
        return "Revisar parámetros del modelo y umbrales de calibración."
    try:
        return builder(result, instance)
    except Exception as exc:  # defensive
        return f"Sugerencia indisponible (error interno: {exc})."

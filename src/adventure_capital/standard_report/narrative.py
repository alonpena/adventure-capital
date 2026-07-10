"""Spanish threshold-based narrative engine for the standard valuation report.

Each builder receives already-aggregated metrics (annual tables, unit economics,
valuation parameters) and emits a dict with a short ``headline`` plus an
ordered list of ``paragraphs``. The phrasing varies based on threshold bands
so the report reads as if it were tailored to the case.
"""

from __future__ import annotations

import math
from typing import Any


def _fmt_money(value: float | None) -> str:
    if value is None or value != value:
        return "USD 0"
    if abs(value) >= 1_000_000:
        return f"USD {value / 1_000_000:.2f} MM"
    if abs(value) >= 1_000:
        return f"USD {value / 1_000:.1f}K"
    return f"USD {value:,.0f}"


def _fmt_pct(value: float | None) -> str:
    if value is None or value != value:
        return "—"
    return f"{value * 100:.1f}%"


def _fmt_number(value: float | None, decimals: int = 0) -> str:
    if value is None or value != value:
        return "—"
    return f"{value:,.{decimals}f}"


def _band(value: float, bands: list[tuple[float, str]], default: str) -> str:
    """bands: list of (upper_bound_exclusive, label). Last default catches the rest."""
    for upper, label in bands:
        if value < upper:
            return label
    return default


def _safe(value: Any) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return f if not math.isnan(f) else float("nan")


def narrate_clients(clients_summary: list[tuple], unit_economics: dict[str, float]) -> dict[str, Any]:
    if not clients_summary:
        return {"headline": "Sin datos suficientes de clientes.", "paragraphs": []}

    total_acq = sum(row[1] for row in clients_summary)
    stock_inicial = clients_summary[0][2]
    stock_final = clients_summary[-1][2]
    growth = (stock_final / stock_inicial - 1) if stock_inicial else float("nan")
    churn = _safe(unit_economics.get("CHURN", float("nan")))
    mom_growth = _safe(unit_economics.get("MoM Growth", float("nan")))

    churn_band = _band(churn, [(0.30, "saludable (bajo)"), (0.50, "moderado")], "elevado")
    mom_band = _band(mom_growth, [(0.0, "contracción"), (0.05, "lento"), (0.15, "sostenido")], "acelerado")

    paragraphs = [
        (
            f"En el horizonte modelado se adquieren **{_fmt_number(total_acq)} clientes**, "
            f"creciendo el stock activo desde {_fmt_number(stock_inicial, 1)} en el año 1 hasta "
            f"{_fmt_number(stock_final, 1)} al cierre, equivalente a {_fmt_pct(growth)} de expansión."
        ),
        (
            f"El churn anual promedio se ubica en {_fmt_pct(churn)} ({churn_band}). "
            f"Con un crecimiento mensual equivalente (MoM) de {_fmt_pct(mom_growth)}, "
            f"el ritmo de adquisición se clasifica como {mom_band}."
        ),
    ]
    if churn >= 0.50:
        paragraphs.append(
            "La tasa de fuga supera el 50% anual, lo que obliga al modelo a sustituir más de la mitad "
            "del stock cada año. Es la principal palanca de mejora: cada reducción de 10 puntos "
            "amplifica el LTV y descomprime la presión sobre adquisición."
        )
    elif churn >= 0.30:
        paragraphs.append(
            "El churn se encuentra en niveles moderados, dentro de lo esperado para B2B con servicios "
            "anuales; vale la pena monitorearlo como métrica primaria de retención."
        )
    return {"headline": f"Clientes: {_fmt_number(stock_final, 1)} activos al cierre", "paragraphs": paragraphs}


def narrate_services(services_summary: list[tuple], services_meta: list[str], unit_economics: dict[str, float]) -> dict[str, Any]:
    if not services_summary:
        return {"headline": "Sin datos de servicios.", "paragraphs": []}
    nuevos_total = sum(row[1] for row in services_summary)
    recurrentes_total = sum(row[2] for row in services_summary)
    totales = nuevos_total + recurrentes_total
    arr_pct = (recurrentes_total / totales) if totales > 0 else 0.0
    recurrencia = _safe(unit_economics.get("Recurrencia mensual", 0.0))

    arr_band = _band(arr_pct, [(0.30, "bajo"), (0.60, "moderado")], "alto")
    paragraphs = [
        (
            f"Se ofrecen {_fmt_number(len(services_meta))} planes ({', '.join(services_meta) if services_meta else '—'}). "
            f"La mezcla de servicios totales es de {_fmt_number(nuevos_total)} nuevos y "
            f"{_fmt_number(recurrentes_total)} recurrentes a lo largo del horizonte."
        ),
        (
            f"La participación recurrente representa {_fmt_pct(arr_pct)} del volumen total ({arr_band}). "
            f"La recurrencia mensual configurada es {_fmt_number(recurrencia, 2)} servicios/cliente/mes, "
            "que sostiene el flujo en años posteriores al ramp-up inicial."
        ),
    ]
    if arr_pct < 0.30:
        paragraphs.append(
            "La base recurrente aún es delgada: el crecimiento depende principalmente de nuevas ventas. "
            "Aumentar la frecuencia o ampliar la oferta hacia productos anuales reduce el riesgo de canal."
        )
    return {"headline": f"Servicios: {_fmt_pct(arr_pct)} recurrencia", "paragraphs": paragraphs}


def narrate_revenue(revenue_summary: list[tuple], n_services: int) -> dict[str, Any]:
    if not revenue_summary or len(revenue_summary) < 1:
        return {"headline": "Sin datos de ingresos.", "paragraphs": []}
    totals = [row[-3] for row in revenue_summary]
    first_year = totals[0]
    last_year = totals[-1]
    yoy_growth: list[float] = []
    for i in range(1, len(totals)):
        if totals[i - 1] > 0:
            yoy_growth.append(totals[i] / totals[i - 1] - 1)
    avg_growth = sum(yoy_growth) / len(yoy_growth) if yoy_growth else float("nan")
    growth_band = _band(avg_growth, [(0.0, "negativo"), (0.30, "bajo"), (0.80, "sostenido")], "acelerado")

    paragraphs = [
        (
            f"Los ingresos pasan de {_fmt_money(first_year)} en el primer año a "
            f"{_fmt_money(last_year)} al final del horizonte, distribuidos en {n_services} planes."
        ),
        (
            f"El crecimiento YoY promedio es {_fmt_pct(avg_growth)} ({growth_band}). "
            f"La curva refleja la maduración de cohortes B2B donde el ticket alto compensa volúmenes acotados."
        ),
    ]
    # ARR signal
    if revenue_summary and len(revenue_summary[-1]) >= 1:
        arr_pct = revenue_summary[-1][-1]
        if isinstance(arr_pct, (int, float)) and not math.isnan(arr_pct):
            if arr_pct < 0.20:
                paragraphs.append(
                    f"En el último año, sólo {_fmt_pct(arr_pct)} de los ingresos provienen de recurrencia. "
                    "Acelerar contratos anuales o upsell sobre clientes activos haría más predecible el flujo."
                )
            elif arr_pct > 0.50:
                paragraphs.append(
                    f"En el último año, {_fmt_pct(arr_pct)} de los ingresos son recurrentes — base saludable "
                    "para apalancar valorizaciones tipo SaaS."
                )
    return {"headline": f"Ingresos año final: {_fmt_money(last_year)}", "paragraphs": paragraphs}


def narrate_cac(cac_summary: list[tuple], unit_economics: dict[str, float]) -> dict[str, Any]:
    if not cac_summary:
        return {"headline": "Sin datos de CAC.", "paragraphs": []}
    ltv = _safe(unit_economics.get("LTV", float("nan")))
    cac = _safe(unit_economics.get("CAC", float("nan")))
    ltv_cac = _safe(unit_economics.get("LTV/CAC", float("nan")))

    ratio_band = _band(ltv_cac, [(1.0, "crítico (LTV no cubre CAC)"), (3.0, "ajustado"), (5.0, "saludable")], "excepcional")

    fuerza_total = sum(row[1] for row in cac_summary)
    lideres_total = sum(row[2] for row in cac_summary)
    com_vendedor = sum(row[3] for row in cac_summary)
    com_lider = sum(row[4] for row in cac_summary)
    cac_total = sum(row[5] for row in cac_summary)
    total_force = fuerza_total + lideres_total
    total_commission = com_vendedor + com_lider
    if cac_total:
        force_pct = total_force / cac_total
        com_pct = total_commission / cac_total
    else:
        force_pct = com_pct = 0.0

    paragraphs = [
        (
            f"El CAC promedio del horizonte es {_fmt_money(cac)} por cliente, "
            f"con un LTV estimado de {_fmt_money(ltv)} y un ratio LTV/CAC de {_fmt_number(ltv_cac, 1)}× ({ratio_band})."
        ),
        (
            "Composición del costo de adquisición: "
            f"**{_fmt_pct(force_pct)}** corresponde a fuerza comercial fija "
            f"({_fmt_money(fuerza_total)} vendedores + {_fmt_money(lideres_total)} líderes), "
            f"mientras **{_fmt_pct(com_pct)}** son comisiones variables sobre ingresos "
            f"({_fmt_money(com_vendedor)} vendedor + {_fmt_money(com_lider)} líder)."
        ),
    ]
    if ltv_cac < 1.0:
        paragraphs.append(
            "Con LTV/CAC bajo 1× el modelo no es sostenible: cada cliente cuesta más de lo que aporta. "
            "Hay que renegociar comisiones, alargar la vida del cliente o subir ticket antes de escalar."
        )
    elif ltv_cac < 3.0:
        paragraphs.append(
            "El ratio LTV/CAC está bajo el umbral 3× típico de VC. Una mejora marginal de churn o de "
            "ticket recurrente lleva la unit economics a zona saludable."
        )
    elif ltv_cac > 10.0:
        paragraphs.append(
            "El ratio LTV/CAC es muy alto. Revisar si el cálculo de LTV no está sobre-estimando la vida "
            "del cliente (churn anualizado vs. mensual) o si conviene reinvertir más agresivamente en "
            "adquisición para acelerar la maduración."
        )
    return {"headline": f"CAC promedio: {_fmt_money(cac)} · LTV/CAC {_fmt_number(ltv_cac, 1)}×", "paragraphs": paragraphs}


def narrate_op_costs(op_cost_summary: list[tuple], unit_economics: dict[str, float]) -> dict[str, Any]:
    if not op_cost_summary:
        return {"headline": "Sin datos de costos operacionales.", "paragraphs": []}
    gp_values = [row[-1] for row in op_cost_summary if row[-1] is not None]
    last_year_gp = gp_values[-1] if gp_values else float("nan")
    avg_gp = sum(gp_values) / len(gp_values) if gp_values else float("nan")
    gp_band = _band(last_year_gp if last_year_gp == last_year_gp else 0.0, [(0.30, "bajo"), (0.60, "adecuado"), (0.80, "fuerte")], "premium")

    cost_total = sum(row[-3] for row in op_cost_summary)
    revenue_total = sum(row[-2] for row in op_cost_summary)
    cost_pct = (cost_total / revenue_total) if revenue_total > 0 else float("nan")

    paragraphs = [
        (
            f"Los costos operacionales agregados son {_fmt_money(cost_total)} contra ingresos de "
            f"{_fmt_money(revenue_total)}, equivalente a {_fmt_pct(cost_pct)} de absorción."
        ),
        (
            f"El Gross Profit del último año es {_fmt_pct(last_year_gp)} y el promedio del horizonte "
            f"{_fmt_pct(avg_gp)} — perfil de margen {gp_band}."
        ),
    ]
    if last_year_gp > 0.90:
        paragraphs.append(
            "Un GP sobre 90% es característico de servicios digitales de alto apalancamiento. "
            "Validar que c_u y c_min reflejen los costos reales de delivery (humano + infra)."
        )
    return {"headline": f"Gross Profit último año: {_fmt_pct(last_year_gp)}", "paragraphs": paragraphs}


def narrate_admin(admin_summary: list[tuple]) -> dict[str, Any]:
    if not admin_summary:
        return {"headline": "Sin datos administrativos.", "paragraphs": []}
    last_pct = admin_summary[-1][-1]
    last_amount = admin_summary[-1][2]
    total = sum(row[2] for row in admin_summary)
    pct_band = _band(last_pct if last_pct == last_pct else 0.0, [(0.05, "muy ligero"), (0.15, "controlado")], "alto")

    paragraphs = [
        (
            f"Los gastos administrativos suman {_fmt_money(total)} en el horizonte. "
            f"En el último año representan {_fmt_pct(last_pct)} de los ingresos ({pct_band})."
        ),
        (
            f"El último año cierra con {_fmt_money(last_amount)} de gasto anual, manteniéndose "
            "como costo cuasi-fijo independiente del volumen."
        ),
    ]
    return {"headline": f"Administración último año: {_fmt_money(last_amount)}", "paragraphs": paragraphs}


def narrate_hr(hr_summary: list[tuple]) -> dict[str, Any]:
    if not hr_summary:
        return {"headline": "Sin datos de RR.HH.", "paragraphs": []}
    last_planilla = hr_summary[-1][2]
    last_pct = hr_summary[-1][3]
    total_planilla = sum(row[2] for row in hr_summary)

    paragraphs = [
        (
            "La sección muestra solo RR.HH. base no comercial. "
            "La fuerza comercial forma parte del CAC y se informa en la sección de adquisición."
        ),
        (
            f"La planilla base del último año asciende a {_fmt_money(last_planilla)} "
            f"({_fmt_pct(last_pct)} de ingresos). En el horizonte suma {_fmt_money(total_planilla)}."
        ),
    ]
    return {"headline": f"RR.HH. base último año: {_fmt_money(last_planilla)}", "paragraphs": paragraphs}


def narrate_valuation(valuation_summary: list[tuple], wacc_base: float, dcf_params: dict[str, Any]) -> dict[str, Any]:
    if not valuation_summary:
        return {"headline": "Sin datos de valorización.", "paragraphs": []}
    values_by_method = {row[0]: row[-1] for row in valuation_summary}
    van = values_by_method.get("Valor Actual Neto (VAN)", values_by_method.get("VAN (suma flujos descontados)", float("nan")))

    paragraphs = [
        (
            f"El WACC anual estimado es {_fmt_pct(wacc_base)}. La valorización se basa en el método de "
            f"Flujos de Caja Descontados (DCF), proyectando los flujos netos del horizonte y sumando "
            f"el valor residual descontado."
        ),
        (
            f"El Valor Actual Neto (VAN) resultante asciende a {_fmt_money(van)}. "
            f"Esto representa el valor presente de la compañía neto de la inversión inicial, "
            f"utilizando la tasa de descuento base definida por el costo de capital de la industria."
        )
    ]
    return {"headline": f"Valorización DCF (VAN): {_fmt_money(van)}", "paragraphs": paragraphs}


def narrate_unit_economics(unit_economics: dict[str, float], annual_rows: list[tuple]) -> dict[str, Any]:
    if not unit_economics:
        return {"headline": "Sin datos de unit economics.", "paragraphs": []}
    arpu = _safe(unit_economics.get("ARPU", float("nan")))
    cac = _safe(unit_economics.get("CAC", float("nan")))
    ltv_cac = _safe(unit_economics.get("LTV/CAC", float("nan")))
    burn = _safe(unit_economics.get("Cash Burn Rate", float("nan")))
    bootstrap = _safe(unit_economics.get("Bootstrapping", float("nan")))
    gp = _safe(unit_economics.get("Gross Profit (GP)", float("nan")))
    arr = _safe(unit_economics.get("ARR", float("nan")))

    paragraphs = [
        (
            f"Indicadores clave: ARPU {_fmt_money(arpu)}, CAC {_fmt_money(cac)}, "
            f"Gross Profit {_fmt_pct(gp)}, ARR {_fmt_pct(arr)} y LTV/CAC {_fmt_number(ltv_cac, 1)}×."
        ),
        (
            f"El bootstrapping requerido es {_fmt_money(bootstrap)} con un cash burn rate de "
            f"{_fmt_money(burn)}/día. Marca el piso de capital de trabajo bajo el cual la operación se rompe."
        ),
    ]
    if annual_rows:
        last_year = annual_rows[-1]
        margin = last_year[4]
        cash_end = last_year[6]
        margin_band = _band(margin if margin == margin else 0.0, [(0.0, "pérdida"), (0.10, "marginal"), (0.25, "adecuado")], "fuerte")
        paragraphs.append(
            f"Al cierre del último año, el margen EBITDA llega a {_fmt_pct(margin)} ({margin_band}) "
            f"con caja final de {_fmt_money(cash_end)}, validando que el plan converge en autosuficiencia."
        )
    if ltv_cac > 50:
        paragraphs.append(
            "El LTV/CAC excede 50× — probablemente refleja una sobre-estimación: el LTV usa churn anual "
            "convertido a mensual y un ticket promedio agregado. Conviene calcular un LTV por servicio "
            "antes de comunicarlo externamente."
        )
    return {"headline": f"Unit Economics: LTV/CAC {_fmt_number(ltv_cac, 1)}×", "paragraphs": paragraphs}


def narrate_sensitivity(
    wacc_rows: list[tuple],
    variable_rows: list[tuple],
    breakeven_rows: list[tuple],
) -> dict[str, Any]:
    paragraphs: list[str] = []
    if wacc_rows:
        all_values = [v for row in wacc_rows for v in row[1:] if isinstance(v, (int, float))]
        if all_values:
            paragraphs.append(
                f"La matriz WACC × múltiplo de EBITDA arroja valorizaciones entre "
                f"{_fmt_money(min(all_values))} y {_fmt_money(max(all_values))}, "
                f"mostrando cuán sensible es el resultado a la combinación tasa-múltiplo."
            )
    if variable_rows:
        sorted_effects = sorted(
            [r for r in variable_rows if isinstance(r[3], (int, float))],
            key=lambda r: abs(r[3]),
            reverse=True,
        )
        if sorted_effects:
            top = sorted_effects[0]
            paragraphs.append(
                f"La variable más sensible es **{top[0]}** con un efecto de {_fmt_pct(top[3])} "
                f"sobre el EBITDA. Es la palanca prioritaria a monitorear."
            )
    if breakeven_rows:
        items = []
        for row in breakeven_rows:
            variable, _current, _breakeven, variation = row
            if isinstance(variation, (int, float)):
                items.append(f"{variable} ({_fmt_pct(variation)})")
        if items:
            paragraphs.append(
                "Las variaciones tolerables para mantener EBITDA ≥ 0 son: " + "; ".join(items) + "."
            )
    if not paragraphs:
        return {"headline": "Sin datos de sensibilidad.", "paragraphs": []}
    return {"headline": "Análisis de sensibilidad", "paragraphs": paragraphs}


def narrate_executive_summary(
    summary: dict[str, Any],
    unit_economics: dict[str, float],
    wacc_base: float,
) -> dict[str, Any]:
    revenue = _safe(summary.get("total_revenue"))
    ebitda = _safe(summary.get("total_ebitda"))
    final_cash = _safe(summary.get("final_cash"))
    min_cash = _safe(summary.get("minimum_cash"))
    last_year_ebitda = _safe(summary.get("last_year_ebitda"))
    last_year_revenue = _safe(summary.get("last_year_revenue"))
    margin = (last_year_ebitda / last_year_revenue) if last_year_revenue else float("nan")
    margin_band = _band(margin if margin == margin else 0.0, [(0.0, "deficitario"), (0.10, "marginal"), (0.25, "adecuado")], "fuerte")
    ltv_cac = _safe(unit_economics.get("LTV/CAC", float("nan")))
    paragraphs = [
        (
            f"El plan acumula ingresos por {_fmt_money(revenue)} y EBITDA por {_fmt_money(ebitda)} "
            f"a lo largo del horizonte modelado, cerrando con caja de {_fmt_money(final_cash)} "
            f"(mínima histórica {_fmt_money(min_cash)})."
        ),
        (
            f"El último año entrega un EBITDA de {_fmt_money(last_year_ebitda)} sobre "
            f"{_fmt_money(last_year_revenue)} de ingresos, equivalente a un margen {_fmt_pct(margin)} ({margin_band}). "
            f"El WACC aplicado es {_fmt_pct(wacc_base)} y el LTV/CAC {_fmt_number(ltv_cac, 1)}×."
        ),
    ]
    return {"headline": "Resumen ejecutivo", "paragraphs": paragraphs}


def build_all_narratives(
    summary: dict[str, Any],
    tables: dict[str, Any],
    document: dict[str, Any],
) -> dict[str, Any]:
    unit_economics = summary.get("unit_economics", {})
    wacc_base = float(tables.get("wacc_base", 0.0))
    dcf_params = document.get("dcf", {})

    return {
        "executive": narrate_executive_summary(summary, unit_economics, wacc_base),
        "clientes": narrate_clients(tables["clientes"]["summary"]["rows"], unit_economics),
        "servicios": narrate_services(tables["servicios"]["summary"]["rows"], tables["servicios"].get("services", []), unit_economics),
        "ingresos": narrate_revenue(tables["ingresos"]["summary"]["rows"], len(tables["ingresos"].get("services", []))),
        "cac": narrate_cac(tables["cac"]["summary"]["rows"], unit_economics),
        "costos_operacionales": narrate_op_costs(tables["costos_operacionales"]["summary"]["rows"], unit_economics),
        "administracion": narrate_admin(tables["administracion"]["summary"]["rows"]),
        "rrhh": narrate_hr(tables["rrhh"]["summary"]["rows"]),
        "valorizacion": narrate_valuation(tables["valorizacion"]["summary"]["rows"], wacc_base, dcf_params),
        "unit_economics": narrate_unit_economics(unit_economics, tables["unit_economics"]["annual"]["rows"]),
        "sensibilidad": narrate_sensitivity(
            tables["sensibilidad"]["wacc"]["rows"],
            tables["sensibilidad"]["variables"]["rows"],
            tables["sensibilidad"]["breakeven"]["rows"],
        ),
    }

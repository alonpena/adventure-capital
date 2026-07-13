"""Due Diligence — verdict, findings y palancas recomendadas.

Muestra el esquema completo de veredicto con campos de decisión:
``valuation_mode``, ``adjustment_level``, ``blocking_reasons``, ``rerun_recommended``.
"""

from __future__ import annotations

from streamlit_pages import components as C
from streamlit_pages.styles import ACCENT_CYAN  # noqa: F401


# --------------------------------------------------------------------------- #
# DD → M4 gate (movido desde el Gestor: auditoría UX P0-3)
# --------------------------------------------------------------------------- #


def _run_m4(st, run_id: str) -> None:
    """Run the stochastic analysis (M4) on an existing execution."""
    from adventure_capital.workflow_registry import run_stochastic_only

    with st.spinner("Ejecutando análisis de robustez (M4)…"):
        try:
            run_stochastic_only(run_id)
            st.session_state["current_run_id"] = run_id
            st.session_state["m4_gate_run_id"] = None
            st.success(
                "Análisis de robustez completado. Revisa la página Análisis de robustez."
            )
        except Exception as exc:
            st.error(f"El análisis de robustez falló: {exc}. El plan determinista sigue disponible.")
            import traceback
            with st.expander("Detalle técnico"):
                st.code(traceback.format_exc())


def _render_m4_gate(st, run_id: str) -> None:
    """Gate the stochastic stage (M4) after phase 1, in the run's own context.

    - Blocking verdict → no M4, show reasons.
    - Warning / minor verdict → require explicit confirmation to run M4.
    - Clean pass → run M4 automatically.
    """
    from adventure_capital.workflow_registry import _CONFIRM_VERDICTS

    if st.session_state.get("m4_gate_run_id") != run_id:
        return

    dd = C.canonical_json(run_id, "due_diligence_report.json") or {}
    verdict = dd.get("verdict", "—")
    allows = dd.get("allows_stochastic")

    # Blocking verdict — M4 not allowed.
    if not allows:
        st.error("El veredicto bloquea el análisis de robustez. "
                 "Recalibra la instancia según las razones de abajo y vuelve a ejecutar.")
        for reason in dd.get("blocking_reasons", []):
            st.markdown(f"- {reason}")
        if st.button("Entendido", key="m4_gate_close_blocked"):
            st.session_state["m4_gate_run_id"] = None
            st.rerun()
        st.markdown("---")
        return

    # Warning / minor adjustment — require explicit confirmation.
    if verdict in _CONFIRM_VERDICTS:
        st.warning("Due diligence aprobó con advertencias. Decide si continuar con el análisis "
                   "de robustez (M4/LHS) o quedarte con el plan determinista oficial.")
        for rec in dd.get("adjustment_recommendations", []):
            msg = rec.get("recommendation") if isinstance(rec, dict) else rec
            st.markdown(f"- {msg}")
        c1, c2 = st.columns(2)
        if c1.button("Continuar con análisis de robustez", type="primary", key="m4_gate_confirm"):
            _run_m4(st, run_id)
            st.rerun()
        if c2.button("Mantener solo plan determinista", key="m4_gate_skip"):
            st.session_state["m4_gate_run_id"] = None
            st.rerun()
        st.markdown("---")
        return

    # Clean pass — run M4 automatically.
    _run_m4(st, run_id)
    st.rerun()


# Etiquetas de negocio para hallazgos técnicos (ver src/adventure_capital/
# due_diligence/rules.py y calibration/checks.py para los nombres canónicos).
FINDING_LABELS: dict[str, str] = {
    "instance_valid": "Configuración de la instancia",
    "unit_margin_positive": "Margen unitario por servicio",
    "financing_present": "Financiamiento inicial",
    "churn_valid": "Rango de churn",
    "churn_severity": "Severidad del churn",
    "breakeven_within_horizon": "Punto de equilibrio",
    "ebitda_regime_by_year3": "Régimen de EBITDA al año 3",
    "revenue_growth": "Crecimiento de ingresos",
    "exit_roi": "ROI de salida",
    "growth_commitment_plan_inconsistent": "Consistencia del plan de crecimiento",
    "growth_commitment_plan_mom_suspicious": "Crecimiento mes a mes del plan",
    "growth_commitment_plan_below_thesis": "Plan de crecimiento vs. tesis",
    "growth_commitment_custom_unjustified": "Justificación del plan personalizado",
    "growth_commitment_infeasible": "Factibilidad del compromiso de crecimiento",
    "conservative_plan_diagnostic": "Diagnóstico de plan conservador",
    "runway": "Runway de caja",
    "funding_gap_severity": "Severidad de la brecha de financiamiento",
    "synthesis_unavailable": "Síntesis de due diligence",
    "seller_capacity_saturation": "Saturación de capacidad comercial",
    "sellers_no_growth_with_saturation": "Dotación de vendedores",
    "ltv_cac": "Ratio LTV/CAC",
}

# Palancas conocidas (ver recommended_levers.json / due_diligence workflow).
LEVER_LABELS: dict[str, str] = {
    "churn_anual": "Churn anual",
    "A_base | acquisition ceiling slack": "Techo de adquisición (holgura de A_base)",
    "meta | commission rates": "Tasa de comisión (meta)",
}

IMPACT_AREA_LABELS: dict[str, str] = {
    "retention": "retención",
    "growth": "crecimiento",
    "acquisition_cost": "costo de adquisición",
    "unmapped": "sin mapear",
}

DIRECTION_LABELS: dict[str, str] = {
    "increase": "subir",
    "decrease": "bajar",
    "adjust": "ajustar",
}


def _humanize_finding_name(name: str) -> str:
    """Turn a machine finding name into a Spanish business label.

    Known ids (``FINDING_LABELS``) map to business-facing text; unknown ones
    fall back to underscore→space + capitalize.
    """
    if not name:
        return "—"
    return FINDING_LABELS.get(name, name.replace("_", " ").strip().capitalize())


def _fmt_lever_value(value) -> str:
    """Format a lever's current value without over-precision on large numbers."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    decimals = 0 if abs(v) >= 1000 else 2
    return C.number(v, decimals)


def render(st) -> None:
    run_id = C.require_execution(st)
    if run_id is None:
        st.title("Due diligence")
        return

    C.page_header(
        st,
        "Due diligence",
        "Evaluación estructurada del caso — veredicto, hallazgos y palancas.",
        run_id=run_id,
    )

    # ── DD → M4 gate (el veredicto se decide aquí, en el contexto del run) ──
    _render_m4_gate(st, run_id)

    # ── Load data ────────────────────────────────────────────────
    dd_report = C.canonical_json(run_id, "due_diligence_report.json")
    assessment = C.canonical_json(run_id, "assessment_summary.json")
    pp_assessment = C.postprocessed_json(run_id, "due_diligence", "due_diligence_assessment.json")

    # Merge sources: canonical DD report > assessment_summary > postprocessed
    assessment_data = dd_report or assessment or pp_assessment or {}
    if not assessment_data:
        st.warning("Este caso no tiene due diligence. Ejecuta el caso desde el Gestor de instancias "
                   "para generar el veredicto.")
        return

    # ── Verdict header ───────────────────────────────────────────
    verdict = assessment_data.get("verdict", "—")
    allows_stochastic = assessment_data.get("allows_stochastic")
    valuation_mode = assessment_data.get("valuation_mode", "—")
    adjustment_level = assessment_data.get("adjustment_level", "—")
    rerun_recommended = assessment_data.get("rerun_recommended")

    st.markdown("### Veredicto")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tone = C.VERDICT_TONE.get(verdict, "muted")
        C.badge(st, C.VERDICT_LABELS.get(verdict, verdict), tone)
        st.caption(f"Veredicto (`{verdict}`)")

    with c2:
        tone = "ok" if allows_stochastic else "bad"
        C.badge(st, "Sí" if allows_stochastic else "No", tone)
        st.caption("Permite análisis de robustez")

    with c3:
        tone_map = {"final": "ok", "warning": "warn", "diagnostic": "warn", "none": "muted"}
        C.badge(st, C.VALUATION_MODE_LABELS.get(valuation_mode, valuation_mode or "—"),
                tone_map.get(valuation_mode, "muted"))
        st.caption("Modo de valoración")

    with c4:
        if rerun_recommended:
            C.badge(st, "Recomienda recalibrar", "warn")
        else:
            C.badge(st, "Aceptado", "ok")
        st.caption("¿Recalibrar?")

    # ── Adjustment level ─────────────────────────────────────────
    if adjustment_level and adjustment_level != "none":
        st.markdown("##### Nivel de ajuste")
        tone_map = {"minor": "warn", "major": "bad", "structural": "bad"}
        C.badge(st, adjustment_level.replace("_", " ").title(),
                tone_map.get(adjustment_level, "muted"))

    # ── Blocking reasons ─────────────────────────────────────────
    blocking = assessment_data.get("blocking_reasons", [])
    if blocking:
        st.markdown("##### Razones de bloqueo")
        for reason in blocking:
            st.markdown(f"- {reason}")

    # ── Recommendations ─────────────────────────────────────────
    recommendations = assessment_data.get("adjustment_recommendations", [])
    if recommendations:
        st.markdown("##### Recomendaciones de ajuste")
        for rec in recommendations:
            if isinstance(rec, dict):
                msg = rec.get("recommendation") or rec.get("message") or rec.get("reason") or str(rec)
                st.markdown(f"- {msg}")
            else:
                st.markdown(f"- {rec}")

    C.source_caption(st, "M3_DUE_DILIGENCE", "due_diligence_report.json", "assessment_summary.json")

    # ── Findings ─────────────────────────────────────────────────
    findings = assessment_data.get("findings", [])
    if findings:
        st.markdown("### Hallazgos")

        passed = [f for f in findings if f.get("passed", True)]
        failing = [f for f in findings if not f.get("passed", True)]
        st.caption(
            f"{len(passed)} de {len(findings)} verificaciones pasaron"
            + (f" · {len(failing)} requieren atención." if failing else ".")
        )

        # Attention first: what failed, why, and what to do about it.
        for f in failing:
            name = _humanize_finding_name(f.get("name", f.get("id", "")))
            msg = f.get("message", "")
            sev = f.get("severity_class", "—")
            with st.expander(f"{name} — requiere atención", expanded=True):
                C.badge(st, sev.capitalize() if isinstance(sev, str) else "Advertencia",
                        C.SEVERITY_TONE.get(sev, "warn"))
                st.markdown(msg)
                if f.get("recommendation"):
                    st.markdown(f"**Qué hacer:** {f.get('recommendation')}")

                evidence = f.get("evidence", {})
                ident = f.get("id", "")
                with st.expander("Detalle técnico / Evidencia", expanded=False):
                    st.markdown(f"**ID:** `{ident}`")
                    st.markdown(f"**Severidad:** `{sev}`")
                    if evidence:
                        st.json(evidence)

        # Then the checklist of what passed, tucked away — it's not the story.
        if passed:
            with st.expander(f"Verificaciones aprobadas ({len(passed)})", expanded=False):
                for f in passed:
                    name = _humanize_finding_name(f.get("name", f.get("id", "")))
                    message = f.get("message") or "Sin observaciones."
                    st.markdown(f"**{name}** — {message}")

        # Raw flag table stays available, but out of the way.
        flags = C.postprocessed_csv(run_id, "due_diligence", "due_diligence_flags.csv")
        if flags is not None:
            with st.expander("Detalle técnico (tabla de flags)"):
                st.dataframe(flags, use_container_width=True, hide_index=True)

    # ── Calibration verdict ─────────────────────────────────────
    cal_verdict = assessment_data.get("calibration_verdict")
    if cal_verdict:
        st.markdown("### Calibración")
        tone = "ok" if cal_verdict == "PASS" else ("warn" if cal_verdict == "WARN" else "bad")
        C.badge(st, f"Calibración: {cal_verdict}", tone)

    # ── Liquidity diagnostic ────────────────────────────────────
    liquidity = assessment_data.get("liquidity_diagnostic", {})
    if liquidity:
        st.markdown("### Diagnóstico de liquidez")
        l1, l2, l3 = st.columns(3)
        with l1:
            C.kpi(st, "Caja mínima", C.money(liquidity.get("min_cash")),
                  tone="alert" if (liquidity.get("min_cash") or 0) < 0 else "")
        with l2:
            C.kpi(st, "Mes de caja mínima",
                  f"Mes {liquidity['min_cash_month']}" if liquidity.get("min_cash_month") else "—")
        with l3:
            C.kpi(st, "Brecha de financiamiento",
                  C.money(liquidity.get("financing_gap_usd", liquidity.get("max_funding_gap", 0))),
                  tone="alert" if (liquidity.get("financing_gap_usd", 0) or 0) > 0 else "")

        if liquidity.get("breakeven_month"):
            C.kpi(st, "Mes de breakeven", f"Mes {liquidity['breakeven_month']}",
                  tone="success")

    # ── Levers ───────────────────────────────────────────────────
    levers = C.postprocessed_json(run_id, "due_diligence", "recommended_levers.json")
    if levers:
        lever_list = levers.get("levers", [])
        if lever_list:
            st.markdown("### Palancas recomendadas")
            for lever in lever_list:
                finding_id = lever.get("finding_id", "")
                lever_key = lever.get("lever")
                direction = lever.get("suggested_direction")
                area = lever.get("impact_area")
                current = lever.get("current_value")

                area_label = IMPACT_AREA_LABELS.get(area, area or "—")

                if not lever_key:
                    st.markdown(
                        f"- **Sin palanca mapeada** ({area_label}): requiere revisión manual "
                        f"(hallazgo `{finding_id}`)."
                    )
                    continue

                lever_label = LEVER_LABELS.get(lever_key, lever_key)
                direction_label = DIRECTION_LABELS.get(direction, direction or "ajustar")
                value_part = (
                    f" Valor actual: {_fmt_lever_value(current)}." if current is not None else ""
                )
                st.markdown(
                    f"- **{lever_label}** ({area_label}): mover al {direction_label}."
                    f"{value_part}"
                )

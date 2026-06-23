"""Due Diligence — verdict, findings y palancas recomendadas.

Muestra el esquema completo de veredicto con campos de decisión:
``valuation_mode``, ``adjustment_level``, ``blocking_reasons``, ``rerun_recommended``.
"""

from __future__ import annotations

from streamlit_pages import components as C
from streamlit_pages.styles import ACCENT_CYAN


def render(st) -> None:
    st.title("Due Diligence")
    st.caption("Evaluación estructurada del caso — veredicto, hallazgos y palancas.")

    run_id = C.require_execution(st)
    if run_id is None:
        return

    # ── Load data ────────────────────────────────────────────────
    dd_report = C.canonical_json(run_id, "due_diligence_report.json")
    assessment = C.canonical_json(run_id, "assessment_summary.json")
    pp_assessment = C.postprocessed_json(run_id, "due_diligence", "due_diligence_assessment.json")

    # Merge sources: canonical DD report > assessment_summary > postprocessed
    assessment_data = dd_report or assessment or pp_assessment or {}
    if not assessment_data:
        st.warning("No se ejecutó Due Diligence para este caso. "
                   "Asegúrate de ejecutar el análisis completo desde el Gestor de Instancias.")
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
        C.badge(st, verdict, tone)
        st.caption("Veredicto")

    with c2:
        tone = "ok" if allows_stochastic else "bad"
        C.badge(st, "Sí" if allows_stochastic else "No", tone)
        st.caption("Permite análisis estocástico")

    with c3:
        tone_map = {"final": "ok", "warning": "warn", "diagnostic": "warn", "none": "muted"}
        C.badge(st, valuation_mode.capitalize() if valuation_mode else "—",
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
            st.markdown(f"- ⛔ {reason}")

    # ── Recommendations ─────────────────────────────────────────
    recommendations = assessment_data.get("adjustment_recommendations", [])
    if recommendations:
        st.markdown("##### Recomendaciones de ajuste")
        for rec in recommendations:
            st.markdown(f"- 💡 {rec}")

    # ── Findings ─────────────────────────────────────────────────
    findings = assessment_data.get("findings", [])
    if findings:
        st.markdown("### Hallazgos")

        # Count by severity
        by_severity = {}
        for f in findings:
            sev = f.get("severity_class", "unknown")
            by_severity[sev] = by_severity.get(sev, 0) + 1

        cols = st.columns(len(by_severity) if by_severity else 1)
        for i, (sev, count) in enumerate(sorted(by_severity.items())):
            tone = C.SEVERITY_TONE.get(sev, "muted")
            with cols[i % len(cols)]:
                C.badge(st, f"{sev}: {count}", tone)

        # Flag table
        flags = C.postprocessed_csv(run_id, "due_diligence", "due_diligence_flags.csv")
        if flags is not None:
            st.dataframe(flags, use_container_width=True, hide_index=True)

        # Failing findings detail
        failing = [f for f in findings if not f.get("passed", True)]
        if failing:
            st.markdown("#### Hallazgos con alerta")
            for f in failing:
                with st.expander(f"[{f.get('id')}] {f.get('name')}"):
                    tone = C.SEVERITY_TONE.get(f.get("severity_class"), "muted")
                    C.badge(st, f.get("severity_class", "—"), tone)
                    st.write(f.get("message", ""))
                    if f.get("recommendation"):
                        st.write(f"**Recomendación:** {f.get('recommendation')}")
                    evidence = f.get("evidence", {})
                    if evidence:
                        st.write("**Evidencia:**", evidence)

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
                st.markdown(
                    f"- **{lever.get('finding_id')}** → palanca: `{lever.get('lever')}` · "
                    f"dirección: *{lever.get('suggested_direction')}* · "
                    f"área: {lever.get('impact_area')}"
                    + (f" · valor actual: {lever.get('current_value')}" if lever.get("current_value") is not None else "")
                )

"""Due Diligence — reads postprocessed_results/due_diligence/."""

from __future__ import annotations

from streamlit_pages import components as C

_VERDICT_TONE = {
    "passed": "ok",
    "passed_with_warnings": "warn",
    "requires_minor_adjustment": "warn",
    "requires_major_adjustment": "bad",
    "rejected_for_stochastic": "bad",
}

_SEVERITY_TONE = {"ok": "ok", "warning": "warn", "minor": "warn", "major": "bad", "structural": "bad"}


def render(st) -> None:
    st.title("Due Diligence")
    root = C.require_run(st)
    if root is None:
        return
    folder = root / "due_diligence"
    assessment = C.read_json(folder / "due_diligence_assessment.json")
    if assessment is None:
        st.warning("No se ejecutó Due Diligence para este caso (corre el análisis completo en Configuración).")
        return

    verdict = assessment.get("verdict", "—")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Veredicto**")
        C.badge(st, verdict, _VERDICT_TONE.get(verdict, "muted"))
    with c2:
        C.kpi(st, "Permite estocástico", "Sí" if assessment.get("allows_stochastic") else "No",
              tone="success" if assessment.get("allows_stochastic") else "alert")
    with c3:
        C.kpi(st, "Modo de valoración", str(assessment.get("valuation_mode", "—")))

    findings = assessment.get("findings", [])
    failing = [f for f in findings if not f.get("passed", True)]
    st.subheader(f"Hallazgos ({len(findings)} — {len(failing)} con alerta)")

    flags = C.read_csv(folder / "due_diligence_flags.csv")
    if flags is not None:
        st.dataframe(flags, use_container_width=True, hide_index=True)

    if failing:
        st.subheader("Hallazgos con alerta")
        for f in failing:
            with st.expander(f"[{f.get('id')}] {f.get('name')}"):
                C.badge(st, f.get("severity_class", "—"), _SEVERITY_TONE.get(f.get("severity_class"), "muted"))
                st.write(f.get("message", ""))

    st.subheader("Palancas recomendadas")
    levers = C.read_json(folder / "recommended_levers.json") or {}
    lever_list = levers.get("levers", [])
    if not lever_list:
        C.note(st, "Sin palancas pendientes: no hay hallazgos accionables.")
    for lever in lever_list:
        st.markdown(
            f"- **{lever.get('finding_id')}** → palanca: `{lever.get('lever')}` · "
            f"dirección: *{lever.get('suggested_direction')}* · área: {lever.get('impact_area')}"
            + (f" · valor actual: {lever.get('current_value')}" if lever.get("current_value") is not None else "")
        )

"""Estocástico — reads postprocessed_results/stochastic_assessment/ if present.

Does not overclaim robust optimization: surfaces the recorded method status
(risk-neutral SAA + ex-post Monte Carlo) verbatim.
"""

from __future__ import annotations

import plotly.graph_objects as go

from streamlit_pages import components as C
from streamlit_pages.styles import ACCENT


def render(st) -> None:
    st.title("Análisis estocástico")
    root = C.require_run(st)
    if root is None:
        return
    folder = root / "stochastic_assessment"
    if not folder.exists():
        st.warning("No ejecutado / no disponible para este caso.")
        C.note(st, "El análisis estocástico requiere un veredicto de Due Diligence que lo permita y el modo de análisis completo.")
        return

    status = C.read_json(folder / "stochastic_method_status.json") or {}
    st.subheader("Estado del método")
    s1, s2, s3 = st.columns(3)
    with s1:
        C.kpi(st, "Método", str(status.get("method", "—")))
    with s2:
        C.kpi(st, "Objetivo", str(status.get("objective", "—")))
    with s3:
        C.kpi(st, "Optimización robusta", "No" if status.get("is_robust_optimization") is False else "—")
    C.note(st, status.get("note", ""))
    b1, b2, b3 = st.columns(3)
    with b1:
        C.badge(st, f"SAA: {'sí' if status.get('saa_implemented') else 'no'}", "ok" if status.get("saa_implemented") else "muted")
    with b2:
        C.badge(st, f"Monte Carlo ex-post: {'sí' if status.get('monte_carlo_ex_post_implemented') else 'no'}",
                "ok" if status.get("monte_carlo_ex_post_implemented") else "muted")
    with b3:
        C.badge(st, f"LHS: {'sí' if status.get('lhs_implemented') else 'no (solo especificado)'}",
                "ok" if status.get("lhs_implemented") else "warn")

    gaps = status.get("known_parity_gaps_vs_deterministic", [])
    if gaps:
        C.note(st, "Brechas de paridad con el modelo determinista: " + ", ".join(gaps) + ".")

    diag = (C.read_json(folder / "stochastic_diagnostics.json") or {}).get("summary", {})
    if diag:
        st.subheader("Diagnósticos de distribución")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            C.kpi(st, "Escenarios", C.number(diag.get("n_scenarios")))
        with d2:
            C.kpi(st, "VAN esperado", C.money(diag.get("expected_van")))
        with d3:
            C.kpi(st, "VAN P10", C.money(diag.get("van_p10")))
        with d4:
            C.kpi(st, "VAN P90", C.money(diag.get("van_p90")))
        d5, d6, d7 = st.columns(3)
        with d5:
            C.kpi(st, "Prob. VAN negativo", C.pct(diag.get("prob_van_negative")))
        with d6:
            C.kpi(st, "Prob. brecha de fondos", C.pct(diag.get("prob_funding_gap")),
                  tone="alert" if (diag.get("prob_funding_gap") or 0) > 0.5 else "")
        with d7:
            C.kpi(st, "Brecha de fondos esperada", C.money(diag.get("expected_funding_gap")))

    scenarios_path = folder / "stochastic_scenarios.csv"
    if scenarios_path.exists():
        scenarios = C.read_csv(scenarios_path)
        if scenarios is not None and "VAN" in scenarios.columns:
            st.subheader("Distribución de VAN (ex-post)")
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=scenarios["VAN"], marker_color=ACCENT, nbinsx=40))
            fig.update_layout(height=320, margin=dict(t=10), xaxis_title="VAN", yaxis_title="Escenarios", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("Escenarios (detalle)"):
            st.dataframe(scenarios, use_container_width=True, hide_index=True)

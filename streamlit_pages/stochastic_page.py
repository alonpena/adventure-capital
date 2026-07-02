"""Análisis de Escenarios — M4 con vocabulario de producto, no académico.

Superficie: escenarios generados, distribución de VAN, probabilidades, brecha
de financiamiento. Los términos técnicos (CVaR, SAA, LHS) se dejan en tooltips
y metadata, no como etiquetas principales.
"""

from __future__ import annotations

import plotly.graph_objects as go

from streamlit_pages import components as C
from streamlit_pages.styles import ACCENT, ACCENT_CYAN, ALERT, SUCCESS, TEXT_SECONDARY


def _load_diagnostics(run_id: str) -> dict | None:
    """Load stochastic diagnostics: flat canonical first, postprocessed fallback.

    The flat canonical file is ``stochastic_diagnostics.json`` at the execution
    root (see ADR 0007/0008). Older runs may keep it under
    ``postprocessed_results/stochastic_assessment/``.
    """
    return (
        C.canonical_json(run_id, "stochastic_diagnostics.json")
        or C.postprocessed_json(run_id, "stochastic_assessment", "stochastic_diagnostics.json")
    )


def _load_scenarios(run_id: str):
    # NB: cannot use ``a or b`` — DataFrame truthiness is ambiguous.
    df = C.canonical_csv(run_id, "stochastic_scenarios.csv")
    if df is None:
        df = C.postprocessed_csv(run_id, "stochastic_assessment", "stochastic_scenarios.csv")
    return df


def render(st) -> None:
    st.title("Análisis de Escenarios")
    st.caption("Distribución de resultados bajo incertidumbre — escenarios generados, probabilidades y brechas.")

    run_id = C.require_execution(st)
    if run_id is None:
        return

    # ── Load data (flat canonical first, postprocessed fallback) ─────
    exe = C.get_execution(run_id) or {}
    m4_state = exe.get("stages", {}).get("M4_STOCHASTIC", "—")
    assessment = C.canonical_json(run_id, "assessment_summary.json") or {}
    diagnostics = _load_diagnostics(run_id)
    scenarios_df = _load_scenarios(run_id)

    # ── Not run / blocked ────────────────────────────────────────
    if diagnostics is None and scenarios_df is None:
        if assessment.get("allows_stochastic") is False or m4_state == "blocked":
            st.info("Análisis de escenarios bloqueado por el veredicto de Due Diligence.")
            for reason in assessment.get("blocking_reasons", []):
                st.markdown(f"- ⛔ {reason}")
            C.note(st, f"Modo de valoración: **{assessment.get('valuation_mode', 'none')}**. "
                       "Revisa la página de Due Diligence para entender el bloqueo.")
        else:
            st.warning("No se ejecutó el análisis de escenarios para este caso. "
                       "Ejecútalo desde el Gestor de Instancias.")
        return

    # ── Method status (derived from diagnostics metadata) ────────
    st.markdown("### Estado del análisis")
    m1, m2 = st.columns(2)
    with m1:
        method = str((diagnostics or {}).get("evaluation", "—")).replace("_", " ").title()
        C.kpi(st, "Método de escenarios", method)
    with m2:
        obj = (diagnostics or {}).get("objective")
        obj_label = {"cvar_van": "Valor en riesgo (CVaR)"}.get(obj, str(obj or "—"))
        C.kpi(st, "Objetivo", obj_label)

    # ── Distribution diagnostics ─────────────────────────────────
    diag_summary = (diagnostics or {}).get("summary", {})
    if not diag_summary:
        # Fallback: single-row stochastic_summary.csv carries the same fields.
        summary_df = C.canonical_csv(run_id, "stochastic_summary.csv")
        if summary_df is not None and not summary_df.empty:
            diag_summary = summary_df.iloc[0].to_dict()
    if diag_summary:
        st.markdown("### Distribución de resultados")

        # KPI row
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            C.kpi(st, "Escenarios generados", C.number(diag_summary.get("n_scenarios")))
        with d2:
            van_expected = diag_summary.get("expected_van", diag_summary.get("VAN"))
            C.kpi(st, "VAN esperado (promedio)", C.money(van_expected),
                  tone="success" if (van_expected or 0) >= 0 else "alert")
        with d3:
            van_p10 = diag_summary.get("van_p10")
            C.kpi(st, "VAN pesimista (P10)", C.money(van_p10),
                  tone="alert" if (van_p10 or 0) < 0 else "")
        with d4:
            van_p90 = diag_summary.get("van_p90")
            C.kpi(st, "VAN optimista (P90)", C.money(van_p90),
                  tone="success" if (van_p90 or 0) > 0 else "")

        # Risk metrics
        st.markdown("#### Riesgos y probabilidades")
        r1, r2, r3 = st.columns(3)
        with r1:
            prob_neg = diag_summary.get("prob_van_negative", 0)
            C.kpi(st, "Probabilidad de VAN negativo", C.pct(prob_neg),
                  tone="alert" if (prob_neg or 0) > 0.3 else "warn" if (prob_neg or 0) > 0.1 else "")
        with r2:
            prob_cash = diag_summary.get("prob_cash_below_floor", 0)
            C.kpi(st, "Prob. caja bajo mínimo", C.pct(prob_cash),
                  tone="alert" if (prob_cash or 0) > 0.5 else "")
        with r3:
            gap = diag_summary.get("expected_funding_gap", 0)
            C.kpi(st, "Brecha de financiamiento esperada", C.money(gap),
                  tone="alert" if (gap or 0) > 0 else "")

        # Additional metrics
        r4, r5, r6 = st.columns(3)
        with r4:
            C.kpi(st, "VAN P50 (mediana)", C.money(diag_summary.get("van_p50")))
        with r5:
            cvar = diag_summary.get("cvar_5", diag_summary.get("cvar"))
            C.kpi(st, "Valor en riesgo (CVaR 5%)", C.money(cvar),
                  tone="alert" if (cvar or 0) < 0 else "")
        with r6:
            C.kpi(st, "Clientes activos final (P50)",
                  C.number(diag_summary.get("final_active_clients_p50")))

    # ── Histogram ────────────────────────────────────────────────
    if scenarios_df is not None and "VAN" in scenarios_df.columns:
        st.markdown("### Distribución de VAN entre escenarios")
        fig = go.Figure()

        # Add mean line
        van_mean = scenarios_df["VAN"].mean()
        van_p10 = scenarios_df["VAN"].quantile(0.10)
        van_p90 = scenarios_df["VAN"].quantile(0.90)

        fig.add_trace(go.Histogram(
            x=scenarios_df["VAN"],
            marker_color=ACCENT,
            nbinsx=40,
            name="VAN",
            hovertemplate="VAN: USD %{x:,.0f}<br>Frecuencia: %{y}<extra></extra>",
        ))
        fig.add_vline(x=0, line_color=ALERT, line_width=2, annotation_text="VAN = 0")
        fig.add_vline(x=van_mean, line_color=SUCCESS, line_dash="dash",
                      annotation_text=f"Media: USD {van_mean:,.0f}")
        fig.add_vline(x=van_p10, line_color=ACCENT_CYAN, line_dash="dot",
                      annotation_text=f"P10: USD {van_p10:,.0f}")
        fig.add_vline(x=van_p90, line_color=ACCENT_CYAN, line_dash="dot",
                      annotation_text=f"P90: USD {van_p90:,.0f}")

        fig.update_layout(
            height=380,
            margin=dict(t=10),
            xaxis_title="VAN (USD)",
            yaxis_title="N° de escenarios",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_SECONDARY),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Scenarios table ──────────────────────────────────────────
    if scenarios_df is not None:
        with st.expander("Escenarios generados (detalle)"):
            st.dataframe(scenarios_df, use_container_width=True, hide_index=True)

    # ── Management summary note ──────────────────────────────────
    val_mode = assessment.get("valuation_mode")
    if val_mode:
        st.markdown("### Resumen para gestión")
        mode_descriptions = {
            "final": "Resultado listo para decisión de inversión.",
            "warning": "Resultado preliminar — requiere atención en los hallazgos de Due Diligence.",
            "diagnostic": "Resultado no listo para inversión — se necesitan recalibraciones significativas.",
            "none": "No se generó análisis de escenarios.",
        }
        desc = mode_descriptions.get(val_mode, "")
        if desc:
            C.note(st, f"**Modo de valoración:** {val_mode}. {desc}")

"""Análisis de robustez (LHS) — M4 con vocabulario de producto, no académico.

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
    run_id = C.require_execution(st)
    if run_id is None:
        st.title("Análisis de robustez (LHS)")
        return

    C.page_header(
        st,
        "Análisis de robustez (LHS)",
        "Distribución de resultados bajo incertidumbre — escenarios generados, probabilidades y brechas.",
        run_id=run_id,
    )

    # ── Load data (flat canonical first, postprocessed fallback) ─────
    exe = C.get_execution(run_id) or {}
    m4_state = exe.get("stages", {}).get("M4_STOCHASTIC", "—")
    assessment = C.canonical_json(run_id, "assessment_summary.json") or {}
    diagnostics = _load_diagnostics(run_id)
    scenarios_df = _load_scenarios(run_id)

    # ── Not run / blocked ────────────────────────────────────────
    if diagnostics is None and scenarios_df is None:
        if assessment.get("allows_stochastic") is False or m4_state == "blocked":
            st.info("El veredicto de due diligence bloquea el análisis de escenarios.")
            for reason in assessment.get("blocking_reasons", []):
                st.markdown(f"- {reason}")
            mode = assessment.get("valuation_mode", "none")
            C.note(st, f"Modo de valoración: **{C.VALUATION_MODE_LABELS.get(mode, mode)}**. "
                       "Revisa la página Due diligence para entender el bloqueo.")
        else:
            st.warning("Este caso no tiene análisis de escenarios. "
                       "Confírmalo desde la página Due diligence tras ejecutar el caso.")
        return

    # ── Scenario Headline: central outcomes first ────────────────
    diag_summary = (diagnostics or {}).get("summary", {})
    if not diag_summary:
        # Fallback: single-row stochastic_summary.csv carries the same fields.
        summary_df = C.canonical_csv(run_id, "stochastic_summary.csv")
        if summary_df is not None and not summary_df.empty:
            diag_summary = summary_df.iloc[0].to_dict()
    if diag_summary:
        n_scen = C.number(diag_summary.get("n_scenarios"))
        h1, h2, h3 = st.columns([2, 2, 1])
        with h1:
            van_expected = diag_summary.get("expected_van", diag_summary.get("VAN"))
            C.kpi(st, "VAN esperado (promedio)", C.money(van_expected),
                  sub=f"sobre {n_scen} escenarios",
                  tone="hero success" if (van_expected or 0) >= 0 else "hero alert")
        with h2:
            C.kpi(st, "VAN mediana (P50)", C.money(diag_summary.get("van_p50")),
                  sub="la mitad de los escenarios supera este valor", tone="hero")
        with h3:
            van_p90 = diag_summary.get("van_p90")
            C.kpi(st, "Optimista (P90)", C.money(van_p90),
                  tone="success" if (van_p90 or 0) > 0 else "")
            C.kpi(st, "Clientes activos final (P50)",
                  C.number(diag_summary.get("final_active_clients_p50")))

        # ── Risk Band: grouped downside summary ──────────────────
        cvar = diag_summary.get("cvar_5", diag_summary.get("cvar"))
        prob_neg = diag_summary.get("prob_van_negative", 0)
        prob_cash = diag_summary.get("prob_cash_below_floor", 0)
        gap = diag_summary.get("expected_funding_gap", 0)
        C.risk_band(
            st,
            "Banda de riesgo — cola 5% de escenarios",
            [
                ("Valor en riesgo (CVaR 5%)", C.money(cvar), "VAN promedio del peor 5%"),
                ("VAN pesimista (P10)", C.money(diag_summary.get("van_p10")), ""),
                ("Prob. VAN negativo", C.pct(prob_neg), ""),
                ("Prob. caja bajo mínimo", C.pct(prob_cash), ""),
                ("Brecha de financiamiento esperada", C.money(gap), ""),
            ],
        )

        # Method metadata — footnote, not headline (vocabulario de producto).
        raw_method = str((diagnostics or {}).get("evaluation", "—"))
        method = {"ex_post_lhs": "ex post (muestreo LHS)"}.get(raw_method, raw_method.replace("_", " "))
        obj = (diagnostics or {}).get("objective")
        obj_label = {"cvar_van": "downside (CVaR 5% sobre VAN)"}.get(obj, str(obj or "—"))
        st.caption(f"Método: {method} · Objetivo de optimización: {obj_label} · "
                   f"{n_scen} escenarios generados")
        C.source_caption(st, "M4_STOCHASTIC", "stochastic_diagnostics.json", "stochastic_summary.csv")

    # ── Histogram ────────────────────────────────────────────────
    if scenarios_df is not None and "VAN" in scenarios_df.columns:
        st.markdown("### Distribución de VAN entre escenarios")
        fig = go.Figure()

        van_mean = scenarios_df["VAN"].mean()
        van_p50 = scenarios_df["VAN"].quantile(0.50)
        van_p90 = scenarios_df["VAN"].quantile(0.90)
        van_var5 = scenarios_df["VAN"].quantile(0.05)
        van_min = scenarios_df["VAN"].min()

        # Shade the 5% tail — the Risk Band (CVaR) region, visually anchored.
        if van_var5 > van_min:
            fig.add_vrect(
                x0=van_min, x1=van_var5,
                fillcolor=ALERT, opacity=0.15, line_width=0,
                annotation_text="cola 5% (CVaR)", annotation_position="top left",
                annotation_font_color=ALERT,
            )

        fig.add_trace(go.Histogram(
            x=scenarios_df["VAN"],
            marker_color=ACCENT,
            nbinsx=40,
            name="VAN",
            hovertemplate="VAN: USD %{x:,.0f}<br>Frecuencia: %{y}<extra></extra>",
        ))
        fig.add_vline(x=0, line_color=ALERT, line_width=2, annotation_text="VAN = 0")
        fig.add_vline(x=van_p50, line_color=ACCENT_CYAN, line_width=2,
                      annotation_text=f"P50: USD {van_p50:,.0f}",
                      annotation_position="top left")
        fig.add_vline(x=van_mean, line_color=SUCCESS, line_dash="dash",
                      annotation_text=f"Media: USD {van_mean:,.0f}",
                      annotation_position="bottom right")
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

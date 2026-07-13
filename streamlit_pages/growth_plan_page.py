"""Plan de Crecimiento — interactive exploration.

Shows Consensuated Plan (months 1–12, fixed A_base) and Projections
(months 13–36, optimized MILP) side-by-side, plus a combined 36-month view.

Data source: canonical ``optimized_results.csv`` + ``fixed_cashflow.csv``.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from streamlit_pages import components as C
from streamlit_pages.styles import ACCENT, ACCENT_CYAN, SUCCESS, TEXT_SECONDARY


def render(st) -> None:
    run_id = C.require_execution(st)
    if run_id is None:
        st.title("Plan de crecimiento")
        return

    C.page_header(
        st,
        "Plan de crecimiento",
        "Plan Consensuado (meses 1–12) y Proyecciones (meses 13–36)",
        run_id=run_id,
    )

    C.infeasible_banner(st, run_id)

    # ── Load data ────────────────────────────────────────────────
    results = C.canonical_csv(run_id, "optimized_results.csv")
    fixed = C.canonical_csv(run_id, "fixed_cashflow.csv")

    if results is None:
        st.warning("No se encontraron resultados optimizados para esta ejecución.")
        return

    # Determine the split point
    consensuated = results[results["t"] <= 12].copy() if "t" in results.columns else pd.DataFrame()
    projections = results[results["t"] > 12].copy() if "t" in results.columns else results.copy()

    # ── KPI summary ──────────────────────────────────────────────
    summary = C.canonical_json(run_id, "growth_plan_summary.json")
    _render_kpis(st, summary)
    C.source_caption(st, "M1_DETERMINISTIC",
                     "growth_plan_summary.json", "optimized_results.csv", "fixed_cashflow.csv")

    # ── Side-by-side: Consensuated vs Projections ────────────────
    st.markdown("### Plan Consensuado vs Proyecciones")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Plan Consensuado (meses 1–12)")
        st.caption("Adquisición fija configurada como A_base")
        if not consensuated.empty:
            _render_compact_table(st, consensuated, "Consensuado")
        else:
            st.info("Los meses 1–12 se muestran desde fixed_cashflow.")
            if fixed is not None:
                _render_compact_table(st, fixed, "Consensuado")

    with c2:
        st.markdown("#### Proyecciones (meses 13–36)")
        st.caption("Adquisición optimizada por el solver MILP")
        if not projections.empty:
            _render_compact_table(st, projections, "Proyección")
        else:
            st.info("No hay datos de proyección disponibles.")

    # ── Combined chart ───────────────────────────────────────────
    st.markdown("### Vista Combinada (36 meses)")
    _render_combined_chart(st, results, fixed)

    # ── Channel breakdown ────────────────────────────────────────
    if "A_salesforce" in results.columns:
        st.markdown("### Desglose por canal")
        _render_channel_chart(st, results)

    # ── Detail expanders ─────────────────────────────────────────
    with st.expander("Flujo de clientes (detalle)"):
        customers = C.postprocessed_csv(run_id, "accelerated_growth_plan", "01_customer_flow.csv")
        if customers is not None:
            st.dataframe(customers, use_container_width=True, hide_index=True)
        else:
            _show_canonical_cols(st, results, ["t", "Adq_clientes", "Clientes_activos"])

    with st.expander("Flujo de ingresos (detalle)"):
        revenue = C.postprocessed_csv(run_id, "accelerated_growth_plan", "03_revenue_flow.csv")
        if revenue is not None:
            st.dataframe(revenue, use_container_width=True, hide_index=True)
        else:
            _show_canonical_cols(st, results, ["t", "Ingresos", "Ingresos_recurrentes_proxy", "ARR_pct"])

    with st.expander("Caja y capital de trabajo (detalle)"):
        cash = C.postprocessed_csv(run_id, "accelerated_growth_plan", "07_cash_and_working_capital.csv")
        if cash is not None:
            st.dataframe(cash, use_container_width=True, hide_index=True)
        else:
            _show_canonical_cols(st, results, ["t", "EBITDA", "EBITDA_acum", "Caja"])

    with st.expander("Costos y CAC (detalle)"):
        costs = C.postprocessed_csv(run_id, "accelerated_growth_plan", "06_costs_and_cac.csv")
        if costs is not None:
            st.dataframe(costs, use_container_width=True, hide_index=True)
        else:
            _show_canonical_cols(st, results, ["t", "CAC", "Costo_operacional", "G_adm", "RRHH"])

    # ── Download ─────────────────────────────────────────────────
    st.markdown("---")
    C.download_excel_button(
        st,
        dfs={
            "Plan_Consensuado": consensuated if not consensuated.empty else fixed,
            "Proyecciones": projections,
            "Resultados_completos": results,
        },
        filename="growth_plan.xlsx",
        label="Descargar Excel (plan de crecimiento)",
    )


# --------------------------------------------------------------------------- #
# KPI row
# --------------------------------------------------------------------------- #


def _render_kpis(st, summary: dict | None) -> None:
    if summary is None:
        return
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        C.kpi(st, "Estado solver", str(summary.get("solver_status", "—")),
              tone="success" if summary.get("solver_status") == "Optimal" else "warn")
    with c2:
        C.kpi(st, "Adquisición total", C.number(summary.get("total_acquisition")), "clientes")
    with c3:
        tone = "success" if (summary.get("total_revenue") or 0) > 0 else ""
        C.kpi(st, "Ingresos totales", C.money(summary.get("total_revenue")), tone=tone)
    with c4:
        tone = "success" if (summary.get("total_ebitda") or 0) >= 0 else "alert"
        C.kpi(st, "EBITDA total", C.money(summary.get("total_ebitda")), tone=tone)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        C.kpi(st, "Caja final", C.money(summary.get("final_cash")))
    with c6:
        min_cash = summary.get("minimum_cash", 0)
        C.kpi(st, "Caja mínima", C.money(min_cash), tone="alert" if (min_cash or 0) < 0 else "")
    with c7:
        C.kpi(st, "Breakeven (mes)",
              f"Mes {summary.get('breakeven_month')}" if summary.get("breakeven_month") else "—")
    with c8:
        channel_names = {"salesforce": "Fuerza de ventas", "advertising": "Publicidad",
                         "third_party": "Terceros"}
        channels = [channel_names.get(c, c) for c in summary.get("enabled_channels", [])]
        C.kpi(st, "Canales activos", ", ".join(channels) if channels else "—")


# --------------------------------------------------------------------------- #
# Compact table
# --------------------------------------------------------------------------- #


def _render_compact_table(st, df: pd.DataFrame, prefix: str) -> None:
    cols = [c for c in ["t", "Adq_clientes", "Ingresos", "EBITDA", "Caja"] if c in df.columns]
    if not cols:
        st.dataframe(df.head(12), use_container_width=True, hide_index=True)
        return
    display = df[cols].copy()
    for col in ["Ingresos", "EBITDA", "Caja"]:
        if col in display.columns:
            display[col] = display[col].apply(lambda x: f"USD {x:,.0f}" if pd.notna(x) else "—")
    st.dataframe(display, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------- #
# Combined chart
# --------------------------------------------------------------------------- #


def _render_combined_chart(st, results: pd.DataFrame, fixed: pd.DataFrame | None) -> None:
    df = results.copy()
    if "t" not in df.columns:
        st.warning("Columna 't' no encontrada en resultados.")
        return

    has_ebitda = "EBITDA" in df.columns
    has_caja = "Caja" in df.columns
    has_ingresos = "Ingresos" in df.columns

    traces = []
    if has_ingresos:
        traces.append(
            go.Scatter(x=df["t"], y=df["Ingresos"], name="Ingresos",
                       line=dict(color=ACCENT), hovertemplate="Mes %{x}<br>USD %{y:,.0f}<extra></extra>")
        )
    if has_ebitda:
        traces.append(
            go.Scatter(x=df["t"], y=df["EBITDA"], name="EBITDA",
                       line=dict(color=SUCCESS), hovertemplate="Mes %{x}<br>USD %{y:,.0f}<extra></extra>")
        )

    if traces:
        fig = go.Figure()
        for t in traces:
            fig.add_trace(t)

        # Add vertical line at month 12
        fig.add_vline(x=12.5, line_dash="dash", line_color=TEXT_SECONDARY,
                      annotation_text="Fin Plan Consensuado", annotation_position="top")

        if has_caja:
            fig.add_trace(
                go.Scatter(x=df["t"], y=df["Caja"], name="Caja acumulada",
                           line=dict(color=ACCENT_CYAN), yaxis="y2",
                           hovertemplate="Mes %{x}<br>USD %{y:,.0f}<extra></extra>")
            )

        fig.update_layout(
            height=400,
            margin=dict(t=10),
            xaxis_title="Mes",
            yaxis_title="USD",
            yaxis2=dict(overlaying="y", side="right", showgrid=False),
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_SECONDARY),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Datos insuficientes para el gráfico combinado.")


def _render_channel_chart(st, results: pd.DataFrame) -> None:
    df = results.copy()
    has_channels = all(c in df.columns for c in ["A_salesforce", "A_advertising", "A_third_party"])
    if not has_channels:
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["t"], y=df["A_salesforce"], name="Fuerza de ventas", marker_color=ACCENT))
    fig.add_trace(go.Bar(x=df["t"], y=df["A_advertising"], name="Publicidad", marker_color=ACCENT_CYAN))
    if df["A_third_party"].sum() > 0:
        fig.add_trace(go.Bar(x=df["t"], y=df["A_third_party"], name="Terceros", marker_color=SUCCESS))

    fig.add_vline(x=12.5, line_dash="dash", line_color=TEXT_SECONDARY,
                  annotation_text="Fin Plan Consensuado", annotation_position="top")

    fig.update_layout(
        barmode="stack",
        height=300,
        margin=dict(t=10),
        xaxis_title="Mes",
        yaxis_title="Adquisición",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def _show_canonical_cols(st, df: pd.DataFrame, cols: list[str]) -> None:
    present = [c for c in cols if c in df.columns]
    if present:
        st.dataframe(df[present], use_container_width=True, hide_index=True)
    else:
        st.info("Detalle no disponible para esta ejecución.")

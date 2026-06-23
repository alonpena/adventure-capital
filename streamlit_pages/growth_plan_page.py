"""Plan de crecimiento — reads postprocessed_results/accelerated_growth_plan/."""

from __future__ import annotations

import plotly.graph_objects as go

from streamlit_pages import components as C
from streamlit_pages.styles import ACCENT, ALERT, SUCCESS


def render(st) -> None:
    st.title("Plan de crecimiento acelerado")
    root = C.require_run(st)
    if root is None:
        return
    folder = root / "accelerated_growth_plan"
    summary = C.read_json(folder / "08_growth_plan_summary.json")
    if summary is None:
        st.warning("No hay artefactos de plan de crecimiento para este caso.")
        return

    status = summary.get("solver_status", "—")
    tone = "success" if status == "Optimal" else "alert"
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        C.kpi(st, "Estado solver", status, tone=tone)
    with c2:
        C.kpi(st, "Adquisición total", C.number(summary.get("total_acquisition")), "clientes")
    with c3:
        C.kpi(st, "Ingresos totales", C.money(summary.get("total_revenue")))
    with c4:
        C.kpi(st, "EBITDA total", C.money(summary.get("total_ebitda")),
              tone="success" if (summary.get("total_ebitda") or 0) >= 0 else "alert")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        C.kpi(st, "Caja final", C.money(summary.get("final_cash")))
    with c6:
        C.kpi(st, "Caja mínima", C.money(summary.get("minimum_cash")),
              tone="alert" if (summary.get("minimum_cash") or 0) < 0 else "")
    with c7:
        C.kpi(st, "Breakeven", f"Mes {summary.get('breakeven_month')}" if summary.get("breakeven_month") else "—")
    with c8:
        C.kpi(st, "Canales activos", ", ".join(summary.get("enabled_channels", [])) or "—")

    revenue = C.read_csv(folder / "03_revenue_flow.csv")
    cash = C.read_csv(folder / "07_cash_and_working_capital.csv")
    customers = C.read_csv(folder / "01_customer_flow.csv")

    if revenue is not None and cash is not None:
        st.subheader("Ingresos y EBITDA mensual")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=revenue["t"], y=revenue["Ingresos"], name="Ingresos", line=dict(color=ACCENT)))
        fig.add_trace(go.Scatter(x=cash["t"], y=cash["EBITDA"], name="EBITDA", line=dict(color=SUCCESS)))
        fig.update_layout(height=340, margin=dict(t=10), xaxis_title="Mes", yaxis_title="USD", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    if cash is not None:
        st.subheader("Caja acumulada")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=cash["t"], y=cash["Caja"], name="Caja", line=dict(color=ACCENT), fill="tozeroy"))
        fig2.add_hline(y=0, line_color=ALERT, line_width=1)
        fig2.update_layout(height=300, margin=dict(t=10), xaxis_title="Mes", yaxis_title="USD", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    if customers is not None:
        st.subheader("Flujo de clientes")
        st.dataframe(customers, use_container_width=True, hide_index=True)

    def _detail(label: str, df) -> None:
        with st.expander(label):
            if df is not None:
                st.dataframe(df, use_container_width=True, hide_index=True)

    _detail("Flujo de ingresos (detalle)", revenue)
    _detail("Caja y capital de trabajo (detalle)", cash)
    _detail("Costos y CAC", C.read_csv(folder / "06_costs_and_cac.csv"))

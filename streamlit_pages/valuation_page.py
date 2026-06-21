"""Valoración — reads postprocessed_results/valuation_workbook/."""

from __future__ import annotations

from streamlit_pages import components as C


def render(st) -> None:
    st.title("Valoración")
    root = C.require_run(st)
    if root is None:
        return
    folder = root / "valuation_workbook"
    summary = C.read_json(folder / "05_valuation_summary.json")
    if summary is None:
        st.warning("No hay artefactos de valoración para este caso.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        C.kpi(st, "VAN (DCF)", C.money(summary.get("van")),
              tone="success" if (summary.get("van") or 0) >= 0 else "alert")
    with c2:
        C.kpi(st, "VP de flujos", C.money(summary.get("vp_flujos")))
    with c3:
        C.kpi(st, "Capital invertido (VC)", C.money(summary.get("vc_invested")))

    c4, c5, c6 = st.columns(3)
    with c4:
        C.kpi(st, "Valor de desecho (VP)", C.money(summary.get("vr_pv")))
    with c5:
        C.kpi(st, "EBITDA anualizado", C.money(summary.get("ebitda_anualizado")))
    with c6:
        C.kpi(st, "Método valor terminal", str(summary.get("terminal_value_method", "—")))

    st.subheader("Insumos DCF")
    dcf_inputs = C.read_json(folder / "02_dcf_inputs.json") or {}
    d1, d2, d3 = st.columns(3)
    with d1:
        C.kpi(st, "Tasa anual (beta)", C.pct(dcf_inputs.get("beta_anual")))
    with d2:
        C.kpi(st, "Tasa mensual", C.pct(dcf_inputs.get("beta_mensual"), 3))
    with d3:
        C.kpi(st, "Impuesto", C.pct(dcf_inputs.get("tax")))

    st.subheader("Múltiplos (referencia)")
    mult = summary.get("multiples_reference", {})
    C.note(st, mult.get("methodological_note", "Múltiplos configurables, no comparables de mercado calibrados."))
    m1, m2 = st.columns(2)
    with m1:
        C.kpi(st, "Valor por ingresos", C.money(mult.get("valor_por_ingresos")), f"x{mult.get('mult_ingresos')}")
    with m2:
        C.kpi(st, "Valor por EBITDA", C.money(mult.get("valor_por_ebitda")), f"x{mult.get('mult_ebitda')}")

    st.subheader("Unit economics")
    unit = C.read_csv(folder / "06_unit_economics_detail.csv")
    if unit is not None:
        st.dataframe(unit, use_container_width=True, hide_index=True)
    C.note(st, "LTV/CAC puede estar inflado por construcción de fórmula (artefacto de calibración); interpretar con la página de Due Diligence.")

    st.subheader("Trazabilidad de fórmulas")
    trace = C.read_json(folder / "07_formula_trace.json") or {}
    for formula in trace.get("formulas", []):
        tone = {"implemented": "ok", "proxy": "warn", "methodological_reference": "muted"}.get(
            formula.get("implementation_status", ""), "muted"
        )
        with st.expander(f"{formula.get('id')} — {formula.get('name')}"):
            C.badge(st, formula.get("implementation_status", "—"), tone)
            st.code(formula.get("expression", ""))
            st.write("**Supuestos:**", "; ".join(formula.get("assumptions", [])) or "—")
            st.write("**Limitaciones:**", "; ".join(formula.get("limitations", [])) or "—")

    with st.expander("Flujo de caja DCF (detalle)"):
        cashflow = C.read_csv(folder / "01_cashflow_detail.csv")
        if cashflow is not None:
            st.dataframe(cashflow, use_container_width=True, hide_index=True)

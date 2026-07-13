"""Valoración — DCF, múltiplos, unit economics y trazabilidad de fórmulas.

Lee desde los artefactos canónicos (``dcf_cashflow.csv``, ``valuation_summary.json``,
``unit_economics.csv``) y desde los postprocessed como respaldo.
"""

from __future__ import annotations

from streamlit_pages import components as C


def render(st) -> None:
    run_id = C.require_execution(st)
    if run_id is None:
        st.title("Valoración")
        return

    C.page_header(
        st,
        "Valoración",
        "Flujo de caja descontado, múltiplos de referencia y unit economics.",
        run_id=run_id,
    )

    C.infeasible_banner(st, run_id)

    # ── Load data ────────────────────────────────────────────────
    summary = C.canonical_json(run_id, "valuation_summary.json")
    dcf_annual = C.canonical_csv(run_id, "dcf_annual_summary.csv")
    dcf_cashflow = C.canonical_csv(run_id, "dcf_cashflow.csv")
    unit_ec = C.canonical_csv(run_id, "unit_economics.csv")
    multiples = C.canonical_csv(run_id, "multiples_valuation.csv")
    formula_trace = C.canonical_json(run_id, "formula_trace.json")

    if summary is None:
        st.warning("No hay datos de valoración para esta ejecución.")
        return

    # ── DCF Summary ──────────────────────────────────────────────
    st.markdown("### Flujo de Caja Descontado (DCF)")
    c1, c2, c3 = st.columns(3)
    with c1:
        van = summary.get("van", summary.get("VAN"))
        C.kpi(st, "VAN (Valor Actual Neto)", C.money(van),
              tone="success" if (van or 0) >= 0 else "alert")
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
        C.kpi(st, "Método valor terminal",
              str(summary.get("terminal_value_method", "—")))
    C.source_caption(st, "M2_VALUATION", "valuation_summary.json", "dcf_cashflow.csv")

    # ── DCF inputs ───────────────────────────────────────────────
    st.markdown("#### Insumos DCF")
    dcf_inputs = C.canonical_json(run_id, "valuation_summary.json") or {}
    d1, d2, d3 = st.columns(3)
    with d1:
        C.kpi(st, "Tasa anual (beta)", C.pct(dcf_inputs.get("beta_anual")))
    with d2:
        C.kpi(st, "Tasa mensual", C.pct(dcf_inputs.get("beta_mensual"), 3))
    with d3:
        C.kpi(st, "Impuesto", C.pct(dcf_inputs.get("tax")))

    # ── Cash flow (annual, standard-report structure) ────────────
    if dcf_annual is not None:
        st.markdown("### Flujo de caja anual")
        _render_annual_cashflow(st, dcf_annual)
        C.source_caption(st, "M2_VALUATION", "dcf_annual_summary.csv")

    # ── Multiples ────────────────────────────────────────────────
    st.markdown("### Múltiplos de referencia")
    if multiples is not None and not multiples.empty:
        mult_row = multiples.iloc[0].to_dict() if len(multiples) == 1 else multiples
        if isinstance(mult_row, dict):
            m1, m2 = st.columns(2)
            with m1:
                C.kpi(st, "Valor por ingresos",
                      C.money(mult_row.get("Valor_ingresos", mult_row.get("valor_por_ingresos"))),
                      f"x{mult_row.get('Mult_ingresos', mult_row.get('mult_ingresos', '—'))}")
            with m2:
                C.kpi(st, "Valor por EBITDA",
                      C.money(mult_row.get("Valor_ebitda", mult_row.get("valor_por_ebitda"))),
                      f"x{mult_row.get('Mult_ebitda', mult_row.get('mult_ebitda', '—'))}")
        else:
            st.dataframe(multiples, use_container_width=True, hide_index=True)

    # ── Unit Economics ───────────────────────────────────────────
    st.markdown("### Unit Economics")
    if unit_ec is not None:
        # Show as a metric grid first
        if "Unit Economic" in unit_ec.columns and "Valor" in unit_ec.columns:
            _render_unit_economics_grid(st, unit_ec)
        # Then full table
        with st.expander("Detalle de unit economics"):
            st.dataframe(unit_ec, use_container_width=True, hide_index=True)
    else:
        pp_unit = C.postprocessed_csv(run_id, "valuation_workbook", "06_unit_economics_detail.csv")
        if pp_unit is not None:
            _render_unit_economics_grid(st, pp_unit)
            with st.expander("Detalle de unit economics"):
                st.dataframe(pp_unit, use_container_width=True, hide_index=True)
        else:
            st.info("Unit economics no disponibles para esta ejecución.")

    # ── Formula trace ────────────────────────────────────────────
    if formula_trace:
        st.markdown("### Trazabilidad de fórmulas")
        for formula in formula_trace.get("formulas", []):
            status = formula.get("implementation_status", "")
            tone = "ok" if status == "implemented" else ("warn" if status == "proxy" else "muted")
            with st.expander(f"{formula.get('id')} — {formula.get('name')}"):
                C.badge(st, status, tone)
                st.code(formula.get("expression", ""))
                st.write("**Supuestos:**", "; ".join(formula.get("assumptions", [])) or "—")
                st.write("**Limitaciones:**", "; ".join(formula.get("limitations", [])) or "—")

    # ── Cashflow detail ──────────────────────────────────────────
    if dcf_cashflow is not None:
        with st.expander("Flujo de caja DCF mensual (detalle)"):
            st.dataframe(dcf_cashflow, use_container_width=True, hide_index=True)

    # ── Download ─────────────────────────────────────────────────
    st.markdown("---")
    _render_download_buttons(st, run_id, dcf_cashflow, dcf_annual, multiples, unit_ec)


# --------------------------------------------------------------------------- #
# Annual cash flow (same structure as the standard report)
# --------------------------------------------------------------------------- #

_CASHFLOW_COLUMNS = {
    "Año": "Año",
    "Ingresos": "Ingresos",
    "Costo_operacional": "Costo operacional",
    "CAC": "CAC",
    "G_adm": "G. administración",
    "RRHH": "RRHH",
    "EBITDA": "EBITDA",
    "Impuesto": "Impuesto",
    "FC_neto": "FC neto",
    "FC_desc": "FC descontado",
}


def _render_annual_cashflow(st, dcf_annual) -> None:
    cols = [c for c in _CASHFLOW_COLUMNS if c in dcf_annual.columns]
    df = dcf_annual[cols].rename(columns=_CASHFLOW_COLUMNS) if cols else dcf_annual
    money_cols = [c for c in df.columns if c != "Año"]
    st.dataframe(
        df.style.format({c: "{:,.0f}" for c in money_cols}),
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------------------------------- #
# Unit economics grid
# --------------------------------------------------------------------------- #


def _format_unit_economic(value, unit: str) -> tuple[str, str]:
    """Format a unit-economics value according to its declared unit.

    Returns ``(display_value, sub_label)``.
    """
    if not isinstance(value, (int, float)):
        return str(value), unit
    unit = (unit or "").strip()
    if unit == "%":
        return C.pct(value), ""
    if unit == "ratio":
        return f"{value:,.1f}x", ""
    if unit.startswith("#"):
        return C.number(value, 0), unit.lstrip("# ").strip()
    if unit.startswith("USD"):
        suffix = unit[3:].lstrip("/ ").strip()
        return C.money(value), suffix
    if "veces" in unit:
        return C.number(value, 2), unit
    return C.number(value, 2), unit


def _render_unit_economics_grid(st, df) -> None:
    import pandas as pd

    if "Unit Economic" not in df.columns or "Valor" not in df.columns:
        return

    rows = [
        (str(row["Unit Economic"]), row["Valor"], str(row.get("Unidad", "") or ""))
        for _, row in df.iterrows()
        if pd.notna(row.get("Valor"))
    ]
    if not rows:
        return

    cols = st.columns(min(4, len(rows)))
    for i, (key, val, unit) in enumerate(rows):
        display, sub = _format_unit_economic(val, unit)
        tone = ""
        if isinstance(val, (int, float)) and val < 0:
            tone = "alert"
        with cols[i % 4]:
            C.kpi(st, key, display, sub=sub, tone=tone)


# --------------------------------------------------------------------------- #
# Download
# --------------------------------------------------------------------------- #


def _render_download_buttons(st, run_id: str, *dfs) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        C.download_html_button(st, run_id, label="Descargar HTML (valoración)")
    with c2:
        C.download_pdf_button(st, run_id, label="Descargar PDF")
    with c3:
        named = {}
        for i, df in enumerate(dfs):
            if df is not None:
                named[f"Sheet_{i+1}"] = df
        if named:
            C.download_excel_button(
                st,
                dfs=named,
                filename="valuation.xlsx",
                label="Descargar Excel",
            )

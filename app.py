"""Adventure Capital — Streamlit UI.

Adapted to the current product vision (ADR 0008):

- Landing page: instance manager (create/list/delete instances)
- Sidebar: execution history browser
- Main area: Executive Report (report.html) as primary view + drill-down tabs

Run: uv run streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from streamlit_pages import (
    due_diligence_page,
    executive_report_page,
    growth_plan_page,
    instance_manager_page,
    stochastic_page,
    valuation_page,
)
from streamlit_pages import components as C
from streamlit_pages.styles import inject


def _build_sidebar(st) -> None:
    """Render sidebar: instance link + execution history + drill-down nav."""
    st.sidebar.title("Adventure Capital")
    st.sidebar.caption("Valoración y plan de crecimiento")

    # ── Instance manager link ────────────────────────────────────
    if st.sidebar.button("🏗️ Gestor de Instancias", use_container_width=True):
        st.session_state["current_page"] = "instancias"
        st.session_state["current_run_id"] = None
        st.rerun()

    st.sidebar.markdown("---")

    # ── Execution history ────────────────────────────────────────
    st.sidebar.markdown("#### Ejecuciones recientes")
    executions = C.list_executions()
    if not executions:
        st.sidebar.info("Sin ejecuciones aún.")
        return

    # Build a list of (label, run_id) for the radio
    options = []
    label_map = {}
    for exe in executions[:20]:  # max 20 recent
        rid = exe["id"]
        name = exe.get("name", rid)
        status = exe.get("status", "—")
        icon = C.STATUS_ICON.get(status, "⚪")
        label = f"{icon} {name}  ({rid[:20]}…)"
        options.append(label)
        label_map[label] = rid

    # Point the radio at the currently selected run so navigating between pages
    # does not snap the selection back to the newest execution (which would
    # override current_run_id and hijack the current page).
    current_run_id = st.session_state.get("current_run_id")
    rid_order = [label_map[label] for label in options]
    try:
        current_index = rid_order.index(current_run_id) if current_run_id else None
    except ValueError:
        current_index = None

    selected_label = st.sidebar.radio(
        "Seleccionar ejecución",
        options,
        index=current_index,
        key="exec_radio",
        format_func=lambda x: x,
    )

    if selected_label and label_map.get(selected_label):
        run_id = label_map[selected_label]
        if run_id != current_run_id:
            st.session_state["current_run_id"] = run_id
            st.session_state["current_page"] = "Informe Ejecutivo"
            st.rerun()

    current_run_id = st.session_state.get("current_run_id")
    if current_run_id:
        rec = C.get_execution(current_run_id)
        if rec:
            st.sidebar.markdown("---")
            stages = rec.get("stages", {})
            status_line = []
            for stage_key in ["M1_DETERMINISTIC", "M2_VALUATION", "M3_DUE_DILIGENCE", "M4_STOCHASTIC", "M5_REPORT"]:
                state = stages.get(stage_key, "—")
                icon = C.STATUS_ICON.get(state, "⚪")
                status_line.append(f"{icon}")
            st.sidebar.markdown("Etapas: " + " ".join(status_line))

            # ── Page navigation ──────────────────────────────────
            st.sidebar.markdown("---")
            st.sidebar.markdown("#### Páginas")

            pages = [
                "📄 Informe Ejecutivo",
                "📊 Plan de Crecimiento",
                "💰 Valoración",
                "🔍 Due Diligence",
                "📈 Análisis de Escenarios",
            ]

            current = st.session_state.get("current_page", pages[0])
            for page in pages:
                if st.sidebar.button(page, use_container_width=True,
                                     type="secondary" if page != current else "primary"):
                    st.session_state["current_page"] = page
                    st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Adventure Capital",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject(st)

    # ── Init session state ─────────────────────────────────────
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "instancias"
    if "current_run_id" not in st.session_state:
        st.session_state["current_run_id"] = None

    _build_sidebar(st)

    # ── Route to page ────────────────────────────────────────────
    page = st.session_state["current_page"]

    if page == "instancias" or st.session_state.get("current_run_id") is None:
        instance_manager_page.render(st)
        return

    if page == "📄 Informe Ejecutivo":
        executive_report_page.render(st)
    elif page == "📊 Plan de Crecimiento":
        growth_plan_page.render(st)
    elif page == "💰 Valoración":
        valuation_page.render(st)
    elif page == "🔍 Due Diligence":
        due_diligence_page.render(st)
    elif page == "📈 Análisis de Escenarios":
        stochastic_page.render(st)
    else:
        instance_manager_page.render(st)


if __name__ == "__main__":
    main()

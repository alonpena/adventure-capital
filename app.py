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
    artifacts_page,
    due_diligence_page,
    executive_report_page,
    growth_plan_page,
    instance_manager_page,
    stochastic_page,
    valuation_page,
)
from streamlit_pages import components as C
from streamlit_pages.styles import inject

_PAGE_RENDERERS = {
    C.PAGE_REPORT: executive_report_page.render,
    C.PAGE_GROWTH: growth_plan_page.render,
    C.PAGE_VALUATION: valuation_page.render,
    C.PAGE_DD: due_diligence_page.render,
    C.PAGE_STOCH: stochastic_page.render,
    C.PAGE_ARTIFACTS: artifacts_page.render,
}

# M3 stores the DD verdict string, not a plain stage status.
_STEP_CLASS = {
    "completed": "completed",
    "failed": "failed",
    "blocked": "blocked",
    "passed": "completed",
    "passed_with_warnings": "blocked",
    "requires_minor_adjustment": "blocked",
    "requires_major_adjustment": "failed",
    "rejected_for_stochastic": "failed",
}


def _run_stamp(run_id: str) -> str:
    """Human-readable timestamp from a run id like ``run_20260701-115219_ab12``."""
    try:
        raw = run_id.split("_")[1]  # 20260701-115219
        date, time = raw.split("-")
        return f"{date[6:8]}-{date[4:6]} {time[:2]}:{time[2:4]}"
    except (IndexError, ValueError):
        return run_id[:12]


def _build_sidebar(st) -> None:
    """Render sidebar: instance link + execution history + drill-down nav."""
    st.sidebar.markdown(
        '<div style="padding:.2rem 0 .6rem 0;">'
        '<div style="font-family:Georgia,serif;font-size:1.3rem;font-weight:600;">'
        'Adventure <span class="ac-brand-accent">Capital</span></div>'
        '<div style="font-size:.75rem;color:#6B675E;">Valoración y plan de crecimiento</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Instance manager link ────────────────────────────────────
    if st.sidebar.button("Gestor de instancias", use_container_width=True):
        st.session_state["current_page"] = C.PAGE_INSTANCES
        st.session_state["current_run_id"] = None
        st.rerun()

    st.sidebar.markdown("---")

    # ── Execution history ────────────────────────────────────────
    st.sidebar.markdown("#### Ejecuciones recientes")
    executions = C.list_executions()
    if not executions:
        st.sidebar.caption(
            "Sin ejecuciones todavía. Crea una instancia y ejecútala para ver resultados aquí."
        )
        return

    # Build a list of (label, run_id) for the radio
    options = []
    label_map = {}
    for exe in executions[:20]:  # max 20 recent
        rid = exe["id"]
        name = exe.get("instance_name", exe.get("name", rid))
        status = exe.get("status", "—")
        icon = C.STATUS_ICON.get(status, "○")
        label = f"{icon} {name} · {_run_stamp(rid)}"
        if label in label_map:  # same instance run in the same minute
            label = f"{label} ({rid[-4:]})"
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
            st.session_state["current_page"] = C.PAGE_REPORT
            st.rerun()

    current_run_id = st.session_state.get("current_run_id")
    if current_run_id:
        rec = C.get_execution(current_run_id)
        if rec:
            st.sidebar.markdown("---")
            st.sidebar.markdown("#### Etapas del caso")
            stages = rec.get("stages", {})
            steps_html = []
            for stage_key in ["M1_DETERMINISTIC", "M2_VALUATION", "M3_DUE_DILIGENCE", "M4_STOCHASTIC", "M5_REPORT"]:
                state = stages.get(stage_key, "pending")
                label = C.STAGE_LABELS.get(stage_key, stage_key)
                steps_html.append(
                    f'<div class="ac-step {_STEP_CLASS.get(state, "")}">'
                    f'<span class="dot"></span>{label}</div>'
                )
            st.sidebar.markdown("".join(steps_html), unsafe_allow_html=True)

            # ── Page navigation ──────────────────────────────────
            st.sidebar.markdown("---")
            st.sidebar.markdown("#### Páginas")

            current = st.session_state.get("current_page", C.PAGE_REPORT)
            for page in C.NAV_PAGES:
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
        st.session_state["current_page"] = C.PAGE_INSTANCES
    if "current_run_id" not in st.session_state:
        st.session_state["current_run_id"] = None

    _build_sidebar(st)

    # ── Route to page ────────────────────────────────────────────
    page = st.session_state["current_page"]

    if page == C.PAGE_INSTANCES or st.session_state.get("current_run_id") is None:
        instance_manager_page.render(st)
        return

    renderer = _PAGE_RENDERERS.get(page, instance_manager_page.render)
    renderer(st)


if __name__ == "__main__":
    main()

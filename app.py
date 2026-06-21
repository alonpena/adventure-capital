"""Adventure Capital — Streamlit MVP.

Local app for configuring a startup case, running the existing pipeline, and
browsing the generated artifacts. Result pages read only from the artifacts
under the run output directory; the model/valuation/DD/stochastic logic is never
recomputed in the UI (artifacts are the source of truth, ADR 0007).

Run: uv run streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from streamlit_pages import (
    config_page,
    due_diligence_page,
    growth_plan_page,
    stochastic_page,
    valuation_page,
)
from streamlit_pages.styles import inject

PAGES = {
    "Configuración": config_page.render,
    "Plan de crecimiento": growth_plan_page.render,
    "Valoración": valuation_page.render,
    "Due Diligence": due_diligence_page.render,
    "Análisis estocástico": stochastic_page.render,
}


def main() -> None:
    st.set_page_config(page_title="Adventure Capital", page_icon="📈", layout="wide")
    inject(st)

    st.sidebar.title("Adventure Capital")
    st.sidebar.caption("Valoración y plan de crecimiento de startups")
    choice = st.sidebar.radio("Navegación", list(PAGES.keys()))

    out = st.session_state.get("output_dir")
    st.sidebar.markdown("---")
    if out:
        st.sidebar.success("Caso ejecutado")
        st.sidebar.caption(out)
    else:
        st.sidebar.info("Sin caso ejecutado")

    PAGES[choice](st)


if __name__ == "__main__":
    main()

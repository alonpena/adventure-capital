"""Smoke tests for the Streamlit MVP: imports and wiring only (no browser)."""

from __future__ import annotations

import importlib


def test_pages_import_and_expose_render():
    modules = [
        "streamlit_pages.config_page",
        "streamlit_pages.growth_plan_page",
        "streamlit_pages.valuation_page",
        "streamlit_pages.due_diligence_page",
        "streamlit_pages.stochastic_page",
    ]
    for name in modules:
        module = importlib.import_module(name)
        assert callable(module.render)


def test_app_registers_all_pages():
    app = importlib.import_module("app")
    assert set(app.PAGES) == {
        "Configuración",
        "Plan de crecimiento",
        "Valoración",
        "Due Diligence",
        "Análisis estocástico",
    }
    assert all(callable(fn) for fn in app.PAGES.values())


def test_components_artifact_helpers_are_pure():
    from streamlit_pages import components as C

    # No run -> readers return None instead of raising.
    from pathlib import Path
    assert C.read_json(Path("/nonexistent/x.json")) is None
    assert C.read_csv(Path("/nonexistent/x.csv")) is None
    assert C.money(None) == "—"
    assert C.money(1000) == "USD 1,000"
    assert C.pct(0.5) == "50.0%"

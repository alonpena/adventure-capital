"""Smoke tests for the Streamlit MVP: imports and wiring only (no browser)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def test_pages_import_and_expose_render():
    modules = [
        "streamlit_pages.instance_manager_page",
        "streamlit_pages.growth_plan_page",
        "streamlit_pages.valuation_page",
        "streamlit_pages.due_diligence_page",
        "streamlit_pages.stochastic_page",
        "streamlit_pages.executive_report_page",
    ]
    for name in modules:
        module = importlib.import_module(name)
        assert callable(module.render)


def test_old_config_page_replaced():
    """config_page was replaced by instance_manager_page; ensure it's gone."""
    with pytest.raises(ImportError):
        importlib.import_module("streamlit_pages.config_page")  # noqa: F401


def test_components_artifact_helpers_are_pure():
    from streamlit_pages import components as C

    # No run -> readers return None instead of raising.
    assert C.canonical_json("nonexistent", "x.json") is None
    assert C.canonical_csv("nonexistent", "x.csv") is None
    assert C.money(None) == "—"
    assert C.money(1000) == "USD 1,000"
    assert C.pct(0.5) == "50.0%"
    assert C.number(1234.6) == "1,235"
    assert C.execution_path("test") == Path("outputs/executions/test")

    # Registry functions return a list (may be empty or contain previous test data)
    assert isinstance(C.list_instances(), list)
    assert isinstance(C.list_executions(), list)


def test_components_tone_maps():
    from streamlit_pages import components as C

    assert "passed" in C.VERDICT_TONE
    assert "ok" in C.SEVERITY_TONE
    assert "completed" in C.STATUS_TONE
    assert "M1_DETERMINISTIC" in C.STAGE_LABELS


def test_apply_loaded_yaml_fills_all_fields():
    """Loading a YAML must populate scalars, services and channels — and drop
    stale per-widget keys so Streamlit's value= takes effect on rerun."""
    from adventure_capital.config import default_config
    from streamlit_pages import instance_manager_page as P

    base = default_config()

    class FakeST:
        def __init__(self):
            self.session_state = {}

    st = FakeST()
    # Stale widget state from a prior render.
    st.session_state.update(
        {"svc_name_0": "OLD", "svc_ticket_0": 1.0, "ch_sf_active": False, "f_H": base["H"]}
    )

    loaded = {
        "nombre": "Caso cargado",
        "H": 30,
        "VC": 250000.0,
        "servicios": [
            {
                "nombre": "NUEVO",
                "ticket": 999.0,
                "frecuencia": 2,
                "alpha": 0.3,
                "c_u": 50.0,
                "c_min": 100.0,
                "u_max": 20,
                "churn_anual": [0.1, 0.2],
                "A_base": [1] * 12,
            }
        ],
        "channels": {
            "salesforce": {"active": True, "min_share": 0.2, "max_share": 0.8},
            "advertising": {"active": True, "I_min": 1000.0, "I_max": 5000.0,
                            "A_min": 1.0, "A_max": 9.0, "A_ad_cap": 50.0,
                            "min_share": 0.0, "max_share": 0.5},
            "third_party": {"active": False, "commission": 0.1, "min_share": 0.0, "max_share": 0.3},
        },
    }
    P._apply_loaded_yaml(st, loaded, base)
    ss = st.session_state

    assert ss["f_H"] == 30
    assert ss["f_nombre"] == "Caso cargado"
    assert ss["services"][0]["nombre"] == "NUEVO"
    # Stale per-widget keys must be gone so value= re-applies.
    assert "svc_name_0" not in ss and "svc_ticket_0" not in ss
    assert "ch_sf_active" not in ss
    assert ss["yaml_channels"]["salesforce"]["active"] is True
    assert ss["merged_config"]["nombre"] == "Caso cargado"

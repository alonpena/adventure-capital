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

    # Empty registry returns empty list
    assert C.list_instances() == []
    assert C.list_executions() == []


def test_components_tone_maps():
    from streamlit_pages import components as C

    assert "passed" in C.VERDICT_TONE
    assert "ok" in C.SEVERITY_TONE
    assert "completed" in C.STATUS_TONE
    assert "M1_DETERMINISTIC" in C.STAGE_LABELS

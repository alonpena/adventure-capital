"""Reusable UI components and artifact readers.

Result pages read ONLY from generated artifacts under the run output_dir. No
model, valuation, due-diligence, or stochastic logic is recomputed here — the
artifacts are the source of truth (ADR 0007).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as _st

POSTPROCESSED = "postprocessed_results"

# --- shared tone maps (used by multiple pages) ----------------------------

VERDICT_TONE: dict[str, str] = {
    "passed": "ok",
    "passed_with_warnings": "warn",
    "requires_minor_adjustment": "warn",
    "requires_major_adjustment": "bad",
    "rejected_for_stochastic": "bad",
}

SEVERITY_TONE: dict[str, str] = {
    "ok": "ok",
    "warning": "warn",
    "minor": "warn",
    "major": "bad",
    "structural": "bad",
}

IMPL_STATUS_TONE: dict[str, str] = {
    "implemented": "ok",
    "proxy": "warn",
    "methodological_reference": "muted",
}


# --- artifact access -------------------------------------------------------

def output_dir(st) -> Path | None:
    value = st.session_state.get("output_dir")
    return Path(value) if value else None


def view_root(st) -> Path | None:
    out = output_dir(st)
    return out / POSTPROCESSED if out else None


@_st.cache_data(show_spinner=False)
def read_json(path: Path) -> dict[str, Any] | None:
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


@_st.cache_data(show_spinner=False)
def read_csv(path: Path) -> pd.DataFrame | None:
    if path and path.exists():
        return pd.read_csv(path)
    return None


def require_run(st) -> Path | None:
    """Return the postprocessed root, or render a guard message and return None."""
    root = view_root(st)
    if root is None or not root.exists():
        st.info("Aún no se ha ejecutado el pipeline. Ve a **Configuración** y ejecuta un caso.")
        return None
    return root


# --- presentation helpers --------------------------------------------------

def money(value: Any) -> str:
    try:
        return f"USD {float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"


def number(value: Any, decimals: int = 0) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def pct(value: Any, decimals: int = 1) -> str:
    try:
        return f"{float(value) * 100:,.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def kpi(st, label: str, value: str, sub: str = "", tone: str = "") -> None:
    cls = f"ac-kpi {tone}".strip()
    st.markdown(
        f'<div class="{cls}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'<div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def badge(st, text: str, tone: str = "muted") -> None:
    st.markdown(f'<span class="ac-badge {tone}">{text}</span>', unsafe_allow_html=True)


def note(st, text: str) -> None:
    st.markdown(f'<div class="ac-note">{text}</div>', unsafe_allow_html=True)

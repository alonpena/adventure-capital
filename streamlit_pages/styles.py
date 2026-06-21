"""Corporate visual identity for the Adventure Capital MVP."""

from __future__ import annotations

SIDEBAR = "#1a2332"
ACCENT = "#2E86AB"
BACKGROUND = "#f8f9fa"
ALERT = "#c0392b"
SUCCESS = "#27ae60"
INK = "#1f2933"
MUTED = "#6b7280"

CSS = f"""
<style>
.stApp {{ background-color: {BACKGROUND}; color: {INK}; }}
[data-testid="stSidebar"] {{ background-color: {SIDEBAR}; }}
[data-testid="stSidebar"] * {{ color: #e6edf5 !important; }}
[data-testid="stSidebar"] .stRadio label {{ color: #e6edf5 !important; }}

h1, h2, h3, h4 {{ color: {INK}; font-family: -apple-system, "Segoe UI", Roboto, sans-serif; }}
h1 {{ border-bottom: 3px solid {ACCENT}; padding-bottom: .3rem; }}

.ac-kpi {{
  background: #ffffff;
  border-left: 5px solid {ACCENT};
  border-radius: 4px;
  padding: 1rem 1.2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
  margin-bottom: .6rem;
}}
.ac-kpi .label {{ color: {MUTED}; font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; }}
.ac-kpi .value {{ color: {INK}; font-size: 1.6rem; font-weight: 700; line-height: 1.2; }}
.ac-kpi .sub {{ color: {MUTED}; font-size: .78rem; }}
.ac-kpi.alert {{ border-left-color: {ALERT}; }}
.ac-kpi.success {{ border-left-color: {SUCCESS}; }}

.ac-badge {{ display:inline-block; padding:.25rem .7rem; border-radius:14px; font-weight:600; font-size:.85rem; color:#fff; }}
.ac-badge.ok {{ background:{SUCCESS}; }}
.ac-badge.warn {{ background:#e08e0b; }}
.ac-badge.bad {{ background:{ALERT}; }}
.ac-badge.muted {{ background:{MUTED}; }}

.ac-note {{ background:#fff; border:1px solid #e3e8ef; border-left:4px solid {MUTED};
  padding:.6rem .9rem; border-radius:4px; color:{MUTED}; font-size:.85rem; margin:.4rem 0; }}
</style>
"""


def inject(st) -> None:
    st.markdown(CSS, unsafe_allow_html=True)

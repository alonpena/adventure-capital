"""Corporate visual identity — dark theme matching the SolutionOps-style report.

Uses the same palette as the standard valuation report (amber accent, dark
background, muted grays) so the Streamlit drill-down tabs feel like part of
the same product as the Executive Report.
"""

from __future__ import annotations

# --- palette ---
DARK_BG = "#0d1b2a"          # deep navy — sidebar
MAIN_BG = "#1b2838"          # slightly lighter — main panel
CARD_BG = "#243447"          # card / kpi backgrounds
ACCENT = "#f0a500"           # amber — primary accent (PULL / hit)
ACCENT_CYAN = "#00b4d8"      # cyan — secondary accent (PUSH / alternative)
ALERT = "#e63946"            # red — losses, negative, danger
SUCCESS = "#2ec4b6"          # teal — positive metrics, OK
WARN = "#e08e0b"             # orange — warnings
MUTED = "#6b7280"            # gray — secondary text
TEXT_PRIMARY = "#e6edf5"     # off-white — body text
TEXT_SECONDARY = "#9ca3af"   # lighter gray — captions
BORDER = "#374151"           # subtle borders

CSS = f"""
<style>
/* ── base ───────────────────────────────────────── */
.stApp, .stApp > div {{ background-color: {MAIN_BG}; color: {TEXT_PRIMARY}; }}
[data-testid="stSidebar"] {{ background-color: {DARK_BG}; }}
[data-testid="stSidebar"] * {{ color: {TEXT_PRIMARY} !important; }}
[data-testid="stSidebar"] .stRadio label {{ color: {TEXT_PRIMARY} !important; }}

h1, h2, h3, h4, h5, h6 {{
  color: {TEXT_PRIMARY};
  font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
  font-weight: 600;
}}
h1 {{ border-bottom: 2px solid {ACCENT}; padding-bottom: .3rem; }}
h2 {{ margin-top: 1.2rem; }}
.stMarkdown, p, li, .stCaption {{ color: {TEXT_PRIMARY}; }}
.stCaption {{ color: {TEXT_SECONDARY}; }}

/* ── KPI card ───────────────────────────────────── */
.ac-kpi {{
  background: {CARD_BG};
  border-left: 4px solid {ACCENT};
  border-radius: 6px;
  padding: 1rem 1.2rem;
  box-shadow: 0 2px 6px rgba(0,0,0,.25);
  margin-bottom: .6rem;
}}
.ac-kpi .label {{ color: {TEXT_SECONDARY}; font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; }}
.ac-kpi .value {{ color: {TEXT_PRIMARY}; font-size: 1.5rem; font-weight: 700; line-height: 1.2; }}
.ac-kpi .sub {{ color: {TEXT_SECONDARY}; font-size: .75rem; }}
.ac-kpi.alert {{ border-left-color: {ALERT}; }}
.ac-kpi.success {{ border-left-color: {SUCCESS}; }}
.ac-kpi.warn {{ border-left-color: {WARN}; }}
.ac-kpi.cyan {{ border-left-color: {ACCENT_CYAN}; }}

/* ── badge / pill ───────────────────────────────── */
.ac-badge {{
  display: inline-block;
  padding: .2rem .7rem;
  border-radius: 14px;
  font-weight: 600;
  font-size: .8rem;
  color: #fff;
}}
.ac-badge.ok {{ background: {SUCCESS}; }}
.ac-badge.warn {{ background: {WARN}; }}
.ac-badge.bad {{ background: {ALERT}; }}
.ac-badge.muted {{ background: {MUTED}; }}
.ac-badge.cyan {{ background: {ACCENT_CYAN}; }}

/* ── note / info box ────────────────────────────── */
.ac-note {{
  background: {CARD_BG};
  border: 1px solid {BORDER};
  border-left: 4px solid {ACCENT};
  padding: .6rem .9rem;
  border-radius: 4px;
  color: {TEXT_SECONDARY};
  font-size: .85rem;
  margin: .4rem 0;
}}

/* ── dataframe override ─────────────────────────── */
[data-testid="StyledDataFrame"] {{
  background: {CARD_BG};
  color: {TEXT_PRIMARY};
}}
[data-testid="StyledDataFrame"] th {{
  background: {DARK_BG};
  color: {TEXT_PRIMARY};
  font-weight: 600;
}}
[data-testid="StyledDataFrame"] td {{
  background: {CARD_BG};
  color: {TEXT_PRIMARY};
}}

/* ── iframe (Executive Report) ──────────────────── */
.ac-report-iframe {{
  width: 100%;
  height: calc(100vh - 120px);
  border: none;
  border-radius: 6px;
  background: #fff;
}}

/* ── divider ────────────────────────────────────── */
hr {{ border-color: {BORDER}; margin: 1rem 0; }}

/* ── buttons ────────────────────────────────────── */
.stButton button {{
  background: {ACCENT};
  color: {DARK_BG};
  font-weight: 600;
  border: none;
}}
.stButton button:hover {{
  background: #d49400;
  color: {DARK_BG};
}}
.stButton > button[data-baseweb="button"].secondary {{
  background: {CARD_BG};
  color: {TEXT_PRIMARY};
  border: 1px solid {BORDER};
}}
.stButton > button[data-baseweb="button"].danger {{
  background: {ALERT};
  color: #fff;
}}

/* ── expander ───────────────────────────────────── */
.streamlit-expanderHeader {{
  color: {TEXT_PRIMARY} !important;
  background: {CARD_BG} !important;
  border-radius: 4px;
}}
.streamlit-expanderContent {{
  background: {CARD_BG};
  border: 1px solid {BORDER};
  border-top: none;
  border-radius: 0 0 4px 4px;
}}

/* ── tabs ───────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  gap: 0;
  border-bottom: 1px solid {BORDER};
}}
.stTabs button {{
  color: {TEXT_SECONDARY} !important;
  font-weight: 500;
}}
.stTabs button[aria-selected="true"] {{
  color: {ACCENT} !important;
  border-bottom-color: {ACCENT} !important;
}}
</style>
"""


def inject(st) -> None:
    st.markdown(CSS, unsafe_allow_html=True)

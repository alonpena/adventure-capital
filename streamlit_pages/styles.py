"""Identidad visual "Memorando / Investment Research Console".

Papel claro, jerarquía documental (serif en títulos y cifras, sans en chrome),
tablas estilo publicación, un solo acento (oxblood) y estados discretos.
Decidida el 2026-07-05; enmienda ADR 0008 §6: la identidad de la app se separa
de la paridad literal con ``report.html`` (el reporte es un documento con tema
propio dentro de la consola).

Las constantes exportadas conservan sus nombres históricos porque las páginas
las importan para las trazas Plotly.
"""

from __future__ import annotations

# --- palette ---
PAPER = "#F7F5F0"            # canvas — papel
PANEL_BG = "#FCFBF8"         # paneles / expanders (blanco roto)
SIDEBAR_BG = "#F2EFE8"       # sidebar, un punto más oscuro que el papel
INK = "#21201C"              # tinta — texto principal y reglas fuertes
ACCENT = "#7A2E2E"           # oxblood — único acento (nav activa, CTA, serie primaria)
ACCENT_CYAN = "#3E5C76"      # slate — serie secundaria en gráficos (reemplaza al cian)
ALERT = "#A32D2D"            # rojo apagado — pérdidas, bloqueos
SUCCESS = "#2E6B4F"          # verde bosque — positivo, aprobado
WARN = "#9A6A00"             # ocre — advertencias
MUTED = "#8A857B"            # gris cálido — texto terciario
TEXT_PRIMARY = INK
TEXT_SECONDARY = "#6B675E"   # gris tinta — captions y ejes de gráficos
BORDER = "#DFDACF"           # hairline
RULE_MID = "#B8B2A6"         # regla media (booktabs)

# compat con nombres antiguos usados internamente
DARK_BG = SIDEBAR_BG
MAIN_BG = PAPER
CARD_BG = PANEL_BG

SERIF = 'Georgia, "Source Serif 4", "Times New Roman", serif'
SANS = '-apple-system, "Inter", "Segoe UI", Roboto, Arial, sans-serif'
MONO = '"SF Mono", "JetBrains Mono", Menlo, Consolas, monospace'

CSS = f"""
<style>
/* ── base ───────────────────────────────────────── */
.stApp, .stApp > div {{ background-color: {PAPER}; color: {INK}; }}
/* No tocar los spans de iconos: Streamlit usa ligaduras "Material Symbols"
   y un font-family global las convierte en texto plano ("upload", …). */
.stApp *:not([data-testid="stIconMaterial"]):not([data-testid="stIconEmoji"]) {{ font-family: {SANS}; }}
[data-testid="stIconMaterial"] {{ font-family: "Material Symbols Rounded" !important; }}
header[data-testid="stHeader"] {{ background: {PAPER}; }}
[data-testid="stSidebar"] {{
  background-color: {SIDEBAR_BG};
  border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] * {{ color: {INK} !important; }}
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {{
  color: {TEXT_SECONDARY} !important;
}}

h1, h2 {{ font-family: {SERIF} !important; color: {INK}; font-weight: 600; letter-spacing: 0; }}
h1 {{ font-size: 1.6rem; }}
.stApp h3, .stApp [data-testid="stMarkdownContainer"] h3 {{
  font-family: {SANS};
  font-size: .82rem !important;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: {TEXT_SECONDARY} !important;
  border-bottom: 1px solid {RULE_MID};
  padding-bottom: .3rem;
  margin-top: 1.6rem;
}}
h4 {{ font-family: {SERIF} !important; color: {INK}; font-weight: 600; }}
.stMarkdown, p, li {{ color: {INK}; }}
.stCaption, small {{ color: {TEXT_SECONDARY}; }}
code {{ font-family: {MONO} !important; font-size: .8em; color: {INK};
       background: {SIDEBAR_BG}; padding: .05rem .3rem; border-radius: 2px; }}

/* ── page header (masthead documental) ──────────── */
.ac-page-head {{
  border-bottom: 2px solid {INK};
  padding-bottom: .55rem;
  margin-bottom: 1.1rem;
}}
.ac-page-head .title {{
  font-family: {SERIF} !important;
  font-size: 1.7rem;
  font-weight: 600;
  color: {INK};
  line-height: 1.15;
}}
.ac-page-head .subtitle {{
  color: {TEXT_SECONDARY};
  font-size: .85rem;
  margin-top: .2rem;
}}
.ac-page-head .case {{
  float: right;
  text-align: right;
  color: {TEXT_SECONDARY};
  font-size: .76rem;
  line-height: 1.5;
}}
.ac-page-head .case b {{ color: {ACCENT}; font-size: .95rem; font-family: {SERIF} !important; }}

/* ── KPI: tipografía, no tarjetas ───────────────── */
.ac-kpi {{
  background: transparent;
  border: none;
  border-top: 1px solid {RULE_MID};
  border-radius: 0;
  padding: .45rem .1rem .3rem .1rem;
  margin-bottom: .6rem;
}}
.ac-kpi .label {{ color: {TEXT_SECONDARY}; font-size: .68rem; text-transform: uppercase; letter-spacing: .1em; }}
.ac-kpi .value {{ font-family: {SERIF} !important; color: {INK}; font-size: 1.45rem; font-weight: 600; line-height: 1.3; font-variant-numeric: tabular-nums; }}
.ac-kpi .sub {{ color: {TEXT_SECONDARY}; font-size: .74rem; }}
.ac-kpi.alert .value {{ color: {ALERT}; }}
.ac-kpi.success .value {{ color: {SUCCESS}; }}
.ac-kpi.warn .value {{ color: {WARN}; }}
.ac-kpi.cyan .value {{ color: {ACCENT_CYAN}; }}

/* hero — cifras de titular */
.ac-kpi.hero .value {{ font-size: 2.3rem; }}
.ac-kpi.hero {{ border-top: 2px solid {INK}; }}

/* ── banda de riesgo (sobria) ───────────────────── */
.ac-riskband {{
  background: rgba(163, 45, 45, .045);
  border: none;
  border-left: 2px solid {ALERT};
  border-radius: 0;
  padding: .55rem .9rem .15rem .9rem;
  margin: .3rem 0 .9rem 0;
}}
.ac-riskband .band-title {{
  color: {ALERT};
  font-size: .68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .12em;
  margin-bottom: .3rem;
}}
.ac-riskband .ac-kpi {{ border-top: none; padding: .15rem .4rem; margin-bottom: .3rem; }}
.ac-riskband .ac-kpi .value {{ font-size: 1.25rem; }}

/* ── badge: texto + borde fino, sin relleno ─────── */
.ac-badge {{
  display: inline-block;
  padding: .12rem .55rem;
  border-radius: 2px;
  font-weight: 600;
  font-size: .74rem;
  letter-spacing: .03em;
  background: transparent;
}}
.ac-badge.ok {{ color: {SUCCESS}; border: 1px solid {SUCCESS}; }}
.ac-badge.warn {{ color: {WARN}; border: 1px solid {WARN}; }}
.ac-badge.bad {{ color: {ALERT}; border: 1px solid {ALERT}; }}
.ac-badge.muted {{ color: {TEXT_SECONDARY}; border: 1px solid {RULE_MID}; }}
.ac-badge.cyan {{ color: {ACCENT_CYAN}; border: 1px solid {ACCENT_CYAN}; }}

/* ── nota ───────────────────────────────────────── */
.ac-note {{
  background: {PANEL_BG};
  border: 1px solid {BORDER};
  border-left: 2px solid {RULE_MID};
  padding: .55rem .9rem;
  border-radius: 0;
  color: {TEXT_SECONDARY};
  font-size: .85rem;
  margin: .4rem 0;
}}

/* ── fuente / trazabilidad ──────────────────────── */
.ac-source {{
  color: {MUTED};
  font-size: .72rem;
  font-family: {MONO} !important;
  margin: -.2rem 0 .9rem 0;
}}

/* ── stepper (sidebar) ──────────────────────────── */
.ac-step {{
  display: flex;
  align-items: center;
  gap: .5rem;
  padding: .16rem 0;
  font-size: .8rem;
  color: {TEXT_SECONDARY};
}}
.ac-step .dot {{
  width: 8px; height: 8px; border-radius: 50%;
  background: {RULE_MID}; flex: 0 0 8px;
}}
.ac-step.completed {{ color: {INK}; }}
.ac-step.completed .dot {{ background: {SUCCESS}; }}
.ac-step.failed .dot {{ background: {ALERT}; }}
.ac-step.blocked .dot {{ background: {WARN}; }}

.ac-brand-accent {{ color: {ACCENT} !important; }}

/* ── iframe (Informe Ejecutivo) ─────────────────── */
iframe {{ border: 1px solid {BORDER}; border-radius: 2px; background: #fff; }}

hr {{ border-color: {BORDER}; margin: 1rem 0; }}

/* ── botones ────────────────────────────────────── */
.stButton button, .stDownloadButton button {{
  border-radius: 2px;
  font-weight: 600;
  font-size: .85rem;
  border: 1px solid {RULE_MID};
  background: transparent;
  color: {INK};
}}
.stButton button:hover, .stDownloadButton button:hover {{
  border-color: {INK};
  color: {INK};
  background: {PANEL_BG};
}}
.stButton button[kind="primary"], .stButton button[data-testid="stBaseButton-primary"] {{
  background: {ACCENT};
  color: #FFFFFF;
  border: 1px solid {ACCENT};
}}
.stButton button[kind="primary"]:hover, .stButton button[data-testid="stBaseButton-primary"]:hover {{
  background: #632525;
  border-color: #632525;
  color: #FFFFFF;
}}

/* ── expander ───────────────────────────────────── */
.streamlit-expanderHeader, [data-testid="stExpander"] summary {{
  color: {INK} !important;
  background: {PANEL_BG} !important;
  border-radius: 2px;
}}
[data-testid="stExpander"] {{
  border: 1px solid {BORDER};
  border-radius: 2px;
  background: {PANEL_BG};
}}

/* ── tabs ───────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  gap: 1.4rem;
  border-bottom: 1px solid {RULE_MID};
}}
.stTabs button {{
  color: {TEXT_SECONDARY} !important;
  font-weight: 500;
  background: transparent;
  border: none;
}}
.stTabs button[aria-selected="true"] {{
  color: {INK} !important;
  border-bottom-color: {ACCENT} !important;
}}

/* ── inputs ─────────────────────────────────────── */
.stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] {{
  background: #FFFFFF;
  color: {INK};
  border-color: {BORDER};
  border-radius: 2px;
}}

.stAlert {{ border-radius: 2px; }}
</style>
"""


def inject(st) -> None:
    st.markdown(CSS, unsafe_allow_html=True)

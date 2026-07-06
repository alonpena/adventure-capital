"""M5 — professional MVP Spanish HTML report from canonical flat artifacts.

This is the MVP delivery report. It deliberately does *not* depend on the
``standard_report`` package or on ``postprocessed_results``: it reads the
canonical flat artifacts written by the assessment flow and hand-builds a
single ``report.html``. Every input is optional — missing artifacts degrade to
an explanatory placeholder rather than an error, so the report renders for
completed, omitted, blocked and failed M4 states alike.

Artifacts consumed (all optional):
``growth_plan_summary.json``, ``valuation_summary.json``, ``unit_economics.csv``,
``due_diligence_report.json``, ``assessment_summary.json``,
``stochastic_summary.csv``, ``stochastic_diagnostics.json``, ``saa_solution.json``,
``optimized_results.csv`` and ``dashboard.png``.
"""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

REPORT_FILENAME = "report.html"
REPORT_PRINT_FILENAME = "report_print.html"

_TEXT = {
    "subtitle": "Valorización determinista, plan de crecimiento target-driven y análisis de robustez.",
    "deterministic": (
        "El plan oficial del MVP se obtiene con el modelo determinista target-driven: "
        "la tesis de inversión fija el crecimiento objetivo y el optimizador calcula "
        "la ejecución eficiente en recursos para alcanzarlo."
    ),
    "robustness": (
        "M4 evalúa la robustez del plan bajo incertidumbre mediante escenarios LHS. "
        "Reporta distribución de VAN, CVaR, probabilidad de VAN negativo y brecha de caja. "
        "No reemplaza el plan determinista oficial."
    ),
    "dd": (
        "La Due Diligence estructura los hallazgos de escalabilidad, caja y consistencia "
        "del modelo. Su objetivo es recomendar recalibraciones, no emitir una recomendación "
        "de inversión."
    ),
    "limitations": (
        "Los casos con logística, downgrades, setup o base instalada requieren extensiones "
        "estructurales. Se reportan como diagnóstico y trabajo futuro, no como fallas silenciosas."
    ),
    "footer": (
        "Reporte MVP generado por Adventure Capital. Material de apoyo para tesis/demo; "
        "no constituye recomendación de inversión."
    ),
}

# Canonical flat artifacts, in display order, for the closing file listing.
_ARTIFACT_FILES = [
    "config.yaml",
    "execution.json",
    "report.html",
    "report.pdf",
    "report_print.html",
    "financial_report.md",
    "dashboard.png",
    "optimized_results.csv",
    "fixed_cashflow.csv",
    "dcf_cashflow.csv",
    "dcf_annual_summary.csv",
    "growth_plan_summary.json",
    "valuation_summary.json",
    "unit_economics.csv",
    "multiples_valuation.csv",
    "due_diligence_report.json",
    "due_diligence_report.md",
    "calibration_report.md",
    "assessment_summary.json",
    "growth_suggestions.json",
    "sensitivity_wacc_multiple.csv",
    "sensitivity_variables.csv",
    "breakeven_variables.csv",
    "mapvalue.json",
    "model_instance.json",
    "stochastic_summary.csv",
    "stochastic_diagnostics.json",
    "saa_solution.json",
]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _load_csv_first_row(path: Path) -> dict[str, str] | None:
    """Return the first data row of a CSV as a dict (used for single-row summaries)."""
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                return dict(row)
    except OSError:
        return None
    return None


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            return [dict(row) for row in csv.DictReader(f)]
    except OSError:
        return []


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _money(value: Any) -> str:
    try:
        return f"USD {float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"


def _num(value: Any, decimals: int = 0) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def _pct(value: Any) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "—"


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _kpi(label: str, value: str) -> str:
    return (
        '<div class="kpi"><div class="kpi-value">'
        f"{value}</div><div class=\"kpi-label\">{_esc(label)}</div></div>"
    )


def _section(title: str, body: str) -> str:
    return f'<section><h2>{_esc(title)}</h2>{body}</section>'


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _paragraph(text: str) -> str:
    return f'<p class="lead">{_esc(text)}</p>'


def _dashboard_image(output_dir: Path) -> str:
    if not (output_dir / "dashboard.png").exists():
        return ""
    return (
        '<figure class="figure"><img src="dashboard.png" alt="Dashboard financiero" />'
        "<figcaption>Dashboard generado desde artefactos canónicos del plan.</figcaption></figure>"
    )


def _svg_chart(
    rows: list[dict[str, str]],
    *,
    title: str,
    series: list[tuple[str, str, str]],
    height: int = 240,
) -> str:
    """Small dependency-free SVG chart from monthly optimized results."""
    if not rows:
        return ""
    points_by_series: list[tuple[str, str, list[tuple[float, float]]]] = []
    values: list[float] = []
    months: list[float] = []
    for label, col, color in series:
        pts: list[tuple[float, float]] = []
        for row in rows:
            t = _float(row.get("t"))
            y = _float(row.get(col))
            if t is None or y is None:
                continue
            pts.append((t, y))
            months.append(t)
            values.append(y)
        if pts:
            points_by_series.append((label, color, pts))
    if not points_by_series or not months or not values:
        return ""

    width = 820
    pad_l, pad_r, pad_t, pad_b = 58, 20, 26, 38
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    min_x, max_x = min(months), max(months)
    min_y, max_y = min(values), max(values)
    if min_y == max_y:
        min_y -= 1.0
        max_y += 1.0
    if min_y > 0:
        min_y = 0.0

    def xy(point: tuple[float, float]) -> tuple[float, float]:
        x, y = point
        sx = pad_l + (x - min_x) / max(1.0, (max_x - min_x)) * plot_w
        sy = pad_t + (max_y - y) / max(1.0, (max_y - min_y)) * plot_h
        return sx, sy

    zero_y = xy((min_x, 0.0))[1] if min_y <= 0 <= max_y else height - pad_b
    lines = [
        f'<div class="chart"><h3>{_esc(title)}</h3>',
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{_esc(title)}">',
        f'<line x1="{pad_l}" y1="{zero_y:.1f}" x2="{width-pad_r}" y2="{zero_y:.1f}" class="axis zero" />',
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{height-pad_b}" class="axis" />',
        f'<line x1="{pad_l}" y1="{height-pad_b}" x2="{width-pad_r}" y2="{height-pad_b}" class="axis" />',
        f'<text x="{pad_l}" y="{height-12}" class="tick">m1</text>',
        f'<text x="{width-pad_r-26}" y="{height-12}" class="tick">m{int(max_x)}</text>',
        f'<text x="8" y="{pad_t+5}" class="tick">{_esc(_money(max_y))}</text>',
        f'<text x="8" y="{height-pad_b}" class="tick">{_esc(_money(min_y))}</text>',
    ]
    legend = []
    for label, color, pts in points_by_series:
        path = " ".join(
            ("M" if i == 0 else "L") + f"{xy(pt)[0]:.1f},{xy(pt)[1]:.1f}"
            for i, pt in enumerate(pts)
        )
        lines.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5" />')
        legend.append(f'<span><i style="background:{color}"></i>{_esc(label)}</span>')
    lines.append("</svg>")
    lines.append('<div class="legend">' + "".join(legend) + "</div></div>")
    return "".join(lines)


def _compact_monthly_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    pick_months = {1, 6, 12, 18, 24, 30, 36}
    selected = [r for r in rows if int(float(r.get("t", 0) or 0)) in pick_months]
    table_rows = []
    for r in selected:
        table_rows.append(
            [
                _num(r.get("t")),
                _num(r.get("Adq_clientes")),
                _num(r.get("Clientes_activos")),
                _money(r.get("Ingresos")),
                _money(r.get("EBITDA")),
                _money(r.get("Caja")),
            ]
        )
    return _table(["Mes", "Adq.", "Clientes", "Ingresos", "EBITDA", "Caja"], table_rows)


def _portada(assessment: dict[str, Any] | None, output_dir: Path) -> str:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    verdict = (assessment or {}).get("verdict", "—")
    mode = (assessment or {}).get("valuation_mode", "—")
    rows = [
        ["Directorio de resultados", str(output_dir)],
        ["Generado", generated],
        ["Veredicto Due Diligence", verdict],
        ["Modo de valorización", mode],
    ]
    return _section(
        "Portada", _table(["Campo", "Valor"], rows)
    )


def _resumen_ejecutivo(
    growth: dict[str, Any] | None,
    valuation: dict[str, Any] | None,
    stoch_summary: dict[str, str] | None,
) -> str:
    kpis = []
    if valuation:
        kpis.append(_kpi("VAN determinista (DCF)", _money(valuation.get("van"))))
    if growth:
        kpis.append(_kpi("EBITDA total", _money(growth.get("total_ebitda"))))
        kpis.append(_kpi("Caja final", _money(growth.get("final_cash"))))
        kpis.append(
            _kpi("Adquisición total", _num(growth.get("total_acquisition")) + " clientes")
        )
    if stoch_summary:
        kpis.append(_kpi("VAN esperado (M4)", _money(stoch_summary.get("expected_van"))))
        kpis.append(_kpi("CVaR 5% (M4)", _money(stoch_summary.get("cvar_5"))))
    if not kpis:
        return _section("Resumen ejecutivo", "<p>Sin KPIs disponibles.</p>")
    body = _paragraph(_TEXT["subtitle"]) + '<div class="kpi-grid">' + "".join(kpis) + "</div>"
    return _section("Resumen ejecutivo", body)


def _m1_growth(
    growth: dict[str, Any] | None,
    optimized_rows: list[dict[str, str]],
    output_dir: Path,
) -> str:
    if not growth:
        return _section(
            "M1 — Plan determinista oficial",
            "<p>Artefacto <code>growth_plan_summary.json</code> no disponible.</p>",
        )
    channels = growth.get("enabled_channels") or []
    rows = [
        ["Estado del solver", growth.get("solver_status", "—")],
        ["Adquisición total (clientes)", _num(growth.get("total_acquisition"))],
        ["Ingresos totales", _money(growth.get("total_revenue"))],
        ["EBITDA total", _money(growth.get("total_ebitda"))],
        ["Caja final", _money(growth.get("final_cash"))],
        ["Caja mínima", _money(growth.get("minimum_cash"))],
        ["Vendedores máx.", _num(growth.get("max_sellers"))],
        ["Líderes máx.", _num(growth.get("max_leaders"))],
        ["Canales activos", ", ".join(channels) if channels else "—"],
    ]
    charts = _dashboard_image(output_dir)
    charts += _svg_chart(
        optimized_rows,
        title="Ingresos, EBITDA y caja mensual",
        series=[
            ("Ingresos", "Ingresos", "#2563EB"),
            ("EBITDA", "EBITDA", "#059669"),
            ("Caja", "Caja", "#D97706"),
        ],
    )
    charts += _svg_chart(
        optimized_rows,
        title="Adquisición y clientes activos",
        series=[
            ("Adquisición", "Adq_clientes", "#7C3AED"),
            ("Clientes activos", "Clientes_activos", "#0891B2"),
        ],
    )
    compact = _compact_monthly_table(optimized_rows)
    body = (
        _paragraph(_TEXT["deterministic"])
        + _table(["Métrica", "Valor"], rows)
        + charts
        + ("<h3>Tabla de aceleración</h3>" + compact if compact else "")
    )
    return _section(
        "M1 — Plan determinista oficial",
        body,
    )


def _m2_valuation(
    valuation: dict[str, Any] | None, unit_rows: list[dict[str, str]]
) -> str:
    if not valuation and not unit_rows:
        return _section(
            "M2 — Valorización y Unit Economics",
            "<p>Artefactos de valorización no disponibles.</p>",
        )
    body = ""
    if valuation:
        rows = [
            ["Método", valuation.get("method", "—")],
            ["VC invertido", _money(valuation.get("vc_invested"))],
            ["VAN", _money(valuation.get("van"))],
            ["VP flujos", _money(valuation.get("vp_flujos"))],
            ["Valor residual (VP)", _money(valuation.get("vr_pv"))],
            ["WACC anual (beta)", _num(valuation.get("beta_anual"), 4)],
            ["EBITDA anualizado", _money(valuation.get("ebitda_anualizado"))],
        ]
        body += "<h3>Valorización DCF</h3>" + _table(["Métrica", "Valor"], rows)
    if unit_rows:
        cols = list(unit_rows[0].keys())
        # Prefer the canonical 3-column unit_economics layout when present.
        display_cols = [c for c in ("Unit Economic", "Valor", "Unidad") if c in cols] or cols
        table_rows = [[r.get(c, "") for c in display_cols] for r in unit_rows]
        body += "<h3>Unit Economics</h3>" + _table(display_cols, table_rows)
    return _section("M2 — Valorización y Unit Economics", body)


def _format_item(item: Any) -> str:
    """Render a DD reason/recommendation that may be a str or a dict.

    Recommendations are dicts ``{id, severity_class, recommendation}``; blocking
    reasons are plain strings. Both degrade to ``str()`` for unknown shapes.
    """
    if isinstance(item, dict):
        text = item.get("recommendation") or item.get("message") or item.get("reason") or ""
        ident = item.get("id")
        return f"{ident} — {text}" if ident and text else (text or str(item))
    return str(item)


def _m3_due_diligence(dd: dict[str, Any] | None) -> str:
    if not dd:
        return _section(
            "M3 — Due Diligence",
            "<p>Artefacto <code>due_diligence_report.json</code> no disponible.</p>",
        )
    rows = [
        ["Veredicto", dd.get("verdict", "—")],
        ["Permite estocástico", "Sí" if dd.get("allows_stochastic") else "No"],
        ["Modo de valorización", dd.get("valuation_mode", "—")],
        ["Nivel de ajuste", dd.get("adjustment_level", "—")],
        ["Veredicto calibración", dd.get("calibration_verdict", "—")],
    ]
    body = _paragraph(_TEXT["dd"]) + _table(["Métrica", "Valor"], rows)

    blocking = dd.get("blocking_reasons") or []
    if blocking:
        body += "<h3>Motivos de bloqueo</h3><ul>"
        body += "".join(f"<li>{_esc(_format_item(r))}</li>" for r in blocking)
        body += "</ul>"

    recs = dd.get("adjustment_recommendations") or []
    if recs:
        body += "<h3>Recomendaciones de ajuste</h3><ul>"
        body += "".join(f"<li>{_esc(_format_item(r))}</li>" for r in recs)
        body += "</ul>"
    return _section("M3 — Due Diligence", body)


def _m4_status_note(assessment: dict[str, Any] | None) -> str:
    """Explain why M4 is absent when there is no stochastic summary."""
    intro = _paragraph(_TEXT["robustness"])
    stoch = (assessment or {}).get("stochastic")
    if not stoch:
        return intro + "<p>El análisis de robustez (M4) no se ejecutó en esta corrida.</p>"
    if stoch.get("ran") is False:
        reason = stoch.get("reason", "desconocido")
        return intro + (
            "<p>El análisis de robustez (M4) <strong>no se ejecutó</strong>. "
            f"Motivo: <code>{_esc(reason)}</code>. Modo de valorización: "
            f"<code>{_esc(stoch.get('valuation_mode', 'none'))}</code>.</p>"
        )
    status = stoch.get("status", "desconocido")
    return intro + (
        "<p>El análisis de robustez (M4) corrió pero no alcanzó solución óptima. "
        f"Estado del solver: <code>{_esc(status)}</code>. Reintentar con mayor "
        "<code>--stochastic-time-limit</code>.</p>"
    )


def _m4_stochastic(
    stoch_summary: dict[str, str] | None,
    saa: dict[str, Any] | None,
    assessment: dict[str, Any] | None,
) -> str:
    title = "M4 — Análisis de robustez (LHS)"
    if not stoch_summary:
        return _section(title, _m4_status_note(assessment))

    val_mode = (assessment or {}).get("valuation_mode", "—")
    s = stoch_summary
    rows = [
        ["Modo de valorización", val_mode],
        ["Estado SAA", (saa or {}).get("status", "—")],
        ["Escenarios SAA", _num((saa or {}).get("saa_scenario_count"))],
        ["Escenarios evaluación (ex-post)", _num(s.get("n_scenarios"))],
        ["CVaR alpha", s.get("cvar_alpha", "—")],
        ["VAN esperado", _money(s.get("expected_van"))],
        ["CVaR 5%", _money(s.get("cvar_5"))],
        ["VAN P5", _money(s.get("van_p5"))],
        ["VAN P10", _money(s.get("van_p10"))],
        ["VAN P50", _money(s.get("van_p50"))],
        ["VAN P90", _money(s.get("van_p90"))],
        ["Prob. VAN negativo", _pct(s.get("prob_van_negative"))],
        ["Clientes activos finales P50", _num(s.get("final_active_clients_p50"))],
        ["Runway mediano (P50)", _num(s.get("runway_month_p50"))],
        ["Gap de financiamiento esperado", _money(s.get("expected_funding_gap"))],
        ["Gap de financiamiento máximo", _money(s.get("max_funding_gap"))],
        ["Prob. caja bajo el piso", _pct(s.get("prob_cash_below_floor"))],
    ]
    note = (
        _paragraph(_TEXT["robustness"])
        + '<p class="note"><strong>Artefacto técnico:</strong> <code>saa_solution.json</code> '
        "documenta la estrategia SAA. No es el plan oficial; el plan oficial es determinista.</p>"
    )
    return _section(title, note + _table(["Métrica", "Valor"], rows))


def _artifacts_listing(output_dir: Path) -> str:
    rows = []
    for name in _ARTIFACT_FILES:
        present = (output_dir / name).exists()
        rows.append([name, "✓ disponible" if present else "— ausente"])
    return _section("Artefactos canónicos", _table(["Archivo", "Estado"], rows))


def _limitations_section() -> str:
    return _section("Limitaciones y alcance", _paragraph(_TEXT["limitations"]))


_STYLE = """
:root {
  --ink: #232019;
  --muted: #6f6a60;
  --line: #e6dfd4;
  --paper: #fffaf1;
  --card: #ffffff;
  --accent: #9d6b2f;
  --blue: #2563eb;
  --green: #059669;
  --warn: #d97706;
}
* { box-sizing: border-box; }
body {
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  margin: 0; color: var(--ink);
  background: linear-gradient(180deg, #f7f1e7 0%, #f8fafc 44%, #f3f4f6 100%);
}
.container { max-width: 1120px; margin: 0 auto; padding: 28px; }
.hero {
  padding: 34px 0 18px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 18px;
}
h1 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 38px; line-height: 1.05; margin: 0 0 8px;
}
.subtitle { color: var(--muted); margin: 0; max-width: 840px; font-size: 16px; }
section {
  background: rgba(255,255,255,.92); border: 1px solid var(--line);
  border-radius: 12px; padding: 22px 26px; margin: 18px 0;
  box-shadow: 0 12px 32px rgba(36, 28, 18, .07);
}
h2 {
  font-size: 21px; margin: 0 0 14px;
  border-bottom: 1px solid var(--line); padding-bottom: 10px;
}
h3 { font-size: 16px; color: #383226; margin: 20px 0 10px; }
.lead { color: #4d463b; font-size: 15px; line-height: 1.6; margin: 0 0 14px; }
.note {
  background: #fff7e6; border: 1px solid #f1d49d; border-radius: 8px;
  padding: 10px 12px; color: #4a3820;
}
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th, td {
  text-align: left; padding: 9px 10px; border-bottom: 1px solid #eee8dc;
  font-size: 13.5px; vertical-align: top;
}
th { background: #f4efe6; color: #3c352a; font-weight: 700; }
.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px; margin-top: 12px;
}
.kpi {
  background: linear-gradient(180deg, #fff 0%, #f9f5ed 100%);
  border: 1px solid var(--line); border-radius: 10px;
  padding: 16px; text-align: left;
}
.kpi-value { font-size: 22px; font-weight: 800; color: var(--accent); }
.kpi-label { font-size: 12px; color: var(--muted); margin-top: 5px; }
.figure { margin: 16px 0; }
.figure img { width: 100%; border-radius: 10px; border: 1px solid var(--line); }
figcaption { color: var(--muted); font-size: 12px; margin-top: 6px; }
.chart {
  margin: 16px 0; border: 1px solid var(--line); border-radius: 10px;
  padding: 12px; background: #fffdf9;
}
.chart svg { width: 100%; height: auto; display: block; }
.axis { stroke: #c9c0b3; stroke-width: 1; }
.zero { stroke-dasharray: 4 4; }
.tick { fill: var(--muted); font-size: 11px; }
.legend { display: flex; flex-wrap: wrap; gap: 12px; color: var(--muted); font-size: 12px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 999px; margin-right: 5px; }
code { background: #f1eadf; padding: 1px 5px; border-radius: 4px; font-size: 13px; }
footer { text-align: center; color: #8b8377; font-size: 12px; padding: 18px; }
@media print {
  body { background: #fff; }
  .container { max-width: none; padding: 12mm; }
  section { break-inside: avoid; box-shadow: none; }
  .hero { padding-top: 0; }
}
"""


def build_simple_report(output_dir: str | Path) -> Path:
    """Render ``report.html`` in ``output_dir`` from available flat artifacts.

    Idempotent: overwrites any existing report. Returns the report path.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    growth = _load_json(out / "growth_plan_summary.json")
    valuation = _load_json(out / "valuation_summary.json")
    dd = _load_json(out / "due_diligence_report.json")
    assessment = _load_json(out / "assessment_summary.json")
    saa = _load_json(out / "saa_solution.json")
    stoch_summary = _load_csv_first_row(out / "stochastic_summary.csv")
    unit_rows = _load_csv_rows(out / "unit_economics.csv")
    optimized_rows = _load_csv_rows(out / "optimized_results.csv")

    sections = [
        _portada(assessment, out),
        _resumen_ejecutivo(growth, valuation, stoch_summary),
        _m1_growth(growth, optimized_rows, out),
        _m2_valuation(valuation, unit_rows),
        _m3_due_diligence(dd),
        _m4_stochastic(stoch_summary, saa, assessment),
        _limitations_section(),
        _artifacts_listing(out),
    ]

    document = (
        "<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Adventure Capital — Reporte</title>"
        f"<style>{_STYLE}</style></head><body><div class=\"container\">"
        "<div class=\"hero\"><h1>Adventure Capital — Reporte de Valorización</h1>"
        f"<p class=\"subtitle\">{_esc(_TEXT['subtitle'])}</p></div>"
        + "".join(sections)
        + f"<footer>{_esc(_TEXT['footer'])}</footer>"
        "</div></body></html>"
    )

    report_path = out / REPORT_FILENAME
    report_path.write_text(document, encoding="utf-8")
    (out / REPORT_PRINT_FILENAME).write_text(document, encoding="utf-8")
    return report_path

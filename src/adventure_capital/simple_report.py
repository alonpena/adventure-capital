"""M5 — simple Spanish HTML report from canonical flat M4 artifacts.

This is the MVP delivery report. It deliberately does *not* depend on the
``standard_report`` package or on ``postprocessed_results``: it reads the
canonical flat artifacts written by the assessment flow and hand-builds a
single ``report.html``. Every input is optional — missing artifacts degrade to
an explanatory placeholder rather than an error, so the report renders for
completed, omitted, blocked and failed M4 states alike.

Artifacts consumed (all optional):
``growth_plan_summary.json``, ``valuation_summary.json``, ``unit_economics.csv``,
``due_diligence_report.json``, ``assessment_summary.json``,
``stochastic_summary.csv``, ``stochastic_diagnostics.json``, ``saa_solution.json``.
"""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

REPORT_FILENAME = "report.html"

# Canonical flat artifacts, in display order, for the closing file listing.
_ARTIFACT_FILES = [
    "growth_plan_summary.json",
    "valuation_summary.json",
    "unit_economics.csv",
    "due_diligence_report.json",
    "assessment_summary.json",
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
    return _section("Resumen ejecutivo", '<div class="kpi-grid">' + "".join(kpis) + "</div>")


def _m1_growth(growth: dict[str, Any] | None) -> str:
    if not growth:
        return _section(
            "M1 — Plan de Crecimiento Acelerado (determinista)",
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
    return _section(
        "M1 — Plan de Crecimiento Acelerado (determinista)",
        _table(["Métrica", "Valor"], rows),
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
    body = _table(["Métrica", "Valor"], rows)

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
    stoch = (assessment or {}).get("stochastic")
    if not stoch:
        return "<p>El análisis estocástico (M4) no se ejecutó en esta corrida.</p>"
    if stoch.get("ran") is False:
        reason = stoch.get("reason", "desconocido")
        return (
            "<p>El análisis estocástico (M4) <strong>no se ejecutó</strong>. "
            f"Motivo: <code>{_esc(reason)}</code>. Modo de valorización: "
            f"<code>{_esc(stoch.get('valuation_mode', 'none'))}</code>.</p>"
        )
    status = stoch.get("status", "desconocido")
    return (
        "<p>El análisis estocástico (M4) corrió pero no alcanzó solución óptima. "
        f"Estado del solver: <code>{_esc(status)}</code>. Reintentar con mayor "
        "<code>--stochastic-time-limit</code>.</p>"
    )


def _m4_stochastic(
    stoch_summary: dict[str, str] | None,
    saa: dict[str, Any] | None,
    assessment: dict[str, Any] | None,
) -> str:
    title = "M4 — Valorización Estocástica (SAA + CVaR)"
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
    return _section(title, _table(["Métrica", "Valor"], rows))


def _artifacts_listing(output_dir: Path) -> str:
    rows = []
    for name in _ARTIFACT_FILES:
        present = (output_dir / name).exists()
        rows.append([name, "✓ disponible" if present else "— ausente"])
    return _section("Artefactos canónicos", _table(["Archivo", "Estado"], rows))


_STYLE = """
body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0;
  color: #1a1a2e; background: #f4f6fb; }
.container { max-width: 960px; margin: 0 auto; padding: 24px; }
h1 { font-size: 28px; margin-bottom: 4px; }
.subtitle { color: #667; margin-top: 0; }
section { background: #fff; border-radius: 10px; padding: 20px 24px; margin: 16px 0;
  box-shadow: 0 1px 3px rgba(0,0,0,.08); }
h2 { font-size: 20px; border-bottom: 2px solid #e2e8f5; padding-bottom: 8px; }
h3 { font-size: 16px; color: #334; margin-top: 20px; }
table { width: 100%; border-collapse: collapse; margin-top: 8px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #eef; font-size: 14px; }
th { background: #f0f3fa; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px; margin-top: 8px; }
.kpi { background: #f0f3fa; border-radius: 8px; padding: 14px; text-align: center; }
.kpi-value { font-size: 20px; font-weight: 700; color: #2E86AB; }
.kpi-label { font-size: 12px; color: #667; margin-top: 4px; }
code { background: #eef; padding: 1px 5px; border-radius: 4px; font-size: 13px; }
footer { text-align: center; color: #99a; font-size: 12px; padding: 16px; }
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

    sections = [
        _portada(assessment, out),
        _resumen_ejecutivo(growth, valuation, stoch_summary),
        _m1_growth(growth),
        _m2_valuation(valuation, unit_rows),
        _m3_due_diligence(dd),
        _m4_stochastic(stoch_summary, saa, assessment),
        _artifacts_listing(out),
    ]

    document = (
        "<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Adventure Capital — Reporte</title>"
        f"<style>{_STYLE}</style></head><body><div class=\"container\">"
        "<h1>Adventure Capital — Reporte de Valorización</h1>"
        "<p class=\"subtitle\">Plan de Crecimiento Acelerado · Due Diligence · "
        "Valorización Estocástica</p>"
        + "".join(sections)
        + "<footer>Generado por Adventure Capital · reporte simple (M5)</footer>"
        "</div></body></html>"
    )

    report_path = out / REPORT_FILENAME
    report_path.write_text(document, encoding="utf-8")
    return report_path

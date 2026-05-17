"""HTML rendering for standard valuation reports."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _money(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"USD {float(value):,.0f}"


def _money_short(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"USD {value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"USD {value / 1_000:.1f}K"
    return f"USD {value:,.0f}"


def _number(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{float(value):,.0f}"


def _number_short(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{float(value):,.1f}"


def _percent(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{float(value) * 100:.1f}%"


def _smart_cell(value: Any, column_name: str = "") -> str:
    """Format a table cell value based on the column name hint."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if isinstance(value, str):
        return escape(value)
    column = (column_name or "").lower()
    if "%" in column or "porcent" in column or "margen" in column or "churn" in column or "arr" in column or "crecimi" in column:
        return _percent(value)
    if "ratio" in column or "múltiplo" in column or "multiplier" in column:
        return f"{float(value):.2f}×"
    if "fte" in column or "vendedores" in column or "líderes" in column or "lideres" in column:
        return f"{float(value):,.2f}"
    if "usd" in column or "valor" in column or "ingres" in column or "ebitda" in column or "costo" in column or "cac" in column or "plani" in column or "comercial" in column or "caja" in column or "valorización" in column or "base" in column:
        return _money_short(value)
    if "frecuencia" in column or "ticket" in column:
        return f"{float(value):,.2f}"
    if "#" in column or "adquisición" in column or "stock" in column or "servicios" in column or "cliente" in column:
        return _number(value)
    if isinstance(value, float):
        return f"{value:,.2f}"
    return _number(value)


_BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")


def _markdown_lite(value: str) -> Markup:
    """Convert ``**bold**`` markdown to safe HTML; escape everything else."""
    if value is None:
        return Markup("")
    parts: list[str] = []
    last_end = 0
    for match in _BOLD_PATTERN.finditer(value):
        parts.append(str(escape(value[last_end:match.start()])))
        parts.append(f"<strong>{escape(match.group(1))}</strong>")
        last_end = match.end()
    parts.append(str(escape(value[last_end:])))
    return Markup("".join(parts))


def render_report(output_dir: str | Path, *, filename: str = "report.html", pdf: bool = False) -> Path | dict[str, Path]:
    """Render report.html from report_data.json and optionally report.pdf."""
    out = Path(output_dir)
    report_data_path = out / "report_data.json"
    if not report_data_path.exists():
        raise FileNotFoundError("report_data.json not found. Build report data package first.")

    data = json.loads(report_data_path.read_text(encoding="utf-8"))
    css = (TEMPLATE_DIR / "styles.css").read_text(encoding="utf-8")
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.globals["money"] = _money
    env.globals["number"] = _number
    env.filters["money"] = _money
    env.filters["money_short"] = _money_short
    env.filters["number"] = _number
    env.filters["number_short"] = _number_short
    env.filters["percent"] = _percent
    env.filters["smart_cell"] = _smart_cell
    env.filters["markdown_lite"] = _markdown_lite
    template = env.get_template("report.html.j2")
    html = template.render(data=data, css=css)
    path = out / filename
    path.write_text(html, encoding="utf-8")

    if not pdf:
        return path

    pdf_path = out / "report.pdf"
    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover - import depends on optional backend health
        raise RuntimeError("PDF rendering requires WeasyPrint.") from exc
    HTML(filename=str(path), base_url=str(out)).write_pdf(str(pdf_path))
    return {"html": path, "pdf": pdf_path}

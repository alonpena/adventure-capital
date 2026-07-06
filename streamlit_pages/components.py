"""Reusable UI components, artifact readers, and download helpers.

Reads from workflow registry (``outputs/instances/``, ``outputs/executions/``)
and canonical flat artifacts. Postprocessed results are secondary — canonical
CSVs + JSONs are the primary source of truth (see ADR 0007, ADR 0008).
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

OUTPUTS_ROOT = Path("outputs")
INSTANCES_DIR = OUTPUTS_ROOT / "instances"
EXECUTIONS_DIR = OUTPUTS_ROOT / "executions"


def _instance_dir(instance_id: str) -> Path:
    return INSTANCES_DIR / instance_id


def _execution_dir(run_id: str) -> Path:
    return EXECUTIONS_DIR / run_id


# --------------------------------------------------------------------------- #
# Instance registry
# --------------------------------------------------------------------------- #


def list_instances() -> list[dict[str, Any]]:
    """Return metadata for all instances, newest first."""
    if not INSTANCES_DIR.exists():
        return []
    out = []
    for d in sorted(INSTANCES_DIR.iterdir(), reverse=True):
        meta = d / "metadata.json"
        if meta.exists():
            data: dict[str, Any] = json.loads(meta.read_text(encoding="utf-8"))
            data["_dir"] = str(d)
            out.append(data)
    return out


def get_instance(instance_id: str) -> dict[str, Any] | None:
    meta = _instance_dir(instance_id) / "metadata.json"
    if not meta.exists():
        return None
    data: dict[str, Any] = json.loads(meta.read_text(encoding="utf-8"))
    data["_dir"] = str(_instance_dir(instance_id))
    return data


def delete_instance(instance_id: str) -> None:
    import shutil

    path = _instance_dir(instance_id)
    if path.exists():
        shutil.rmtree(path)


def create_instance(config: dict[str, Any], *, name: str | None = None) -> dict[str, Any]:
    """Write a frozen config + metadata under outputs/instances/.

    Returns the metadata dict (id, name, config_hash, created_at).
    """
    import hashlib
    from datetime import datetime

    import yaml

    config_hash = hashlib.sha256(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=True).encode("utf-8")
    ).hexdigest()[:8]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    instance_id = f"inst_{stamp}_{config_hash}"
    display_name = name or instance_id

    inst_dir = INSTANCES_DIR / instance_id
    inst_dir.mkdir(parents=True, exist_ok=True)

    (inst_dir / "instance.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    metadata = {
        "id": instance_id,
        "name": display_name,
        "config_hash": config_hash,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (inst_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return metadata


def load_instance_config(instance_id: str) -> dict[str, Any] | None:
    cfg = _instance_dir(instance_id) / "instance.yaml"
    if not cfg.exists():
        return None
    import yaml

    return yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}


# --------------------------------------------------------------------------- #
# Execution registry
# --------------------------------------------------------------------------- #


def execution_path(run_id: str) -> Path:
    """Return the execution directory path for a run_id."""
    return EXECUTIONS_DIR / run_id


def list_executions() -> list[dict[str, Any]]:
    """Return execution records, newest first."""
    if not EXECUTIONS_DIR.exists():
        return []
    out = []
    for d in sorted(EXECUTIONS_DIR.iterdir(), reverse=True):
        rec = d / "execution.json"
        if rec.exists():
            data: dict[str, Any] = json.loads(rec.read_text(encoding="utf-8"))
            data["_dir"] = str(d)
            out.append(data)
    return out


def get_execution(run_id: str) -> dict[str, Any] | None:
    rec = _execution_dir(run_id) / "execution.json"
    if not rec.exists():
        return None
    data: dict[str, Any] = json.loads(rec.read_text(encoding="utf-8"))
    data["_dir"] = str(_execution_dir(run_id))
    return data


def run_execution(
    instance_id: str,
    *,
    name: str | None = None,
    run_stochastic: bool = True,
) -> dict[str, Any]:
    """Thin wrapper around workflow_registry.run_execution.

    Returns the execution record.
    """
    from adventure_capital.workflow_registry import run_execution as _registry_run

    return _registry_run(instance_id, name=name, run_stochastic=run_stochastic)


# --------------------------------------------------------------------------- #
# Artifact readers — canonical (flat CSVs + JSONs under execution dir)
# --------------------------------------------------------------------------- #


def _exec_path(run_id: str) -> Path | None:
    rec = get_execution(run_id)
    if rec is None:
        return None
    return _execution_dir(run_id)


def canonical_csv(run_id: str, filename: str) -> pd.DataFrame | None:
    """Read a canonical CSV from an execution directory."""
    exe = _exec_path(run_id)
    if exe is None:
        return None
    path = exe / filename
    if not path.exists():
        return None
    return pd.read_csv(path)


def canonical_json(run_id: str, filename: str) -> dict[str, Any] | None:
    """Read a canonical JSON from an execution directory."""
    exe = _exec_path(run_id)
    if exe is None:
        return None
    path = exe / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def canonical_text(run_id: str, filename: str) -> str | None:
    """Read a plain text file from an execution directory."""
    exe = _exec_path(run_id)
    if exe is None:
        return None
    path = exe / filename
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def report_html_exists(run_id: str) -> bool:
    """Check if report.html exists (simple or standard)."""
    exe = _exec_path(run_id)
    if exe is None:
        return False
    return (exe / "report.html").exists()


def report_html_path(run_id: str) -> Path | None:
    """Get path to report.html if it exists."""
    exe = _exec_path(run_id)
    if exe is None:
        return None
    p = exe / "report.html"
    return p if p.exists() else None


# --------------------------------------------------------------------------- #
# Postprocessed readers (derived view, ADR 0007) — secondary fallback
# --------------------------------------------------------------------------- #

POSTPROCESSED = "postprocessed_results"


def _postprocessed_root(run_id: str) -> Path | None:
    exe = _exec_path(run_id)
    if exe is None:
        return None
    return exe / POSTPROCESSED


def postprocessed_json(run_id: str, subfolder: str, filename: str) -> dict[str, Any] | None:
    root = _postprocessed_root(run_id)
    if root is None:
        return None
    path = root / subfolder / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def postprocessed_csv(run_id: str, subfolder: str, filename: str) -> pd.DataFrame | None:
    root = _postprocessed_root(run_id)
    if root is None:
        return None
    path = root / subfolder / filename
    if not path.exists():
        return None
    return pd.read_csv(path)


# --------------------------------------------------------------------------- #
# Smart readers — try canonical first, then postprocessed
# --------------------------------------------------------------------------- #


def require_execution(st) -> str | None:
    """Get run_id from session_state, or show a guard message."""
    run_id = st.session_state.get("current_run_id")
    if not run_id:
        st.info("Sin caso seleccionado. Elige una ejecución en el panel lateral "
                "o crea una en el Gestor de instancias.")
        return None
    rec = get_execution(run_id)
    if rec is None:
        st.warning(f"La ejecución `{run_id}` ya no está en el registro. "
                   "Selecciona otra en el panel lateral.")
        return None
    return run_id


# --------------------------------------------------------------------------- #
# Presentation helpers
# --------------------------------------------------------------------------- #

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

STATUS_TONE: dict[str, str] = {
    "completed": "ok",
    "failed": "bad",
    "blocked": "warn",
    "pending": "muted",
}

STAGE_LABELS: dict[str, str] = {
    "M1_DETERMINISTIC": "Plan determinista",
    "M2_VALUATION": "Valoración",
    "M3_DUE_DILIGENCE": "Due diligence",
    "M4_STOCHASTIC": "Análisis de escenarios",
    "M5_REPORT": "Reporte",
}

STAGE_SHORT: dict[str, str] = {
    "M1_DETERMINISTIC": "M1",
    "M2_VALUATION": "M2",
    "M3_DUE_DILIGENCE": "M3",
    "M4_STOCHASTIC": "M4",
    "M5_REPORT": "M5",
}

# Glifos monocromos — identidad Memorando: estados discretos, sin semáforos emoji.
STATUS_ICON: dict[str, str] = {
    "completed": "●",
    "failed": "✕",
    "blocked": "◐",
    "pending": "○",
}

STATUS_LABELS: dict[str, str] = {
    "completed": "Completada",
    "failed": "Fallida",
    "blocked": "Bloqueada",
    "pending": "Pendiente",
}

# Etiquetas de negocio en español; el término técnico se conserva como caption.
VERDICT_LABELS: dict[str, str] = {
    "passed": "Aprobado",
    "passed_with_warnings": "Aprobado con advertencias",
    "requires_minor_adjustment": "Requiere ajuste menor",
    "requires_major_adjustment": "Requiere ajuste mayor",
    "rejected_for_stochastic": "Rechazado para escenarios",
}

VALUATION_MODE_LABELS: dict[str, str] = {
    "final": "Final",
    "warning": "Preliminar",
    "diagnostic": "Diagnóstico",
    "none": "No ejecutado",
}

# Nombres canónicos de páginas — el router de app.py y cualquier página que
# navegue deben usar estas constantes (nunca strings sueltos: ya hubo un bug
# de navegación por un prefijo emoji desalineado).
PAGE_INSTANCES = "instancias"
PAGE_REPORT = "Informe ejecutivo"
PAGE_GROWTH = "Plan de crecimiento"
PAGE_VALUATION = "Valoración"
PAGE_DD = "Due diligence"
PAGE_STOCH = "Análisis de escenarios"
PAGE_ARTIFACTS = "Artefactos"

NAV_PAGES = [PAGE_REPORT, PAGE_GROWTH, PAGE_VALUATION, PAGE_DD, PAGE_STOCH, PAGE_ARTIFACTS]


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


def page_header(st, title: str, subtitle: str = "", run_id: str | None = None) -> None:
    """Render the page title with the current case context pinned top-right.

    Keeps the user oriented when navigating between drill-down pages
    (which execution am I looking at?) without repeating status boxes.
    """
    case_html = ""
    if run_id:
        rec = get_execution(run_id)
        if rec:
            name = rec.get("instance_name", rec.get("name", run_id))
            status = rec.get("status", "—")
            icon = STATUS_ICON.get(status, "○")
            status_label = STATUS_LABELS.get(status, status)
            config_hash = rec.get("config_hash", "")
            hash_html = f" · config <code>{config_hash}</code>" if config_hash else ""
            case_html = (
                f'<span class="case"><b>{name}</b><br/>'
                f'{icon} {status_label}{hash_html}<br/>'
                f'<code>{run_id}</code></span>'
            )
    st.markdown(
        f'<div class="ac-page-head">{case_html}'
        f'<div class="title">{title}</div>'
        f'<div class="subtitle">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def risk_band(st, title: str, items: list[tuple[str, str, str]]) -> None:
    """Render the Risk Band: grouped downside KPIs inside one visual band.

    ``items`` is a list of (label, value, sub) tuples.
    """
    cells = "".join(
        f'<div class="ac-kpi"><div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'<div class="sub">{sub}</div></div>'
        for label, value, sub in items
    )
    st.markdown(
        f'<div class="ac-riskband"><div class="band-title">{title}</div>'
        f'<div style="display:flex;gap:.6rem;flex-wrap:wrap;">'
        f'{cells}</div></div>',
        unsafe_allow_html=True,
    )


def source_caption(st, stage_key: str, *files: str) -> None:
    """Trazabilidad por bloque: qué artefactos alimentan lo que se muestra.

    Renderiza p. ej. ``Fuente: valuation_summary.json · M2 — Valoración``.
    """
    short = STAGE_SHORT.get(stage_key, stage_key)
    label = STAGE_LABELS.get(stage_key, "")
    names = ", ".join(files)
    st.markdown(
        f'<div class="ac-source">Fuente: {names} · {short} — {label}</div>',
        unsafe_allow_html=True,
    )


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


# --------------------------------------------------------------------------- #
# Download helpers
# --------------------------------------------------------------------------- #


def _excel_bytes(dfs: dict[str, pd.DataFrame]) -> bytes:
    """Write multiple DataFrames to an Excel workbook in memory."""
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        raise RuntimeError("openpyxl es requerido para descargar Excel. Agrega 'openpyxl' a tus dependencias.")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            # Truncate sheet name to Excel's 31-char limit
            sheet_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()


def download_excel_button(st, dfs: dict[str, pd.DataFrame], filename: str, label: str = "Descargar Excel") -> None:
    """Render a download button for an Excel workbook."""
    try:
        data = _excel_bytes(dfs)
    except RuntimeError as exc:
        st.warning(str(exc))
        return
    st.download_button(
        label=label,
        data=data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def download_pdf_button(st, run_id: str, label: str = "Descargar PDF") -> None:
    """Render a download button for report.pdf if it exists."""
    exe = _exec_path(run_id)
    if exe is None:
        return
    pdf_path = exe / "report.pdf"
    if not pdf_path.exists():
        st.info("PDF no disponible. Genera el reporte estándar primero.")
        return
    with pdf_path.open("rb") as f:
        st.download_button(
            label=label,
            data=f,
            file_name="report.pdf",
            mime="application/pdf",
        )


def download_html_button(st, run_id: str, label: str = "Descargar HTML") -> None:
    """Render a download button for report.html if it exists."""
    exe = _exec_path(run_id)
    if exe is None:
        return
    html_path = exe / "report.html"
    if not html_path.exists():
        st.info("HTML no disponible.")
        return
    with html_path.open("r", encoding="utf-8") as f:
        st.download_button(
            label=label,
            data=f,
            file_name="report.html",
            mime="text/html",
        )

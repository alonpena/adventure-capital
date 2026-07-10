"""Artefactos — trazabilidad de insumos y salidas de una ejecución.

Expone la cadena instancia → ejecución → artefacto que ya existe en disco
(``execution.json`` guarda ``instance_id`` y ``config_hash``): configuración
congelada, artefactos canónicos agrupados por etapa del pipeline y vista
derivada (``postprocessed_results/``, ADR 0007). Solo lectura del directorio
del run — nada se recalcula.
"""

from __future__ import annotations

from pathlib import Path

from streamlit_pages import components as C

# Catálogo estático: archivo → (etapa, descripción de negocio).
# Archivos fuera del catálogo se listan bajo "Otros" sin descripción.
_CATALOG: dict[str, tuple[str, str]] = {
    "config.yaml": ("INPUT", "Configuración congelada con la que corrió el pipeline"),
    "execution.json": ("INPUT", "Registro de la ejecución: instancia, hash y estado por etapa"),
    "optimized_results.csv": ("M1_DETERMINISTIC", "Serie mensual optimizada: adquisición, ingresos, EBITDA, caja"),
    "fixed_cashflow.csv": ("M1_DETERMINISTIC", "Plan Consensuado (meses 1–12, A_base fija)"),
    "model_instance.json": ("M1_DETERMINISTIC", "Instancia del modelo tal como la vio el solver"),
    "growth_plan_summary.json": ("M1_DETERMINISTIC", "Resumen del plan: estado del solver, totales, breakeven"),
    "breakeven_variables.csv": ("M1_DETERMINISTIC", "Variables en el mes de breakeven"),
    "summary.json": ("M1_DETERMINISTIC", "Resumen corto de la corrida"),
    "valuation_summary.json": ("M2_VALUATION", "VAN, VP de flujos, valor terminal y supuestos DCF"),
    "dcf_cashflow.csv": ("M2_VALUATION", "Flujo de caja descontado mensual"),
    "dcf_annual_summary.csv": ("M2_VALUATION", "DCF agregado por año"),
    "unit_economics.csv": ("M2_VALUATION", "LTV, CAC, LTV/CAC, payback"),
    "multiples_valuation.csv": ("M2_VALUATION", "Valorización por múltiplos de referencia"),
    "formula_trace.json": ("M2_VALUATION", "Trazabilidad de fórmulas: expresión, supuestos, limitaciones"),
    "sensitivity_wacc_multiple.csv": ("M2_VALUATION", "Sensibilidad WACC × múltiplo"),
    "sensitivity_variables.csv": ("M2_VALUATION", "Variables del análisis de sensibilidad"),
    "mapvalue.json": ("M2_VALUATION", "Datos del diagrama MapValue"),
    "due_diligence_report.json": ("M3_DUE_DILIGENCE", "Veredicto, hallazgos y recomendaciones de ajuste"),
    "due_diligence_report.md": ("M3_DUE_DILIGENCE", "Reporte de due diligence legible"),
    "assessment_summary.json": ("M3_DUE_DILIGENCE", "Decisión sobre M4: permite/bloquea y modo de valoración"),
    "calibration_report.json": ("M3_DUE_DILIGENCE", "Chequeos de calibración reutilizados como evidencia"),
    "calibration_report.md": ("M3_DUE_DILIGENCE", "Reporte de calibración legible"),
    "consistency_report.json": ("M3_DUE_DILIGENCE", "Chequeos de consistencia interna"),
    "stochastic_scenarios.csv": ("M4_STOCHASTIC", "Escenarios generados con VAN y variables realizadas"),
    "stochastic_summary.csv": ("M4_STOCHASTIC", "Estadísticos de la distribución (E[VAN], P50, CVaR)"),
    "stochastic_diagnostics.json": ("M4_STOCHASTIC", "Método, objetivo y diagnóstico del análisis"),
    "saa_solution.json": ("M4_STOCHASTIC", "Artefacto técnico SAA (no es el plan oficial)"),
    "stochastic_unit_economics.csv": ("M4_STOCHASTIC", "Unit economics por escenario"),
    "report_data.json": ("M5_REPORT", "Paquete de datos render-ready del reporte estándar"),
    "report.html": ("M5_REPORT", "Informe ejecutivo (documento oficial del caso)"),
    "report.pdf": ("M5_REPORT", "Informe ejecutivo en PDF"),
}

_STAGE_ORDER = ["INPUT", "M1_DETERMINISTIC", "M2_VALUATION", "M3_DUE_DILIGENCE",
                "M4_STOCHASTIC", "M5_REPORT", "OTHER"]

_STAGE_TITLES = {
    "INPUT": "Insumos y registro",
    "OTHER": "Otros archivos",
    **C.STAGE_LABELS,
}

_MIME = {
    ".csv": "text/csv",
    ".json": "application/json",
    ".html": "text/html",
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".yaml": "application/yaml",
    ".txt": "text/plain",
    ".png": "image/png",
}


def _size_label(n_bytes: int) -> str:
    if n_bytes >= 1_000_000:
        return f"{n_bytes / 1_000_000:.1f} MB"
    if n_bytes >= 1_000:
        return f"{n_bytes / 1_000:.0f} KB"
    return f"{n_bytes} B"


def render(st) -> None:
    run_id = C.require_execution(st)
    if run_id is None:
        st.title("Artefactos")
        return

    C.page_header(
        st,
        "Artefactos",
        "Cadena de trazabilidad del caso: configuración congelada, salidas por etapa y vista derivada.",
        run_id=run_id,
    )

    exe = C.get_execution(run_id) or {}
    exe_dir = C.execution_path(run_id)

    # ── Insumo congelado ─────────────────────────────────────────
    st.markdown("### Insumo del caso")
    i1, i2 = st.columns(2)
    with i1:
        C.kpi(st, "Instancia de origen", exe.get("instance_name", "—"),
              sub=exe.get("instance_id", ""))
    with i2:
        C.kpi(st, "Hash de configuración", exe.get("config_hash", "—"),
              sub="identifica el YAML congelado exacto")

    frozen = C.canonical_text(run_id, "config.yaml")
    if frozen:
        with st.expander("Configuración congelada (config.yaml)"):
            st.code(frozen, language="yaml")
    C.source_caption(st, "M1_DETERMINISTIC", "execution.json", "config.yaml")

    # ── Artefactos por etapa ─────────────────────────────────────
    st.markdown("### Artefactos por etapa")

    files = sorted(p for p in exe_dir.iterdir() if p.is_file() and not p.name.startswith("."))
    by_stage: dict[str, list[Path]] = {key: [] for key in _STAGE_ORDER}
    for path in files:
        stage = _CATALOG.get(path.name, ("OTHER", ""))[0]
        by_stage.setdefault(stage, []).append(path)

    for stage in _STAGE_ORDER:
        stage_files = by_stage.get(stage, [])
        if not stage_files:
            continue
        title = _STAGE_TITLES.get(stage, stage)
        short = C.STAGE_SHORT.get(stage, "")
        header = f"{short} · {title}" if short else title
        with st.expander(f"{header} ({len(stage_files)})", expanded=(stage == "M5_REPORT")):
            for path in stage_files:
                desc = _CATALOG.get(path.name, ("", ""))[1]
                c1, c2, c3, c4 = st.columns([3, 4, 1, 2])
                c1.markdown(f"`{path.name}`")
                c2.caption(desc or "Sin descripción registrada")
                c3.caption(_size_label(path.stat().st_size))
                c4.download_button(
                    "Descargar",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime=_MIME.get(path.suffix, "application/octet-stream"),
                    key=f"dl_{run_id}_{path.name}",
                )

    # ── Vista derivada (ADR 0007) ────────────────────────────────
    pp_dir = exe_dir / "postprocessed_results"
    if pp_dir.exists():
        st.markdown("### Vista derivada (postprocessed_results)")
        C.note(st, "Re-presentación por audiencia de los artefactos canónicos (ADR 0007). "
                   "No es fuente de verdad: nada se recalcula aquí.")
        for sub in sorted(p for p in pp_dir.iterdir() if p.is_dir()):
            sub_files = sorted(p for p in sub.iterdir() if p.is_file() and not p.name.startswith("."))
            with st.expander(f"{sub.name} ({len(sub_files)})"):
                for path in sub_files:
                    c1, c2, c3 = st.columns([5, 1, 2])
                    c1.markdown(f"`{path.name}`")
                    c2.caption(_size_label(path.stat().st_size))
                    c3.download_button(
                        "Descargar",
                        data=path.read_bytes(),
                        file_name=path.name,
                        mime=_MIME.get(path.suffix, "application/octet-stream"),
                        key=f"dl_{run_id}_pp_{sub.name}_{path.name}",
                    )

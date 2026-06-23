"""Informe Ejecutivo — primary client-facing deliverable.

Embeds ``report.html`` inline via ``st.components.v1.html()``. If the standard
report hasn't been generated yet, offers a button to build it. All data shown
matches what the drill-down tabs display — they read from the same canonical
artifacts.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_pages import components as C


def render(st) -> None:
    st.title("Informe Ejecutivo")
    st.caption("Reporte de valoración y plan de crecimiento — documento oficial del caso.")

    run_id = C.require_execution(st)
    if run_id is None:
        return

    exe = C.get_execution(run_id)
    if exe is None:
        return

    _render_instance_header(st, run_id, exe)
    _render_report_view(st, run_id)


# --------------------------------------------------------------------------- #
# Instance header
# --------------------------------------------------------------------------- #


def _render_instance_header(st, run_id: str, exe: dict) -> None:
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        name = exe.get("instance_name", exe.get("name", run_id))
        st.markdown(f"**Caso:** {name}")
        st.caption(f"Ejecución: `{run_id}`")
    with c2:
        status = exe.get("status", "—")
        icon = C.STATUS_ICON.get(status, "⚪")
        st.metric("Estado", f"{icon} {status}")
    with c3:
        stages = exe.get("stages", {})
        completed = sum(1 for s in stages.values() if s == "completed")
        total = len(stages)
        st.metric("Etapas completadas", f"{completed}/{total}")

    # Stage status badges
    stages = exe.get("stages", {})
    badges = []
    for stage_key in ["M1_DETERMINISTIC", "M2_VALUATION", "M3_DUE_DILIGENCE", "M4_STOCHASTIC", "M5_REPORT"]:
        label = C.STAGE_LABELS.get(stage_key, stage_key)
        state = stages.get(stage_key, "—")
        icon = C.STATUS_ICON.get(state, "⚪")
        badges.append(f"{icon} {label}")
    st.markdown(" | ".join(badges))


# --------------------------------------------------------------------------- #
# Report view — embed report.html inline
# --------------------------------------------------------------------------- #


def _render_report_view(st, run_id: str) -> None:
    report_path = C.report_html_path(run_id)

    if report_path is None:
        st.warning("El reporte no se ha generado aún para esta ejecución.")
        _render_build_report_section(st, run_id)
        return

    # Check if standard report (report_data.json exists) or simple
    report_data = C.canonical_json(run_id, "report_data.json")
    has_standard = report_data is not None

    if has_standard:
        st.success("Reporte estándar disponible")
    else:
        C.note(st, "Reporte simple disponible. Genera el reporte estándar para obtener el documento completo.")

    # Read and embed the report HTML
    html_content = report_path.read_text(encoding="utf-8")
    st.components.v1.html(html_content, height=800, scrolling=True)

    # Download buttons
    st.markdown("#### Descargar")
    d1, d2 = st.columns(2)
    with d1:
        C.download_html_button(st, run_id, label="📄 Descargar HTML")
    with d2:
        C.download_pdf_button(st, run_id, label="📕 Descargar PDF")

    if not has_standard:
        st.markdown("---")
        _render_build_report_section(st, run_id)


# --------------------------------------------------------------------------- #
# Build standard report
# --------------------------------------------------------------------------- #


def _render_build_report_section(st, run_id: str) -> None:
    st.markdown("#### Generar reporte estándar")
    C.note(st, "El reporte estándar incluye narrativa parametrizada, gráficos por servicio, "
               "matriz de sensibilidad WACC × múltiplo y diagrama MapValue. Requiere un documento YAML de narrativa.")

    doc_path = st.text_input(
        "Ruta del documento YAML de narrativa",
        value="reports/valuation-base.yaml",
        key="exec_report_doc_path",
    )

    if st.button("🚀 Generar reporte estándar", type="primary", key="build_std_report"):
        _build_standard_report(st, run_id, doc_path)


def _build_standard_report(st, run_id: str, doc_path: str) -> None:
    from adventure_capital.standard_report import build_report_data_package, render_report

    exe_dir = C.execution_path(run_id)
    if not exe_dir.exists():
        st.error(f"Directorio de ejecución no encontrado: {exe_dir}")
        return

    doc = Path(doc_path)
    if not doc.exists():
        st.error(f"Documento YAML no encontrado: {doc_path}")
        return

    with st.spinner("Construyendo paquete de datos del reporte…"):
        try:
            build_report_data_package(
                str(exe_dir),
                document_path=doc_path,
                blueprint_path="docs/report-blueprint.md",
            )
        except Exception as exc:
            st.error(f"Error construyendo paquete de datos: {exc}")
            return

    with st.spinner("Renderizando reporte HTML…"):
        try:
            render_report(str(exe_dir))
            st.success("Reporte estándar generado exitosamente.")
            st.rerun()
        except Exception as exc:
            st.error(f"Error renderizando reporte: {exc}")

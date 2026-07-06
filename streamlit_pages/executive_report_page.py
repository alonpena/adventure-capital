"""Informe Ejecutivo — primary client-facing deliverable.

Embeds ``report.html`` inline via ``st.components.v1.html()``. If the standard
report hasn't been generated yet, offers a button to build it. All data shown
matches what the drill-down tabs display — they read from the same canonical
artifacts.
"""

from __future__ import annotations

from pathlib import Path

from streamlit_pages import components as C


def render(st) -> None:
    run_id = C.require_execution(st)
    if run_id is None:
        st.title("Informe ejecutivo")
        return

    C.page_header(
        st,
        "Informe ejecutivo",
        "Documento oficial de valoración y plan de crecimiento del caso.",
        run_id=run_id,
    )
    _render_report_view(st, run_id)


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

    # Toolbar: downloads next to the document, no status boxes above it.
    exe_dir = C.execution_path(run_id)
    pdf_exists = (exe_dir / "report.pdf").exists()
    t1, t2, t3 = st.columns([1, 1, 4])
    with t1:
        C.download_html_button(st, run_id, label="Descargar HTML")
    with t2:
        if pdf_exists:
            C.download_pdf_button(st, run_id, label="Descargar PDF")
    with t3:
        hints = []
        if not pdf_exists:
            hints.append("PDF disponible tras generar el reporte estándar.")
        if not has_standard:
            hints.append("Reporte simple — genera el reporte estándar para el documento completo (abajo).")
        if hints:
            st.caption(" ".join(hints))

    # The document is the page: give it almost the full viewport.
    st.iframe(report_path, height=1100)
    C.source_caption(st, "M5_REPORT", "report.html")

    if not has_standard:
        with st.expander("Generar reporte estándar"):
            _render_build_report_section(st, run_id)


# --------------------------------------------------------------------------- #
# Build standard report
# --------------------------------------------------------------------------- #


def _render_build_report_section(st, run_id: str) -> None:
    C.note(st, "El reporte estándar incluye narrativa parametrizada, gráficos por servicio, "
               "matriz de sensibilidad WACC × múltiplo y diagrama MapValue. Requiere un documento YAML de narrativa.")

    doc_path = st.text_input(
        "Ruta del documento YAML de narrativa",
        value="reports/valuation-base.yaml",
        key="exec_report_doc_path",
    )

    if st.button("Generar reporte estándar", type="primary", key="build_std_report"):
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

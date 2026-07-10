"""Informe Ejecutivo — primary client-facing deliverable.

The page shows the *simple report* (``report.html``, built by
``simple_report.build_simple_report`` during every run) inline, and offers the
*standard report* (``standard_report.html`` + ``report.pdf``) as a separate,
downloadable artifact that can be generated on demand. The standard report
never overwrites the simple one.
"""

from __future__ import annotations

from pathlib import Path

from streamlit_pages import components as C

STANDARD_FILENAME = "standard_report.html"


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

    exe_dir = C.execution_path(run_id)
    _repair_legacy_layout(st, exe_dir)
    _render_simple_report(st, run_id, exe_dir)
    st.markdown("---")
    _render_standard_report_section(st, run_id, exe_dir)


# --------------------------------------------------------------------------- #
# Legacy repair — older runs where the standard report overwrote report.html
# --------------------------------------------------------------------------- #


def _repair_legacy_layout(st, exe_dir: Path) -> None:
    """If report.html holds the standard report, move it aside and rebuild the simple one."""
    report = exe_dir / "report.html"
    standard = exe_dir / STANDARD_FILENAME
    if not report.exists() or standard.exists():
        return
    head = report.read_text(encoding="utf-8", errors="ignore")[:4000]
    if 'class="section-tag"' not in head and "section-tag" not in head:
        return  # already the simple report
    report.rename(standard)
    try:
        from adventure_capital.simple_report import build_simple_report

        build_simple_report(exe_dir)
    except Exception as exc:
        st.warning(f"No se pudo regenerar el informe simple: {exc}")


# --------------------------------------------------------------------------- #
# Simple report — the executive document
# --------------------------------------------------------------------------- #


def _render_simple_report(st, run_id: str, exe_dir: Path) -> None:
    report_path = exe_dir / "report.html"

    if not report_path.exists():
        st.warning("El informe ejecutivo no se ha generado aún para esta ejecución.")
        if st.button("Generar informe ejecutivo", type="primary", key="build_simple_report"):
            from adventure_capital.simple_report import build_simple_report

            with st.spinner("Generando informe ejecutivo…"):
                try:
                    build_simple_report(exe_dir)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error generando el informe: {exc}")
        return

    t1, _ = st.columns([1, 5])
    with t1:
        C.download_html_button(st, run_id, label="Descargar informe (HTML)")

    C.embed_report_html(st, report_path, height=1100)
    C.source_caption(st, "M5_REPORT", "report.html")


# --------------------------------------------------------------------------- #
# Standard report — downloadable artifact, generated on demand
# --------------------------------------------------------------------------- #


def _render_standard_report_section(st, run_id: str, exe_dir: Path) -> None:
    st.markdown("### Reporte estándar")
    st.caption(
        "Documento extendido con narrativa parametrizada, gráficos por servicio, "
        "sensibilidad WACC × múltiplo y diagrama MapValue."
    )

    standard = exe_dir / STANDARD_FILENAME
    pdf = exe_dir / "report.pdf"

    if standard.exists():
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            C.download_html_button(
                st, run_id, label="Descargar estándar (HTML)", filename=STANDARD_FILENAME
            )
        with c2:
            if pdf.exists():
                C.download_pdf_button(st, run_id, label="Descargar estándar (PDF)")
        with st.expander("Ver reporte estándar"):
            C.embed_report_html(st, standard, height=1000)
        C.source_caption(st, "M5_REPORT", STANDARD_FILENAME)
        with st.expander("Regenerar reporte estándar"):
            _render_build_form(st, run_id, exe_dir)
    else:
        _render_build_form(st, run_id, exe_dir)


def _render_build_form(st, run_id: str, exe_dir: Path) -> None:
    default_doc_path = (
        "reports/gold-b2b-saas.yaml"
        if Path("reports/gold-b2b-saas.yaml").exists()
        else "reports/valuation-base.yaml"
    )
    doc_path = st.text_input(
        "Documento YAML de narrativa",
        value=default_doc_path,
        key="exec_report_doc_path",
    )
    if st.button("Generar reporte estándar", type="primary", key="build_std_report"):
        _build_standard_report(st, exe_dir, doc_path)


def _build_standard_report(st, exe_dir: Path, doc_path: str) -> None:
    from adventure_capital.standard_report import build_report_data_package, render_report

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

    with st.spinner("Renderizando reporte estándar…"):
        # WeasyPrint needs Homebrew's shared libraries on macOS.
        import os

        os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")
        try:
            render_report(str(exe_dir), filename=STANDARD_FILENAME, pdf=True)
        except Exception:
            # PDF backend (WeasyPrint) may be unavailable — keep the HTML.
            try:
                render_report(str(exe_dir), filename=STANDARD_FILENAME)
                st.info("Reporte estándar generado (PDF no disponible: requiere WeasyPrint).")
            except Exception as exc:
                st.error(f"Error renderizando reporte: {exc}")
                return
        else:
            st.success("Reporte estándar generado (HTML + PDF).")
        st.rerun()

"""Adventure Capital Streamlit UI — drill-down tabs for the Executive Report.

Read-only views over generated artifacts. The authoritative client-facing
deliverable is ``report.html`` (Informe Ejecutivo), embedded via iframe in
:mod:`~streamlit_pages.executive_report_page`. Drill-down pages read the same
canonical CSVs and JSONs that feed the report — they never recompute model,
valuation, due-diligence, or stochastic logic.
"""

"""Build Report Data Package files from existing core artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from adventure_capital.standard_report.charts import generate_figures
from adventure_capital.standard_report.document import load_document
from adventure_capital.standard_report.narrative import build_all_narratives
from adventure_capital.standard_report.sensitivity import write_derived_artifacts
from adventure_capital.standard_report.tables import build_all_tables
from adventure_capital.standard_report.validation import (
    REQUIRED_CORE_ARTIFACTS,
    validate_report_inputs,
    write_validation_report,
)


def _read_unit_economics(path: Path) -> dict[str, float]:
    df = pd.read_csv(path)
    if "Unit Economic" not in df.columns or "Valor" not in df.columns:
        return {}
    return {str(row["Unit Economic"]): float(row["Valor"]) for _, row in df.iterrows() if pd.notna(row["Valor"])}


def _build_summary(output_dir: Path) -> dict[str, Any]:
    optimized = pd.read_csv(output_dir / "optimized_results.csv")
    dcf_cashflow = pd.read_csv(output_dir / "dcf_cashflow.csv")
    annual = pd.read_csv(output_dir / "dcf_annual_summary.csv")
    multiples = pd.read_csv(output_dir / "multiples_valuation.csv")
    unit = _read_unit_economics(output_dir / "unit_economics.csv")

    summary = {
        "total_acquisition": float(optimized["Adq_clientes"].sum()),
        "total_revenue": float(optimized["Ingresos"].sum()),
        "total_ebitda": float(optimized["EBITDA"].sum()),
        "final_cash": float(optimized["Caja"].iloc[-1]),
        "minimum_cash": float(optimized["Caja"].min()),
        "last_year_revenue": float(annual["Ingresos"].iloc[-1]) if "Ingresos" in annual else None,
        "last_year_ebitda": float(annual["EBITDA"].iloc[-1]) if "EBITDA" in annual else None,
        "last_month_ebitda": float(dcf_cashflow["EBITDA"].iloc[-1]),
        "unit_economics": unit,
    }

    if "Valorización" in multiples.columns:
        for _, row in multiples.iterrows():
            summary[str(row["Método"])] = float(row["Valorización"])
    return summary


def _load_instance(instance_path: str | Path | None) -> dict[str, Any] | None:
    if instance_path is None:
        return None
    path = Path(instance_path)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else None


def build_report_data_package(
    input_dir: str | Path,
    *,
    document_path: str | Path,
    blueprint_path: str | Path = "docs/report-blueprint.md",
    schema_path: str | Path = "reports/schema/valuation-document.schema.yaml",
    instance_path: str | Path | None = None,
) -> dict[str, Path]:
    """Validate inputs and write report_data.json plus artifacts_manifest.json."""
    out = Path(input_dir)
    out.mkdir(parents=True, exist_ok=True)

    validation = validate_report_inputs(out, document_path, schema_path)
    if not validation.valid:
        write_validation_report(validation, out, document_path=document_path, schema_path=schema_path)
        raise ValueError("Report inputs are invalid. See report_validation.json.")

    document = load_document(document_path)
    instance = _load_instance(instance_path)
    created_at = datetime.now(timezone.utc).isoformat()
    summary = _build_summary(out)
    derived_paths = write_derived_artifacts(out, document)
    tables = build_all_tables(out, document, instance=instance)
    narratives = build_all_narratives(summary, tables, document)
    figure_paths = generate_figures(out, instance=instance, base_wacc=tables.get("wacc_base"))

    qualitative_present = bool(
        document.get("empresa", {}).get("descripcion")
        or document.get("empresa", {}).get("mision")
        or document.get("empresa", {}).get("vision")
        or document.get("target_market")
        or document.get("modelo_negocio")
        or document.get("cap_table")
        or document.get("inversion", {}).get("narrativa")
    )
    scope = "full" if qualitative_present else "ev_only"

    summary_json_path = out / "summary.json"
    valuation_data = {}
    if summary_json_path.exists():
        try:
            valuation_data = json.loads(summary_json_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    report_data = {
        "schema_version": "1.0",
        "created_at": created_at,
        "document": {
            "title": document.get("document", {}).get("title", "Informe de Valorización"),
            "company_name": document.get("document", {}).get("company_name") or document.get("empresa", {}).get("nombre", "Empresa Demo SpA"),
            "report_date": document.get("document", {}).get("report_date") or document.get("report", {}).get("date") or document.get("fecha_referencia", ""),
            "author": document.get("document", {}).get("author") or document.get("report", {}).get("author", "Adventure Capital"),
            "scope": scope,
        },
        "dcf": document.get("dcf", {}),
        "valuation": valuation_data,
        "summary": summary,
        "narrative": document,
        "tables": tables,
        "narratives": narratives,
        "source_artifacts": {name.removesuffix(".csv"): name for name in REQUIRED_CORE_ARTIFACTS},
        "derived_artifacts": {key: path.name for key, path in derived_paths.items()},
        "figures": {key: str(path.relative_to(out)) for key, path in figure_paths.items()},
        "sensitivity": {
            "method": document.get("sensitivity", {}).get("method", "calculation"),
            "include_ltv_cac_reference": document.get("sensitivity", {}).get("include_ltv_cac_reference", False),
        },
    }

    manifest = {
        "schema_version": "1.0",
        "created_at": created_at,
        "inputs": {
            "output_dir": str(out),
            "document": str(document_path),
            "blueprint": str(blueprint_path),
            "schema": str(schema_path),
            "instance": str(instance_path) if instance_path else None,
        },
        "artifacts": {
            "report_data": "report_data.json",
            "artifacts_manifest": "artifacts_manifest.json",
            **{name.removesuffix(".csv"): name for name in REQUIRED_CORE_ARTIFACTS},
            **{key: path.name for key, path in derived_paths.items()},
            **{f"figure_{key}": str(path.relative_to(out)) for key, path in figure_paths.items()},
        },
        "checks": validation.to_dict(),
    }

    report_data_path = out / "report_data.json"
    manifest_path = out / "artifacts_manifest.json"
    report_data_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return {"report_data": report_data_path, "artifacts_manifest": manifest_path}

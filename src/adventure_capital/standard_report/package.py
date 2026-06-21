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


def _optional_artifacts(out: Path) -> dict[str, str]:
    candidates = {
        "summary": "summary.json",
        "model_instance": "model_instance.json",
        "growth_plan_summary": "growth_plan_summary.json",
        "valuation_summary": "valuation_summary.json",
        "formula_trace": "formula_trace.json",
        "config": "config.yaml",
        "dashboard": "dashboard.png",
        "financial_report": "financial_report.md",
        "calibration_report_json": "calibration_report.json",
        "calibration_report_markdown": "calibration_report.md",
        "consistency_report": "consistency_report.json",
        "due_diligence_report_json": "due_diligence_report.json",
        "due_diligence_report_markdown": "due_diligence_report.md",
        "assessment_summary": "assessment_summary.json",
        "stochastic_scenarios": "stochastic_scenarios.csv",
        "stochastic_summary": "stochastic_summary.csv",
        "stochastic_breakeven": "stochastic_breakeven.csv",
    }
    return {key: filename for key, filename in candidates.items() if (out / filename).exists()}


def _stage_status(out: Path, validation_valid: bool) -> dict[str, str]:
    return {
        "instance": "passed" if (out / "model_instance.json").exists() else "missing",
        "deterministic": "passed" if (out / "optimized_results.csv").exists() else "missing",
        "valuation": "passed" if (out / "valuation_summary.json").exists() else "missing",
        "due_diligence": "passed" if (out / "due_diligence_report.json").exists() else "skipped",
        "stochastic_saa": "passed" if (out / "stochastic_summary.csv").exists() else "skipped",
        "monte_carlo": "passed" if (out / "stochastic_scenarios.csv").exists() else "skipped",
        "report_package": "passed" if validation_valid else "failed",
    }


def _artifact_audience() -> dict[str, str]:
    return {
        "optimized_results": "audit",
        "fixed_cashflow": "audit",
        "dcf_cashflow": "audit",
        "dcf_annual_summary": "entrepreneur",
        "multiples_valuation": "entrepreneur",
        "unit_economics": "entrepreneur",
        "summary": "entrepreneur",
        "model_instance": "audit",
        "growth_plan_summary": "entrepreneur",
        "valuation_summary": "entrepreneur",
        "formula_trace": "audit",
        "dashboard": "entrepreneur",
        "financial_report": "entrepreneur",
        "calibration_report_json": "audit",
        "calibration_report_markdown": "entrepreneur",
        "due_diligence_report_json": "audit",
        "due_diligence_report_markdown": "entrepreneur",
        "assessment_summary": "audit",
        "stochastic_scenarios": "audit",
        "stochastic_summary": "entrepreneur",
        "stochastic_breakeven": "entrepreneur",
        "report_data": "audit",
        "artifacts_manifest": "audit",
    }


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

    dd_json_path = out / "due_diligence_report.json"
    dd_data = {
        "verdict": "ok",
        "allows_stochastic": True,
        "calibration_verdict": "N/A",
        "summary": {"failing": 0, "structural": 0, "major": 0, "minor": 0, "warnings": 0},
        "findings": []
    }
    if dd_json_path.exists():
        try:
            loaded = json.loads(dd_json_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                dd_data.update(loaded)
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
        "due_diligence": dd_data,
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

    manifest_artifacts = {
        "report_data": "report_data.json",
        "artifacts_manifest": "artifacts_manifest.json",
        **{name.removesuffix(".csv"): name for name in REQUIRED_CORE_ARTIFACTS},
        **_optional_artifacts(out),
        **{key: path.name for key, path in derived_paths.items()},
        **{f"figure_{key}": str(path.relative_to(out)) for key, path in figure_paths.items()},
    }
    audience = _artifact_audience()
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
        "artifacts": manifest_artifacts,
        "checks": validation.to_dict(),
        "stage_status": _stage_status(out, validation.valid),
        "audience": {key: audience.get(key, "entrepreneur") for key in manifest_artifacts},
    }

    report_data_path = out / "report_data.json"
    manifest_path = out / "artifacts_manifest.json"
    report_data_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return {"report_data": report_data_path, "artifacts_manifest": manifest_path}

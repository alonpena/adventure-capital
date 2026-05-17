"""Validation for standard report inputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adventure_capital.standard_report.document import load_document
from adventure_capital.standard_report.schema import load_schema, validate_required_paths

REQUIRED_CORE_ARTIFACTS = [
    "optimized_results.csv",
    "fixed_cashflow.csv",
    "dcf_cashflow.csv",
    "dcf_annual_summary.csv",
    "multiples_valuation.csv",
    "unit_economics.csv",
]


@dataclass(frozen=True)
class ReportValidationResult:
    valid: bool
    missing_document_fields: list[str]
    missing_core_artifacts: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "missing_document_fields": self.missing_document_fields,
            "missing_core_artifacts": self.missing_core_artifacts,
        }


def validate_report_inputs(
    input_dir: str | Path,
    document_path: str | Path,
    schema_path: str | Path = "reports/schema/valuation-document.schema.yaml",
) -> ReportValidationResult:
    out = Path(input_dir)
    document = load_document(document_path)
    schema = load_schema(schema_path)
    missing_fields = validate_required_paths(document, schema)
    missing_artifacts = [name for name in REQUIRED_CORE_ARTIFACTS if not (out / name).exists()]
    return ReportValidationResult(
        valid=not missing_fields and not missing_artifacts,
        missing_document_fields=missing_fields,
        missing_core_artifacts=missing_artifacts,
    )


def write_validation_report(
    result: ReportValidationResult,
    output_dir: str | Path,
    *,
    document_path: str | Path,
    schema_path: str | Path,
) -> Path:
    path = Path(output_dir) / "report_validation.json"
    payload = {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "document_path": str(document_path),
        "schema_path": str(schema_path),
        **result.to_dict(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

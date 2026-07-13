"""Orchestrator for the calibration gate."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from adventure_capital.calibration.checks import CheckResult, collect_checks
from adventure_capital.calibration.suggestions import build_suggestion

DEFAULT_THRESHOLDS_PATH = Path("configs/calibration.yaml")
DEFAULT_DOCUMENT_PATH = Path("reports/valuation-base.yaml")
DEFAULT_SCHEMA_PATH = Path("reports/schema/valuation-document.schema.yaml")


@dataclass
class CalibrationVerdict:
    verdict: str  # "PASS" | "WARN" | "FAIL"
    total_checks: int
    passed: int
    warnings: int
    errors: int
    skipped: int
    checks: list[CheckResult] = field(default_factory=list)
    suggestions: dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    inputs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "created_at": self.created_at,
            "verdict": self.verdict,
            "summary": {
                "total_checks": self.total_checks,
                "passed": self.passed,
                "warnings": self.warnings,
                "errors": self.errors,
                "skipped": self.skipped,
            },
            "checks": [
                {**check.to_dict(), "suggestion": self.suggestions.get(check.id, "")}
                for check in self.checks
            ],
            "inputs": self.inputs,
        }


def _load_yaml(path: str | Path | None, fallback: Path) -> dict[str, Any]:
    target = Path(path) if path else fallback
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def _aggregate_verdict(results: list[CheckResult]) -> tuple[str, int, int, int, int]:
    passed = sum(1 for r in results if r.passed and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    errors = sum(1 for r in results if (not r.passed) and (not r.skipped) and r.severity == "error")
    warnings = sum(1 for r in results if (not r.passed) and (not r.skipped) and r.severity == "warning")
    if errors:
        verdict = "FAIL"
    elif warnings:
        verdict = "WARN"
    else:
        verdict = "PASS"
    return verdict, passed, warnings, errors, skipped


def run_calibration(
    output_dir: str | Path,
    *,
    instance_path: str | Path,
    document_path: str | Path | None = None,
    schema_path: str | Path | None = None,
    thresholds_path: str | Path | None = None,
    solver_status: str | None = "Optimal",
) -> CalibrationVerdict:
    """Run the calibration gate against an existing output directory.

    ``solver_status`` defaults to ``"Optimal"`` because the current pipeline
    doesn't persist the solver status after running; callers integrating
    inline can pass the actual status.
    """
    out = Path(output_dir)
    instance = _load_yaml(instance_path, Path("configs/base.yaml"))
    thresholds = _load_yaml(thresholds_path, DEFAULT_THRESHOLDS_PATH)
    document = Path(document_path) if document_path else DEFAULT_DOCUMENT_PATH
    schema = Path(schema_path) if schema_path else DEFAULT_SCHEMA_PATH

    results = collect_checks(
        output_dir=out,
        instance=instance,
        document_path=document,
        schema_path=schema,
        thresholds=thresholds,
        solver_status=solver_status,
    )
    suggestions = {result.id: build_suggestion(result, instance) for result in results}
    verdict, passed, warnings, errors, skipped = _aggregate_verdict(results)

    return CalibrationVerdict(
        verdict=verdict,
        total_checks=len(results),
        passed=passed,
        warnings=warnings,
        errors=errors,
        skipped=skipped,
        checks=results,
        suggestions=suggestions,
        created_at=datetime.now(timezone.utc).isoformat(),
        inputs={
            "output_dir": str(out),
            "instance": str(instance_path),
            "document": str(document),
            "schema": str(schema),
            "thresholds": str(thresholds_path) if thresholds_path else str(DEFAULT_THRESHOLDS_PATH),
        },
    )


def _severity_label(sev: str) -> str:
    return {"error": "🚫 Error", "warning": "⚠️ Warning", "info": "ℹ️ Info"}.get(sev, sev)


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.4g}"
    if isinstance(value, dict):
        return ", ".join(f"{k}={_format_value(v)}" for k, v in value.items())
    if isinstance(value, list):
        return ", ".join(_format_value(v) for v in value)
    return str(value)


def _markdown_report(verdict: CalibrationVerdict) -> str:
    badge = {"PASS": "✅ PASS", "WARN": "⚠️ WARN", "FAIL": "🚫 FAIL"}.get(verdict.verdict, verdict.verdict)
    lines = [
        "# Reporte de Calibración — Adventure Capital",
        "",
        f"**Veredicto**: {badge}",
        f"**Fecha**: {verdict.created_at}",
        "",
        "## Resumen",
        "",
        "| Total | Pasaron | Warnings | Errors | Saltados |",
        "|---|---|---|---|---|",
        f"| {verdict.total_checks} | {verdict.passed} | {verdict.warnings} | {verdict.errors} | {verdict.skipped} |",
        "",
    ]
    failing = [r for r in verdict.checks if not r.passed and not r.skipped]
    if failing:
        lines += ["## Cheques que fallaron", ""]
        for result in failing:
            suggestion = verdict.suggestions.get(result.id, "")
            lines += [
                f"### {result.id} · {result.name} — {_severity_label(result.severity)}",
                "",
                f"**Fórmula**: `{result.formula}`",
                "",
                f"**Valor**: {_format_value(result.value)}",
                "",
                f"**Umbral**: {_format_value(result.threshold)}",
                "",
                f"**Mensaje**: {result.message}",
                "",
                f"**Sugerencia**: {suggestion}" if suggestion else "",
                "",
            ]

    passing = [r for r in verdict.checks if r.passed and not r.skipped]
    if passing:
        lines += ["## Cheques que pasaron", ""]
        for result in passing:
            lines += [f"- **{result.id} · {result.name}** — {result.message}"]
        lines += [""]

    skipped = [r for r in verdict.checks if r.skipped]
    if skipped:
        lines += ["## Cheques saltados", ""]
        for result in skipped:
            lines += [f"- **{result.id} · {result.name}** — {result.message}"]
        lines += [""]

    lines += [
        "## Inputs",
        "",
        f"- Output dir: `{verdict.inputs.get('output_dir', '')}`",
        f"- Instance: `{verdict.inputs.get('instance', '')}`",
        f"- Document: `{verdict.inputs.get('document', '')}`",
        f"- Thresholds: `{verdict.inputs.get('thresholds', '')}`",
        "",
    ]
    return "\n".join(lines)


def write_calibration_report(verdict: CalibrationVerdict, output_dir: str | Path) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "calibration_report.json"
    md_path = out / "calibration_report.md"
    json_path.write_text(
        json.dumps(verdict.to_dict(), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    md_path.write_text(_markdown_report(verdict), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}

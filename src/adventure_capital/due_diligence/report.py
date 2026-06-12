"""Due Diligence verdict aggregation and report generation.

Due Diligence is an iterative assess -> recommend -> rerun workflow. The verdict
carries decision fields the consultant/orchestrator acts on:

    allows_stochastic           run robust valuation? (only structural blocks)
    valuation_mode              final | warning | diagnostic | none
    adjustment_level            none | minor | major | structural
    blocking_reasons            structural reasons that block the run
    adjustment_recommendations  what to recalibrate before re-running
    rerun_recommended           should the consultant adjust and re-run?

A report is ALWAYS produced, including on rejection.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adventure_capital.due_diligence.rules import (
    MAJOR,
    MINOR,
    STRUCTURAL,
    WARNING,
    Finding,
)

PASSED = "passed"
PASSED_WITH_WARNINGS = "passed_with_warnings"
REQUIRES_MINOR_ADJUSTMENT = "requires_minor_adjustment"
REQUIRES_MAJOR_ADJUSTMENT = "requires_major_adjustment"
REJECTED_FOR_STOCHASTIC = "rejected_for_stochastic"

# verdict -> (valuation_mode, adjustment_level, rerun_recommended)
_VERDICT_POLICY: dict[str, tuple[str, str, bool]] = {
    PASSED: ("final", "none", False),
    PASSED_WITH_WARNINGS: ("final", "none", False),
    REQUIRES_MINOR_ADJUSTMENT: ("warning", "minor", True),
    REQUIRES_MAJOR_ADJUSTMENT: ("diagnostic", "major", True),
    REJECTED_FOR_STOCHASTIC: ("none", "structural", True),
}


def aggregate_verdict(findings: list[Finding]) -> str:
    """Worst failing finding determines the verdict (severity precedence)."""
    classes = {f.severity_class for f in findings if not f.passed}
    if STRUCTURAL in classes:
        return REJECTED_FOR_STOCHASTIC
    if MAJOR in classes:
        return REQUIRES_MAJOR_ADJUSTMENT
    if MINOR in classes:
        return REQUIRES_MINOR_ADJUSTMENT
    if WARNING in classes:
        return PASSED_WITH_WARNINGS
    return PASSED


@dataclass
class DueDiligenceVerdict:
    verdict: str
    findings: list[Finding] = field(default_factory=list)
    calibration_verdict: str | None = None
    liquidity_diagnostic: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    inputs: dict[str, str] = field(default_factory=dict)

    @property
    def allows_stochastic(self) -> bool:
        # Blocked only by structural rejection; financial risk stays diagnostic.
        return self.verdict != REJECTED_FOR_STOCHASTIC

    @property
    def valuation_mode(self) -> str:
        return _VERDICT_POLICY[self.verdict][0]

    @property
    def adjustment_level(self) -> str:
        return _VERDICT_POLICY[self.verdict][1]

    @property
    def rerun_recommended(self) -> bool:
        return _VERDICT_POLICY[self.verdict][2]

    def failing(self) -> list[Finding]:
        return [f for f in self.findings if not f.passed]

    @property
    def blocking_reasons(self) -> list[str]:
        return [f.message for f in self.failing() if f.severity_class == STRUCTURAL]

    @property
    def adjustment_recommendations(self) -> list[dict[str, str]]:
        return [
            {"id": f.id, "severity_class": f.severity_class, "recommendation": f.recommendation}
            for f in self.failing()
            if f.recommendation
        ]

    def to_dict(self) -> dict[str, Any]:
        failing = self.failing()
        return {
            "schema_version": "2.0",
            "created_at": self.created_at,
            "verdict": self.verdict,
            "allows_stochastic": self.allows_stochastic,
            "valuation_mode": self.valuation_mode,
            "adjustment_level": self.adjustment_level,
            "rerun_recommended": self.rerun_recommended,
            "blocking_reasons": self.blocking_reasons,
            "adjustment_recommendations": self.adjustment_recommendations,
            "calibration_verdict": self.calibration_verdict,
            "liquidity_diagnostic": self.liquidity_diagnostic,
            "summary": {
                "total_findings": len(self.findings),
                "failing": len(failing),
                "structural": sum(1 for f in failing if f.severity_class == STRUCTURAL),
                "major": sum(1 for f in failing if f.severity_class == MAJOR),
                "minor": sum(1 for f in failing if f.severity_class == MINOR),
                "warnings": sum(1 for f in failing if f.severity_class == WARNING),
            },
            "findings": [f.to_dict() for f in self.findings],
            "inputs": self.inputs,
        }


def build_verdict(
    findings: list[Finding],
    *,
    calibration_verdict: str | None = None,
    liquidity_diagnostic: dict[str, Any] | None = None,
    inputs: dict[str, str] | None = None,
) -> DueDiligenceVerdict:
    return DueDiligenceVerdict(
        verdict=aggregate_verdict(findings),
        findings=findings,
        calibration_verdict=calibration_verdict,
        liquidity_diagnostic=liquidity_diagnostic or {},
        created_at=datetime.now(timezone.utc).isoformat(),
        inputs=inputs or {},
    )


_VERDICT_BADGE = {
    PASSED: "✅ PASSED",
    PASSED_WITH_WARNINGS: "⚠️ PASSED WITH WARNINGS",
    REQUIRES_MINOR_ADJUSTMENT: "🔧 REQUIRES MINOR ADJUSTMENT",
    REQUIRES_MAJOR_ADJUSTMENT: "🛠️ REQUIRES MAJOR ADJUSTMENT",
    REJECTED_FOR_STOCHASTIC: "🚫 REJECTED FOR STOCHASTIC",
}

_CLASS_LABEL = {
    STRUCTURAL: "🚫 Estructural (bloqueante)",
    MAJOR: "🛠️ Mayor (elegibilidad venture)",
    MINOR: "🔧 Menor (riesgo de negocio)",
    WARNING: "⚠️ Aviso",
}


def _liquidity_section(diag: dict[str, Any]) -> list[str]:
    if not diag:
        return []
    return [
        "## Diagnóstico de liquidez",
        "",
        f"- Caja mínima: {diag.get('min_cash', 0):,.0f} (mes {diag.get('min_cash_month', '—')})",
        f"- Brecha máxima de financiamiento: {diag.get('max_funding_gap', 0):,.0f} "
        f"(mes {diag.get('max_funding_gap_month', '—')})",
        *(
            [f"- Alerta capital de trabajo: {diag.get('financing_gap_alert')}"]
            if diag.get("financing_gap_alert")
            else []
        ),
        f"- Mes de breakeven (EBITDA acumulado ≥ 0): {diag.get('breakeven_month', '—')}",
        f"- ¿La caja se vuelve negativa?: {'sí' if diag.get('cash_went_negative') else 'no'}",
        f"- ¿La caja se recupera al final?: {'sí' if diag.get('cash_recovers') else 'no'}",
        f"- Caja final: {diag.get('final_cash', 0):,.0f}",
        "",
        "_La liquidez es diagnóstica: no bloquea la valoración estocástica._",
        "",
    ]


def _markdown_report(verdict: DueDiligenceVerdict) -> str:
    badge = _VERDICT_BADGE.get(verdict.verdict, verdict.verdict)
    summary = verdict.to_dict()["summary"]
    lines = [
        "# Reporte de Due Diligence — Adventure Capital",
        "",
        f"**Veredicto**: {badge}",
        f"**Permite valoración estocástica**: {'sí' if verdict.allows_stochastic else 'no'}",
        f"**Modo de valoración**: {verdict.valuation_mode}",
        f"**Nivel de ajuste**: {verdict.adjustment_level}",
        f"**Re-ejecución recomendada**: {'sí' if verdict.rerun_recommended else 'no'}",
        f"**Veredicto de calibración (insumo)**: {verdict.calibration_verdict or '—'}",
        f"**Fecha**: {verdict.created_at}",
        "",
        "## Resumen",
        "",
        "| Hallazgos | Fallidos | Estructural | Mayor | Menor | Avisos |",
        "|---|---|---|---|---|---|",
        f"| {summary['total_findings']} | {summary['failing']} | {summary['structural']} "
        f"| {summary['major']} | {summary['minor']} | {summary['warnings']} |",
        "",
    ]

    lines += _liquidity_section(verdict.liquidity_diagnostic)

    failing = verdict.failing()
    if failing:
        lines += ["## Hallazgos", ""]
        for finding in failing:
            label = _CLASS_LABEL.get(finding.severity_class, finding.severity_class)
            lines += [
                f"### {finding.id} · {finding.name} — {label} ({finding.source})",
                "",
                f"**Qué pasó**: {finding.message}",
                "",
            ]
            if finding.recommendation:
                lines += [f"**Qué recalibrar**: {finding.recommendation}", ""]
            if finding.evidence:
                lines += [f"**Evidencia**: `{finding.evidence}`", ""]
    else:
        lines += ["Sin hallazgos materiales.", ""]

    if verdict.blocking_reasons:
        lines += ["## Motivos de bloqueo (estructural)", ""]
        lines += [f"- {reason}" for reason in verdict.blocking_reasons]
        lines += [""]

    lines += ["## Próximo paso", ""]
    if verdict.verdict == REJECTED_FOR_STOCHASTIC:
        lines += [
            "La instancia es estructuralmente inviable; la valoración estocástica **no corre**. "
            "Corregir los motivos de bloqueo y re-ejecutar el flujo.",
        ]
    elif verdict.verdict == REQUIRES_MAJOR_ADJUSTMENT:
        lines += [
            "El caso aún no cumple criterios de escala venture. La valoración estocástica puede "
            "correr de forma **diagnóstica** (no apta para decisión de inversión). Recalibrar los "
            "supuestos señalados y re-ejecutar.",
        ]
    elif verdict.verdict == REQUIRES_MINOR_ADJUSTMENT:
        lines += [
            "Riesgos de negocio acotados. La valoración estocástica corre marcada como "
            "**preliminar/advertencia**. Ajustar los puntos señalados y re-ejecutar para una "
            "valoración final.",
        ]
    else:
        lines += ["La valoración estocástica robusta puede correr normalmente."]
    lines += [""]

    lines += [
        "## Inputs",
        "",
        f"- Output dir: `{verdict.inputs.get('output_dir', '')}`",
        f"- Config: `{verdict.inputs.get('config', '')}`",
        "",
    ]
    return "\n".join(lines)


def write_due_diligence_report(
    verdict: DueDiligenceVerdict, output_dir: str | Path
) -> dict[str, Path]:
    """Always writes a JSON + Markdown report to ``output_dir``."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "due_diligence_report.json"
    md_path = out / "due_diligence_report.md"
    json_path.write_text(
        json.dumps(verdict.to_dict(), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    md_path.write_text(_markdown_report(verdict), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}

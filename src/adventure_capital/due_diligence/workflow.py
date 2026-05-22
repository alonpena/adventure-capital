"""Due Diligence orchestration (iterative assess -> recommend -> rerun).

``run_due_diligence`` wraps the deterministic baseline and reuses calibration as
evidence:

    pre-rules -> run_pipeline -> run_calibration -> synthesis + liquidity
              -> aggregate verdict (+ decision fields) -> always write report

``run_assessment`` is the full preliminary flow for report v1:

    due diligence -> if allows_stochastic: stochastic robust valuation
                  -> tag valuation_mode -> write assessment_summary.json

Never modifies ``pipeline.py`` or ``model.py``. A structural pre-rule failure
short-circuits the model run (it would be uninterpretable); a rejection report is
still produced.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from adventure_capital.calibration.report import run_calibration, write_calibration_report
from adventure_capital.due_diligence.report import (
    DueDiligenceVerdict,
    build_verdict,
    write_due_diligence_report,
)
from adventure_capital.due_diligence.rules import (
    STRUCTURAL,
    Finding,
    compute_liquidity_diagnostic,
    evaluate_pre_rules,
    evaluate_synthesis_rules,
    map_calibration_findings,
    resolve_thresholds,
)
from adventure_capital.pipeline import run_pipeline

DEFAULT_DD_CONFIG_PATH = Path("configs/due_diligence.yaml")


def _load_dd_config(path: str | Path | None) -> dict[str, Any]:
    target = Path(path) if path else DEFAULT_DD_CONFIG_PATH
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def _has_structural(findings: list[Finding]) -> bool:
    return any(f.severity_class == STRUCTURAL and not f.passed for f in findings)


def run_due_diligence(
    config: dict[str, Any],
    *,
    output_dir: str | Path,
    dd_config_path: str | Path | None = None,
    document_path: str | Path | None = None,
    schema_path: str | Path | None = None,
    calibration_thresholds_path: str | Path | None = None,
    verbose_solver: bool = False,
) -> dict[str, Any]:
    """Run the Due Diligence assessment for ``config``.

    Returns a dict with the :class:`DueDiligenceVerdict`, report artifact paths,
    and (when the model ran) the pipeline result and calibration verdict.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    dd_config = _load_dd_config(dd_config_path)
    thresholds = resolve_thresholds(dd_config)
    blocking_ids = dd_config.get("blocking_ids", ["C01"])
    major_ids = dd_config.get("major_ids", [])
    overrides = dd_config.get("calibration_overrides", {}) or {}

    inputs = {"output_dir": str(out), "config": "<in-memory>"}

    # 1. Pre-rules on the raw instance.
    pre_findings = evaluate_pre_rules(config, thresholds)

    # If the instance is structurally invalid, do not run the model.
    if _has_structural(pre_findings):
        verdict = build_verdict(pre_findings, calibration_verdict=None, inputs=inputs)
        artifacts = write_due_diligence_report(verdict, out)
        return {
            "verdict": verdict,
            "artifacts": artifacts,
            "pipeline": None,
            "calibration": None,
            "ran_model": False,
        }

    # 2. Deterministic baseline (reused, not duplicated).
    pipeline_result = run_pipeline(config, output_dir=str(out), verbose_solver=verbose_solver)
    optimized = pipeline_result["optimized_results"]
    solver_status = pipeline_result["solution"]["status"]

    # Persist the config so calibration can load the same instance.
    config_path = out / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    inputs["config"] = str(config_path)

    # 3. Calibration as an evidence source.
    calibration = run_calibration(
        out,
        instance_path=config_path,
        document_path=document_path,
        schema_path=schema_path,
        thresholds_path=calibration_thresholds_path,
        solver_status=solver_status,
    )
    write_calibration_report(calibration, out)
    calibration_findings = map_calibration_findings(
        calibration, blocking_ids=blocking_ids, major_ids=major_ids, overrides=overrides
    )

    # 4. Synthesis + liquidity diagnostic over deterministic outputs.
    synthesis_findings = evaluate_synthesis_rules(optimized, config, thresholds)
    liquidity = compute_liquidity_diagnostic(optimized)

    findings = pre_findings + synthesis_findings + calibration_findings
    verdict = build_verdict(
        findings,
        calibration_verdict=calibration.verdict,
        liquidity_diagnostic=liquidity,
        inputs=inputs,
    )
    artifacts = write_due_diligence_report(verdict, out)

    return {
        "verdict": verdict,
        "artifacts": artifacts,
        "pipeline": pipeline_result,
        "calibration": calibration,
        "ran_model": True,
    }


def _run_stochastic(config: dict[str, Any], output_dir: Path, *, time_limit: int) -> dict[str, Any]:
    """Run the stochastic Phase A + Phase B for an accepted case."""
    from adventure_capital.stochastic.evaluate import evaluate_strategy
    from adventure_capital.stochastic.model import build_saa_model, solve_saa_model
    from adventure_capital.stochastic.results import summarize_distribution, write_outputs
    from adventure_capital.stochastic.scenarios import (
        generate_evaluation_scenarios,
        generate_scenarios,
    )

    scenarios = generate_scenarios(config)
    bundle = build_saa_model(config, scenarios)
    solution = solve_saa_model(bundle, time_limit=time_limit)
    if solution["status"] != "Optimal":
        return {"ran": True, "status": solution["status"], "summary": None, "artifacts": None}

    eval_scenarios = generate_evaluation_scenarios(config)
    evaluation = evaluate_strategy(config, solution["strategy"], eval_scenarios)
    summary = summarize_distribution(evaluation)
    artifacts = write_outputs(evaluation, summary, output_dir)
    return {
        "ran": True,
        "status": solution["status"],
        "expected_objective": solution["expected_objective"],
        "summary": summary,
        "artifacts": artifacts,
    }


def run_assessment(
    config: dict[str, Any],
    *,
    output_dir: str | Path,
    run_stochastic: bool = True,
    stochastic_time_limit: int = 120,
    **dd_kwargs: Any,
) -> dict[str, Any]:
    """Full preliminary flow: due diligence -> (if allowed) stochastic valuation.

    Writes ``assessment_summary.json`` linking the deterministic baseline, the DD
    verdict + decision fields, and the stochastic result (tagged with the verdict's
    ``valuation_mode``). The stochastic run is skipped when the verdict is
    structurally rejected or when ``run_stochastic`` is False.
    """
    import json

    out = Path(output_dir)
    dd_result = run_due_diligence(config, output_dir=out, **dd_kwargs)
    verdict: DueDiligenceVerdict = dd_result["verdict"]

    stochastic: dict[str, Any] | None = None
    if run_stochastic and verdict.allows_stochastic:
        stochastic = _run_stochastic(config, out, time_limit=stochastic_time_limit)
        # The robustness study inherits the DD verdict's valuation mode.
        stochastic["valuation_mode"] = verdict.valuation_mode
    elif not verdict.allows_stochastic:
        stochastic = {"ran": False, "reason": "rejected_for_stochastic", "valuation_mode": "none"}

    assessment = {
        "verdict": verdict.verdict,
        "allows_stochastic": verdict.allows_stochastic,
        "valuation_mode": verdict.valuation_mode,
        "adjustment_level": verdict.adjustment_level,
        "rerun_recommended": verdict.rerun_recommended,
        "calibration_verdict": verdict.calibration_verdict,
        "blocking_reasons": verdict.blocking_reasons,
        "adjustment_recommendations": verdict.adjustment_recommendations,
        "liquidity_diagnostic": verdict.liquidity_diagnostic,
        "ran_model": dd_result["ran_model"],
        "stochastic": (
            None
            if stochastic is None
            else {k: v for k, v in stochastic.items() if k != "artifacts"}
        ),
        "due_diligence_report": str(dd_result["artifacts"]["markdown"]),
    }
    summary_path = out / "assessment_summary.json"
    summary_path.write_text(
        json.dumps(assessment, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )

    return {
        "due_diligence": dd_result,
        "verdict": verdict,
        "stochastic": stochastic,
        "assessment_summary": str(summary_path),
    }

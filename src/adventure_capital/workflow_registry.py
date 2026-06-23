"""Filesystem-backed registry for the MVP CLI workflow (instances + executions).

No database: instances and executions are plain directories under ``outputs/``.
An *instance* is a frozen model config plus metadata; an *execution* is one run
of the assessment flow (M1-M3, optionally M4, then the M5 report) against an
instance. IDs embed a timestamp and a short config hash for human readability.

    outputs/
      instances/<instance_id>/{instance.yaml, metadata.json}
      executions/<run_id>/{execution.json, config.yaml, ...canonical artifacts...}

The execution gate mirrors ADR-0009: M4 auto-runs on a clean verdict, prompts on
warnings/minor adjustment, and is blocked on major adjustment / structural
rejection. The DD verdict's ``valuation_mode`` tags the stochastic study.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from adventure_capital.simple_report import build_simple_report

OUTPUTS_ROOT = Path("outputs")
INSTANCES_DIR = "instances"
EXECUTIONS_DIR = "executions"

# DD verdicts that require an interactive confirmation before running M4.
_CONFIRM_VERDICTS = {"passed_with_warnings", "requires_minor_adjustment"}


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _config_hash(config: dict[str, Any]) -> str:
    blob = yaml.safe_dump(config, allow_unicode=True, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:8]


def _slug(name: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in name.strip()]
    out = "".join(keep)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "instance"


# --------------------------------------------------------------------------- #
# Instances
# --------------------------------------------------------------------------- #
def create_instance(
    config: dict[str, Any],
    *,
    name: str | None,
    config_source: str | None = None,
    root: str | Path = OUTPUTS_ROOT,
) -> dict[str, Any]:
    """Freeze ``config`` as a new instance and return its metadata."""
    config_hash = _config_hash(config)
    instance_id = f"inst_{_now_stamp()}_{config_hash}"
    display_name = name or _slug(config_source or instance_id)

    inst_dir = Path(root) / INSTANCES_DIR / instance_id
    inst_dir.mkdir(parents=True, exist_ok=True)
    (inst_dir / "instance.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    metadata = {
        "id": instance_id,
        "name": display_name,
        "config_hash": config_hash,
        "config_source": config_source,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (inst_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return metadata


def list_instances(root: str | Path = OUTPUTS_ROOT) -> list[dict[str, Any]]:
    base = Path(root) / INSTANCES_DIR
    if not base.exists():
        return []
    out = []
    for d in sorted(base.iterdir()):
        meta = d / "metadata.json"
        if meta.exists():
            out.append(json.loads(meta.read_text(encoding="utf-8")))
    return out


def get_instance(instance_id: str, root: str | Path = OUTPUTS_ROOT) -> dict[str, Any]:
    inst_dir = Path(root) / INSTANCES_DIR / instance_id
    meta = inst_dir / "metadata.json"
    if not meta.exists():
        raise FileNotFoundError(f"Instancia no encontrada: {instance_id}")
    data = json.loads(meta.read_text(encoding="utf-8"))
    data["_dir"] = str(inst_dir)
    return data


def load_instance_config(instance_id: str, root: str | Path = OUTPUTS_ROOT) -> dict[str, Any]:
    inst_dir = Path(root) / INSTANCES_DIR / instance_id
    cfg_path = inst_dir / "instance.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config de instancia no encontrada: {instance_id}")
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}


# --------------------------------------------------------------------------- #
# Executions
# --------------------------------------------------------------------------- #
def _execution_dir(run_id: str, root: str | Path = OUTPUTS_ROOT) -> Path:
    return Path(root) / EXECUTIONS_DIR / run_id


def _write_execution_json(run_dir: Path, record: dict[str, Any]) -> None:
    (run_dir / "execution.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )


def list_executions(root: str | Path = OUTPUTS_ROOT) -> list[dict[str, Any]]:
    base = Path(root) / EXECUTIONS_DIR
    if not base.exists():
        return []
    out = []
    for d in sorted(base.iterdir()):
        rec = d / "execution.json"
        if rec.exists():
            out.append(json.loads(rec.read_text(encoding="utf-8")))
    return out


def get_execution(run_id: str, root: str | Path = OUTPUTS_ROOT) -> dict[str, Any]:
    rec = _execution_dir(run_id, root) / "execution.json"
    if not rec.exists():
        raise FileNotFoundError(f"Ejecución no encontrada: {run_id}")
    return json.loads(rec.read_text(encoding="utf-8"))


def _stage_states(verdict: Any, stochastic: dict[str, Any] | None, wanted_m4: bool) -> dict[str, str]:
    if stochastic is None:
        m4 = "pending"
    elif stochastic.get("ran") is False:
        m4 = "blocked"
    elif stochastic.get("status") == "Optimal":
        m4 = "completed"
    elif stochastic.get("ran"):
        m4 = "failed"
    else:
        m4 = "pending" if not wanted_m4 else "blocked"
    return {
        "M1_DETERMINISTIC": "completed",
        "M2_VALUATION": "completed",
        "M3_DUE_DILIGENCE": getattr(verdict, "verdict", "unknown"),
        "M4_STOCHASTIC": m4,
        "M5_REPORT": "pending",
    }


def _overall_status(stages: dict[str, str]) -> str:
    m4 = stages["M4_STOCHASTIC"]
    if m4 == "failed":
        return "failed"
    if m4 == "blocked":
        return "blocked"
    return "completed"


def run_execution(
    instance_id: str,
    *,
    name: str | None = None,
    run_stochastic: bool = True,
    stochastic_time_limit: int | None = None,
    confirm: Any = None,
    root: str | Path = OUTPUTS_ROOT,
    **dd_kwargs: Any,
) -> dict[str, Any]:
    """Run the assessment flow for ``instance_id`` and persist an execution.

    ``confirm`` is an optional callable ``(verdict_str) -> bool`` consulted when
    the DD verdict needs confirmation before M4 (warnings / minor adjustment).
    When ``None``, confirmation defaults to allowed (used for ``--yes`` and
    non-interactive callers).
    """
    from adventure_capital.due_diligence.workflow import run_assessment, run_due_diligence

    instance = get_instance(instance_id, root)
    config = load_instance_config(instance_id, root)

    run_id = f"run_{_now_stamp()}_{instance['config_hash']}"
    run_dir = _execution_dir(run_id, root)
    run_dir.mkdir(parents=True, exist_ok=True)

    exec_name = name or f"{instance['name']} — {_now_stamp()}"

    # Probe the DD verdict first so we can apply the interactive M4 gate.
    decided_stochastic = run_stochastic
    if run_stochastic:
        probe = run_due_diligence(config, output_dir=run_dir, **dd_kwargs)
        verdict = probe["verdict"]
        if not verdict.allows_stochastic:
            decided_stochastic = False  # blocked by DD; run_assessment records reason.
        elif verdict.verdict in _CONFIRM_VERDICTS and confirm is not None:
            decided_stochastic = bool(confirm(verdict.verdict))

    result = run_assessment(
        config,
        output_dir=run_dir,
        run_stochastic=decided_stochastic,
        stochastic_time_limit=stochastic_time_limit,
        **dd_kwargs,
    )
    verdict = result["verdict"]
    stochastic = result.get("stochastic")

    stages = _stage_states(verdict, stochastic, wanted_m4=run_stochastic)

    record = {
        "id": run_id,
        "name": exec_name,
        "instance_id": instance_id,
        "instance_name": instance["name"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "config_hash": instance["config_hash"],
        "output_dir": str(run_dir),
        "status": _overall_status(stages),
        "stages": stages,
    }

    # M5 report from canonical flat artifacts.
    build_simple_report(run_dir)
    record["stages"]["M5_REPORT"] = "completed"
    _write_execution_json(run_dir, record)
    return record


def run_stochastic_only(
    run_id: str,
    *,
    stochastic_time_limit: int | None = None,
    root: str | Path = OUTPUTS_ROOT,
) -> dict[str, Any]:
    """Re-run M4 for an existing execution, then refresh its report + record."""
    from adventure_capital.due_diligence.report import (
        REJECTED_FOR_STOCHASTIC,
        REQUIRES_MAJOR_ADJUSTMENT,
    )
    from adventure_capital.due_diligence.workflow import _run_stochastic

    record = get_execution(run_id, root)
    run_dir = _execution_dir(run_id, root)
    config = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8")) or {}

    dd = json.loads((run_dir / "due_diligence_report.json").read_text(encoding="utf-8"))
    if not dd.get("allows_stochastic"):
        block = {
            REQUIRES_MAJOR_ADJUSTMENT: "requires_major_adjustment_recalibration_required",
            REJECTED_FOR_STOCHASTIC: "rejected_for_stochastic",
        }.get(dd.get("verdict"), dd.get("verdict"))
        record["stages"]["M4_STOCHASTIC"] = "blocked"
        record["status"] = "blocked"
        build_simple_report(run_dir)
        _write_execution_json(run_dir, record)
        return {**record, "m4_reason": block}

    if stochastic_time_limit is None:
        from adventure_capital.stochastic.defaults import M4_DEFAULTS

        block = config.get("stochastic", {}) or {}
        stochastic_time_limit = int(
            block.get("solver_time_limit", M4_DEFAULTS["solver_time_limit"])
        )

    stochastic = _run_stochastic(config, run_dir, time_limit=stochastic_time_limit)
    if stochastic.get("status") == "Optimal":
        record["stages"]["M4_STOCHASTIC"] = "completed"
        record["status"] = "completed"
    else:
        record["stages"]["M4_STOCHASTIC"] = "failed"
        record["status"] = "failed"

    build_simple_report(run_dir)
    record["stages"]["M5_REPORT"] = "completed"
    _write_execution_json(run_dir, record)
    return record


def regenerate_report(run_id: str, root: str | Path = OUTPUTS_ROOT) -> Path:
    """Regenerate ``report.html`` for an existing execution."""
    run_dir = _execution_dir(run_id, root)
    if not (run_dir / "execution.json").exists():
        raise FileNotFoundError(f"Ejecución no encontrada: {run_id}")
    return build_simple_report(run_dir)

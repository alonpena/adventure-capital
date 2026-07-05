"""Deterministic infeasibility diagnosis for the growth commitment (ADR 0014, plan §5).

When ``growth_commitment`` makes the deterministic MILP Infeasible, "Infeasible"
is itself a valid business result ("this structure does not support the x3
thesis") — never an error. This module runs a fixed, ordered sequence of eight
directed one-at-a-time relaxations (R1-R8) on top of the SAME config, and
reports which relaxations (individually) restore feasibility, so the business
reading is: "what specific lever would make the thesis fit."

Pattern: rebuild via a config->generate_instance->build_model->solve_model
pipeline for each relaxation (same precedent as ``scripts/growth_band_experiment.py``
and the core ``elastic_floor``/``diagnose_financing_gap`` in ``model.py``). Never
mutates the caller's config. Pure function ``diagnose_infeasibility(config) ->
dict``, SaaS-ready (config in, JSON-serializable dict out), plus a CLI.

Relaxations (fixed order, run independently — NOT cumulative):
    R1  hiring: h_v, h_l -> +inf (remove hiring friction)
    R2  advertising: I_max, A_ad_cap x10 (only if advertising channel active)
    R3  min_share -> 0 for all active channels (commercial mix unlocked)
    R4  churn x0.5 (recomputes delta/phi via generate_instance)
    R5  RRHH and g_adm -> 0 (fixed-cost counterfactual; informative only)
    R6  c_u -> 0 for all services (operating cost / margin counterfactual)
    R7  elastic working-capital floor (only if working_capital / liquidity policy
        implies a hard floor; pattern: model.py elastic_floor)
    R8  the commitment itself: multiple_3y -> 1.0 (no floor above C12)

Usage:
    uv run python scripts/diagnose_infeasibility.py --config path/to/config.yaml
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from adventure_capital.instance import generate_instance
from adventure_capital.model import build_model, solve_model


RELAXATIONS: list[tuple[str, str]] = [
    ("R1", "hiring friction removed (h_v, h_l -> +inf)"),
    ("R2", "advertising cap/investment x10 (only if advertising active)"),
    ("R3", "channel min_share -> 0 (commercial mix unlocked)"),
    ("R4", "churn x0.5 (retention doubled)"),
    ("R5", "RRHH and g_adm -> 0 (fixed-cost counterfactual, informative only)"),
    ("R6", "c_u -> 0 for all services (operating cost counterfactual)"),
    ("R7", "elastic working-capital floor (cash floor relaxed)"),
    ("R8", "growth_commitment.multiple_3y -> 1.0 (the thesis itself)"),
]

_DIAGNOSIS_TEXT: dict[str, str] = {
    "R1": "ritmo de contratación/onboarding insuficiente para la tesis",
    "R2": "canal publicitario saturado — tope de gasto/cap limita la tesis",
    "R3": "mix comercial rígido — los mínimos por canal impiden el mix necesario",
    "R4": "retención insuficiente: el stock decae más rápido de lo que se puede adquirir",
    "R5": "carga de costo fijo (solo informativo si no hay piso de caja activo)",
    "R6": "estructura de costo operativo / margen bruto",
    "R7": "capital insuficiente — brecha = valor del slack (runway)",
    "R8": "ninguna palanca alcanza: la tesis en sí es el binding (múltiplo máximo factible no calculado en v1)",
}


def _base_solve(config: dict[str, Any], *, time_limit: int | None) -> str:
    """Solve the unmodified config and return the solver status string."""
    inst = generate_instance(config)
    bundle = build_model(inst)
    solved = solve_model(bundle, time_limit=time_limit)
    return solved["status"]


def _relax_r1_hiring(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    hiring = cfg.get("hiring", {})
    if hiring.get("enabled", False):
        cfg["hiring"] = {**hiring, "enabled": False}
    return cfg


def _relax_r2_advertising(config: dict[str, Any]) -> dict[str, Any] | None:
    cfg = copy.deepcopy(config)
    channels = cfg.get("channels", {}) or {}
    advertising = channels.get("advertising", {})
    if not advertising.get("active", False):
        return None  # not applicable
    advertising = dict(advertising)
    advertising["I_max"] = float(advertising.get("I_max", 0.0)) * 10.0
    advertising["A_ad_cap"] = float(advertising.get("A_ad_cap", 0.0)) * 10.0
    channels = {**channels, "advertising": advertising}
    cfg["channels"] = channels
    return cfg


def _relax_r3_min_share(config: dict[str, Any]) -> dict[str, Any] | None:
    channels = config.get("channels", {}) or {}
    any_min_share = any(
        (channels.get(name, {}) or {}).get("min_share", 0.0) > 0.0
        for name in ("salesforce", "advertising", "third_party")
    )
    if not any_min_share:
        return None  # not applicable, nothing to relax
    cfg = copy.deepcopy(config)
    new_channels = {}
    for name, ch in channels.items():
        if isinstance(ch, dict) and "min_share" in ch:
            ch = {**ch, "min_share": 0.0}
        new_channels[name] = ch
    cfg["channels"] = new_channels
    return cfg


def _relax_r4_churn(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    for service in cfg["servicios"]:
        service["churn_anual"] = [max(0.0, c * 0.5) for c in service["churn_anual"]]
    return cfg


def _relax_r5_fixed_costs(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    cfg["g_adm"] = 0.0
    cfg["RRHH_mensual"] = [0.0 for _ in cfg["RRHH_mensual"]]
    return cfg


def _relax_r6_unit_cost(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    for service in cfg["servicios"]:
        service["c_u"] = 0.0
    return cfg


def _relax_r7_cash_floor(config: dict[str, Any]) -> dict[str, Any] | None:
    """Elastic cash floor: only applicable when a hard floor is active
    (working_capital.enabled or a liquidity_policy other than 'none')."""
    working_capital = config.get("working_capital", {}) or {}
    liquidity_policy = config.get("liquidity_policy", {}) or {}
    has_floor = working_capital.get("enabled", False) or liquidity_policy.get("type", "none") != "none"
    if not has_floor:
        return None
    cfg = copy.deepcopy(config)
    cfg["working_capital"] = {**working_capital, "enabled": False}
    cfg["liquidity_policy"] = {"type": "none"}
    return cfg


def _relax_r8_multiple(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    growth_commitment = dict(cfg.get("growth_commitment", {}))
    growth_commitment["multiple_3y"] = 1.0 + 1e-6
    cfg["growth_commitment"] = growth_commitment
    return cfg


_RELAXERS = {
    "R1": _relax_r1_hiring,
    "R2": _relax_r2_advertising,
    "R3": _relax_r3_min_share,
    "R4": _relax_r4_churn,
    "R5": _relax_r5_fixed_costs,
    "R6": _relax_r6_unit_cost,
    "R7": _relax_r7_cash_floor,
    "R8": _relax_r8_multiple,
}


def diagnose_infeasibility(
    config: dict[str, Any], *, time_limit: int | None = 60
) -> dict[str, Any]:
    """Run the fixed R1-R8 relaxation sequence and report which restore feasibility.

    Pure function: config in, JSON-serializable dict out. Never mutates ``config``.
    Intended for a config that is confirmed Infeasible with ``growth_commitment``
    enabled (callers typically check the base solve status first), but this also
    runs safely (and harmlessly) on an already-feasible config (every relaxation
    will simply report ``feasible: True`` alongside the base).
    """
    base_status = _base_solve(config, time_limit=time_limit)

    results: list[dict[str, Any]] = []
    for relax_id, description in RELAXATIONS:
        relaxer = _RELAXERS[relax_id]
        relaxed_config = relaxer(config)
        if relaxed_config is None:
            results.append(
                {
                    "relaxation": relax_id,
                    "description": description,
                    "applicable": False,
                    "feasible": None,
                    "objective": None,
                    "diagnosis": "no aplica a esta instancia (canal/piso no activo)",
                }
            )
            continue
        try:
            inst = generate_instance(relaxed_config)
            bundle = build_model(inst)
            solved = solve_model(bundle, time_limit=time_limit)
            status = solved["status"]
            feasible = status == "Optimal"
            objective = solved.get("objective") if feasible else None
        except Exception as exc:  # pragma: no cover - defensive, reported not raised
            status = f"ERROR:{type(exc).__name__}"
            feasible = False
            objective = None
        results.append(
            {
                "relaxation": relax_id,
                "description": description,
                "applicable": True,
                "status": status,
                "feasible": feasible,
                "objective": objective,
                "diagnosis": _DIAGNOSIS_TEXT[relax_id] if feasible else "no restaura factibilidad por sí sola",
            }
        )

    feasible_relaxations = [r["relaxation"] for r in results if r.get("feasible")]
    summary = {
        "base_status": base_status,
        "base_feasible": base_status == "Optimal",
        "relaxations": results,
        "feasible_relaxations": feasible_relaxations,
        "readable_summary": (
            f"Base status: {base_status}. "
            + (
                f"Relajaciones que restauran factibilidad por sí solas: {', '.join(feasible_relaxations)}."
                if feasible_relaxations
                else "Ninguna relajación individual restaura factibilidad — "
                "la combinación de restricciones (o la tesis misma, R8) es el binding."
            )
        ),
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to the YAML config.")
    parser.add_argument("--output", default=None, help="Path to write infeasibility_diagnosis.json.")
    parser.add_argument("--time-limit", type=int, default=60, help="CBC time limit per solve (s).")
    args = parser.parse_args()

    import yaml

    with open(args.config, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    diagnosis = diagnose_infeasibility(config, time_limit=args.time_limit)

    out_path = Path(args.output) if args.output else Path("infeasibility_diagnosis.json")
    out_path.write_text(json.dumps(diagnosis, indent=2, ensure_ascii=False), encoding="utf-8")
    print(diagnosis["readable_summary"])
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

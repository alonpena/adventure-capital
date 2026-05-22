"""Scenario generation for the stochastic extension.

Two modes (config-selectable, default ``saa``):

- ``saa``: draw ``scenario_count`` scenarios by sampling each uncertain
  multiplier from a triangular distribution. Equal probability ``1/N``.
- ``explicit``: business-facing named scenarios with explicit multipliers and
  probabilities, for interpretability and manual stress tests.

A :class:`Scenario` carries only multipliers/values relative to a base config;
``apply_scenario`` produces the concrete per-scenario config. Distributions are
configurable modeling assumptions, not empirically calibrated truth.
"""

from __future__ import annotations

import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

# Defaults used when the ``stochastic`` config block is absent or partial.
DEFAULT_DISTRIBUTIONS: dict[str, dict[str, float]] = {
    "churn_multiplier": {"min": 0.8, "mode": 1.0, "max": 1.3},
    "productivity_multiplier": {"min": 0.5, "mode": 1.0, "max": 1.2},
    "financing_multiplier": {"min": 0.7, "mode": 1.0, "max": 1.3},
    "wacc_relative": {"min": 0.6, "mode": 1.0, "max": 1.5},
}

DEFAULT_NAMED_SCENARIOS: list[dict[str, Any]] = [
    {"name": "base", "probability": 0.40},
    {"name": "commercial_downside", "probability": 0.15, "productivity_multiplier": 0.6},
    {"name": "retention_stress", "probability": 0.15, "churn_multiplier": 1.3},
    {"name": "funding_stress", "probability": 0.15, "financing_multiplier": 0.7},
    {"name": "upside", "probability": 0.15, "churn_multiplier": 0.85, "productivity_multiplier": 1.2},
]

# WACC is truncated to a sane band regardless of sampled relative factor.
_WACC_MIN = 0.05
_WACC_MAX = 0.90


@dataclass
class Scenario:
    """One realized draw of the uncertain parameters.

    Multipliers are relative to the base config (1.0 = no change). ``wacc_value``
    is an absolute annual discount rate; ``None`` means "keep base beta".
    """

    name: str
    probability: float
    churn_multiplier: float = 1.0
    productivity_multiplier: float = 1.0
    financing_multiplier: float = 1.0
    wacc_value: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def as_row(self) -> dict[str, Any]:
        return {
            "scenario": self.name,
            "probability": self.probability,
            "churn_multiplier": self.churn_multiplier,
            "productivity_multiplier": self.productivity_multiplier,
            "financing_multiplier": self.financing_multiplier,
            "wacc_value": self.wacc_value,
        }


def _stochastic_block(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("stochastic", {}) or {}


def _distributions(config: dict[str, Any]) -> dict[str, dict[str, float]]:
    configured = _stochastic_block(config).get("distributions", {}) or {}
    merged = deepcopy(DEFAULT_DISTRIBUTIONS)
    for key, value in configured.items():
        merged[key] = {**merged.get(key, {}), **value}
    return merged


def _triangular(rng: random.Random, spec: dict[str, float]) -> float:
    low, mode, high = float(spec["min"]), float(spec["mode"]), float(spec["max"])
    # random.triangular requires low <= high; mode is clamped into the range.
    return rng.triangular(low, high, min(max(mode, low), high))


def generate_scenarios(config: dict[str, Any], *, mode: str | None = None) -> list[Scenario]:
    """Build the Phase-A scenario sample for ``config``.

    ``mode`` overrides ``stochastic.scenario_generation.mode`` when provided.
    """
    block = _stochastic_block(config)
    gen = block.get("scenario_generation", {}) or {}
    resolved_mode = (mode or gen.get("mode", "saa")).lower()

    if resolved_mode == "explicit":
        return _explicit_scenarios(config)
    if resolved_mode == "saa":
        count = int(gen.get("scenario_count", 100))
        seed = int(gen.get("seed", 12345))
        return _saa_scenarios(config, count=count, seed=seed)
    raise ValueError(f"Unsupported scenario_generation.mode: {resolved_mode}")


def _saa_scenarios(config: dict[str, Any], *, count: int, seed: int) -> list[Scenario]:
    if count <= 0:
        raise ValueError("scenario_count must be > 0.")
    rng = random.Random(seed)
    dists = _distributions(config)
    base_beta = float(config["beta"])
    probability = 1.0 / count

    scenarios: list[Scenario] = []
    for k in range(count):
        churn = _triangular(rng, dists["churn_multiplier"])
        productivity = _triangular(rng, dists["productivity_multiplier"])
        financing = _triangular(rng, dists["financing_multiplier"])
        wacc_rel = _triangular(rng, dists["wacc_relative"])
        wacc = min(max(base_beta * wacc_rel, _WACC_MIN), _WACC_MAX)
        scenarios.append(
            Scenario(
                name=f"saa_{k:04d}",
                probability=probability,
                churn_multiplier=churn,
                productivity_multiplier=productivity,
                financing_multiplier=financing,
                wacc_value=wacc,
            )
        )
    return scenarios


def _explicit_scenarios(config: dict[str, Any]) -> list[Scenario]:
    named = _stochastic_block(config).get("named_scenarios") or DEFAULT_NAMED_SCENARIOS
    base_beta = float(config["beta"])
    total_prob = sum(float(item.get("probability", 0.0)) for item in named)
    if total_prob <= 0:
        raise ValueError("named_scenarios probabilities must sum to > 0.")

    scenarios: list[Scenario] = []
    for item in named:
        wacc_mult = item.get("wacc_multiplier")
        wacc_value = (
            min(max(base_beta * float(wacc_mult), _WACC_MIN), _WACC_MAX)
            if wacc_mult is not None
            else None
        )
        scenarios.append(
            Scenario(
                name=str(item["name"]),
                probability=float(item.get("probability", 0.0)) / total_prob,
                churn_multiplier=float(item.get("churn_multiplier", 1.0)),
                productivity_multiplier=float(item.get("productivity_multiplier", 1.0)),
                financing_multiplier=float(item.get("financing_multiplier", 1.0)),
                wacc_value=wacc_value,
            )
        )
    return scenarios


def generate_evaluation_scenarios(config: dict[str, Any]) -> list[Scenario]:
    """Build the larger Phase-B ex-post sample (always SAA sampling)."""
    block = _stochastic_block(config)
    eval_cfg = block.get("evaluation", {}) or {}
    count = int(eval_cfg.get("n_scenarios", 1000))
    seed = int(eval_cfg.get("seed", 999))
    return _saa_scenarios(config, count=count, seed=seed)


def apply_scenario(config: dict[str, Any], scenario: Scenario) -> dict[str, Any]:
    """Return a deep-copied config with the scenario's overrides applied.

    Churn multiplier scales each service's annual churn (clamped to [0,1]).
    ``meta`` and ``VC`` are scaled by their multipliers; ``beta`` is replaced by
    the scenario's absolute WACC value when present.
    """
    scenario_config = deepcopy(config)

    for service in scenario_config["servicios"]:
        service["churn_anual"] = [
            min(max(float(value) * scenario.churn_multiplier, 0.0), 1.0)
            for value in service["churn_anual"]
        ]

    scenario_config["meta"] = max(
        1e-9, float(scenario_config["meta"]) * scenario.productivity_multiplier
    )
    scenario_config["VC"] = float(scenario_config["VC"]) * scenario.financing_multiplier
    if scenario.wacc_value is not None:
        scenario_config["beta"] = float(scenario.wacc_value)

    return scenario_config

"""Scenario generation for the canonical M4 stochastic PCA.

Scenarios are drawn by Latin Hypercube Sampling (LHS) over the unit hypercube
and mapped to multipliers through a native triangular inverse-CDF. No SciPy.

Each :class:`Scenario` carries multipliers relative to the deterministic base
config (1.0 = no change):

- ``churn_multiplier``        — one global churn scaler;
- ``salesforce_efficiency``   — per-channel acquisition efficiency;
- ``advertising_efficiency``  — per-channel acquisition efficiency;
- ``third_party_efficiency``  — per-channel acquisition efficiency;
- ``wacc_multiplier``         — scales the base discount rate.

There is intentionally **no financing multiplier**: VC is fixed across
scenarios (ADR 0009). Distributions are modeling assumptions, not calibrated
truth. See ``src/adventure_capital/stochastic/defaults.py`` and the M4 plan.
"""

from __future__ import annotations

import math
import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from adventure_capital.stochastic.defaults import (
    M4_DEFAULTS,
    SCENARIO_DIMENSIONS,
)

# WACC is truncated to a sane band regardless of the sampled multiplier.
_WACC_MIN = 0.05
_WACC_MAX = 0.90


@dataclass
class Scenario:
    """One realized draw of the uncertain parameters."""

    name: str
    probability: float
    churn_multiplier: float = 1.0
    salesforce_efficiency: float = 1.0
    advertising_efficiency: float = 1.0
    third_party_efficiency: float = 1.0
    wacc_multiplier: float = 1.0
    meta: dict[str, Any] = field(default_factory=dict)

    def as_row(self) -> dict[str, Any]:
        return {
            "scenario": self.name,
            "probability": self.probability,
            "churn_multiplier": self.churn_multiplier,
            "salesforce_efficiency": self.salesforce_efficiency,
            "advertising_efficiency": self.advertising_efficiency,
            "third_party_efficiency": self.third_party_efficiency,
            "wacc_multiplier": self.wacc_multiplier,
        }


def triangular_icdf(p: float, low: float, mode: float, high: float) -> float:
    """Inverse CDF of the triangular distribution at quantile ``p`` in [0, 1].

    Native implementation (no SciPy):

        F_c = (c - a) / (b - a)
        if p < F_c:  x = a + sqrt(p * (b - a) * (c - a))
        else:        x = b - sqrt((1 - p) * (b - a) * (b - c))

    where ``a = low``, ``c = mode``, ``b = high``.
    """
    if not (low <= mode <= high):
        raise ValueError(f"Require low <= mode <= high, got {low}, {mode}, {high}.")
    if not (high > low):
        raise ValueError(f"Require high > low, got low={low}, high={high}.")
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Quantile p must be in [0, 1], got {p}.")

    span = high - low
    f_c = (mode - low) / span
    if p < f_c:
        return low + math.sqrt(p * span * (mode - low))
    return high - math.sqrt((1.0 - p) * span * (high - mode))


def latin_hypercube(n: int, d: int, rng: random.Random) -> list[list[float]]:
    """Return an ``n x d`` Latin Hypercube sample in [0, 1).

    Each column is stratified into ``n`` equal bins (one sample per bin), with
    the bin order independently permuted per dimension and a uniform jitter
    inside each bin.
    """
    if n <= 0:
        raise ValueError("n must be > 0.")
    if d <= 0:
        raise ValueError("d must be > 0.")

    columns: list[list[float]] = []
    for _ in range(d):
        perm = list(range(n))
        rng.shuffle(perm)
        columns.append([(perm[i] + rng.random()) / n for i in range(n)])

    return [[columns[j][i] for j in range(d)] for i in range(n)]


def _distributions(config: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Merge configured distribution overrides onto the M4 defaults."""
    configured = (config.get("stochastic", {}) or {}).get("distributions", {}) or {}
    merged = deepcopy(M4_DEFAULTS["distributions"])
    for key, value in configured.items():
        merged[key] = {**merged.get(key, {}), **value}
    return merged


def _build_scenarios(
    config: dict[str, Any], *, count: int, seed: int, prefix: str
) -> list[Scenario]:
    if count <= 0:
        raise ValueError("scenario count must be > 0.")
    rng = random.Random(seed)
    dists = _distributions(config)
    dims = SCENARIO_DIMENSIONS
    sample = latin_hypercube(count, len(dims), rng)
    probability = 1.0 / count

    scenarios: list[Scenario] = []
    for k, row in enumerate(sample):
        values: dict[str, float] = {}
        for col, dim in enumerate(dims):
            spec = dists[dim]
            values[dim] = triangular_icdf(
                row[col], float(spec["min"]), float(spec["mode"]), float(spec["max"])
            )
        scenarios.append(
            Scenario(
                name=f"{prefix}_{k:04d}",
                probability=probability,
                churn_multiplier=values["churn_multiplier"],
                salesforce_efficiency=values["salesforce_efficiency"],
                advertising_efficiency=values["advertising_efficiency"],
                third_party_efficiency=values["third_party_efficiency"],
                wacc_multiplier=values["wacc_multiplier"],
            )
        )
    return scenarios


def generate_scenarios(config: dict[str, Any]) -> list[Scenario]:
    """Build the SAA first-stage scenario sample (LHS)."""
    block = config.get("stochastic", {}) or {}
    count = int(block.get("saa_scenario_count", M4_DEFAULTS["saa_scenario_count"]))
    seed = int(block.get("seed_saa", M4_DEFAULTS["seed_saa"]))
    return _build_scenarios(config, count=count, seed=seed, prefix="saa")


def generate_evaluation_scenarios(config: dict[str, Any]) -> list[Scenario]:
    """Build the larger ex-post evaluation sample (LHS, independent seed)."""
    block = config.get("stochastic", {}) or {}
    count = int(
        block.get("evaluation_scenario_count", M4_DEFAULTS["evaluation_scenario_count"])
    )
    seed = int(block.get("seed_eval", M4_DEFAULTS["seed_eval"]))
    return _build_scenarios(config, count=count, seed=seed, prefix="eval")


def apply_scenario(config: dict[str, Any], scenario: Scenario) -> dict[str, Any]:
    """Return a deep-copied config with scenario churn/WACC applied.

    Channel efficiency multipliers are consumed directly by the model when
    realizing acquisition; they are not folded into the config here. VC is
    fixed across scenarios (no financing multiplier).
    """
    scenario_config = deepcopy(config)

    for service in scenario_config["servicios"]:
        service["churn_anual"] = [
            min(max(float(value) * scenario.churn_multiplier, 0.0), 1.0)
            for value in service["churn_anual"]
        ]

    base_beta = float(scenario_config["beta"])
    scenario_config["beta"] = min(
        max(base_beta * scenario.wacc_multiplier, _WACC_MIN), _WACC_MAX
    )
    return scenario_config

"""Backend-static configuration for the canonical M4 stochastic PCA.

These defaults are *internal* modeling assumptions, not user-facing form
inputs. They are intentionally not exposed in the Streamlit config form (see
the M4 plan and ADR 0009). Override only in code or tests when validating
alternative parameterizations.

Key invariants (ADR 0009):
- objective is ``cvar_van`` at ``cvar_alpha = 0.05``;
- VC is fixed across scenarios (no financing multiplier);
- efficiency multipliers are per *channel* (not per service);
- churn is a single global multiplier per scenario.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Canonical M4 backend configuration. Triangular specs are ``min/mode/max``
# multipliers relative to the deterministic base (1.0 = no change).
M4_DEFAULTS: dict[str, Any] = {
    "objective": "cvar_van",
    "cvar_alpha": 0.05,
    "saa_scenario_count": 100,
    "evaluation_scenario_count": 1000,
    "seed_saa": 12345,
    "seed_eval": 999,
    "distributions": {
        "churn_multiplier": {"min": 0.8, "mode": 1.0, "max": 1.3},
        "salesforce_efficiency": {"min": 0.6, "mode": 1.0, "max": 1.2},
        "advertising_efficiency": {"min": 0.5, "mode": 1.0, "max": 1.3},
        "third_party_efficiency": {"min": 0.7, "mode": 1.0, "max": 1.2},
        "wacc_multiplier": {"min": 0.7, "mode": 1.0, "max": 1.5},
    },
    "milestones": {"client_counts": [500, 1000, 2000]},
    "third_party_defaults": {"commission_periods": 6},
}

# The uncertain dimensions sampled per scenario, in a stable order. Used by the
# LHS generator to map columns of the unit hypercube to named multipliers.
SCENARIO_DIMENSIONS: tuple[str, ...] = (
    "churn_multiplier",
    "salesforce_efficiency",
    "advertising_efficiency",
    "third_party_efficiency",
    "wacc_multiplier",
)


def m4_defaults() -> dict[str, Any]:
    """Return a deep copy of :data:`M4_DEFAULTS` safe to mutate."""
    return deepcopy(M4_DEFAULTS)

"""Isolated two-stage stochastic optimization prototype.

Non-breaking extension layered on top of the deterministic growth-plan model.
The deterministic ``model.py`` and ``pipeline.py`` are untouched. See
``docs/STOCHASTIC_EXTENSION.md`` and ADR 0004.
"""

from adventure_capital.stochastic.evaluate import evaluate_strategy
from adventure_capital.stochastic.model import build_saa_model, solve_saa_model
from adventure_capital.stochastic.results import summarize_distribution
from adventure_capital.stochastic.scenarios import Scenario, generate_scenarios

__all__ = [
    "Scenario",
    "generate_scenarios",
    "build_saa_model",
    "solve_saa_model",
    "evaluate_strategy",
    "summarize_distribution",
]

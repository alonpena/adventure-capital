"""End-to-end smoke test for the M4 stochastic flow.

SAA first-stage solve -> ex-post LHS evaluation -> summary -> artifacts.
Uses a small horizon and scenario samples so CBC stays fast. Scenario-layer
and model-internal coverage live in ``test_stochastic_scenarios.py`` and
``test_stochastic_model.py``.
"""

from __future__ import annotations

from pathlib import Path

from adventure_capital.config import default_config
from adventure_capital.stochastic.evaluate import evaluate_strategy
from adventure_capital.stochastic.model import build_saa_model, solve_saa_model
from adventure_capital.stochastic.results import summarize_distribution, write_outputs
from adventure_capital.stochastic.scenarios import (
    generate_evaluation_scenarios,
    generate_scenarios,
)


def _smoke_config() -> dict:
    config = default_config()
    config["H"] = 14
    config["stochastic"] = {
        "saa_scenario_count": 6,
        "seed_saa": 7,
        "evaluation_scenario_count": 40,
        "seed_eval": 99,
    }
    return config


def test_saa_then_ex_post_lhs(tmp_path: Path) -> None:
    config = _smoke_config()

    scenarios = generate_scenarios(config)
    bundle = build_saa_model(config, scenarios)
    solution = solve_saa_model(bundle, time_limit=90)
    assert solution["status"] == "Optimal"
    assert solution["cvar_van"] is not None
    assert solution["expected_van"] is not None

    strategy = solution["strategy"]
    # First-stage plan is committed and non-negative for every service-period.
    assert all(value >= -1e-6 for value in strategy["A_plan"].values())

    eval_scenarios = generate_evaluation_scenarios(config)
    assert len(eval_scenarios) == 40
    evaluation = evaluate_strategy(config, strategy, eval_scenarios)
    assert len(evaluation) == 40
    assert {"VAN", "funding_gap", "breakeven_month", "runway_month",
            "final_active_clients"}.issubset(evaluation.columns)

    summary = summarize_distribution(evaluation, cvar_alpha=solution["cvar_alpha"])
    assert summary["n_scenarios"] == 40
    assert summary["van_p10"] <= summary["van_p50"] <= summary["van_p90"]
    assert summary["cvar_5"] <= summary["expected_van"] + 1e-6
    # Tolerancia flotante: en Linux la suma de pesos LHS da 1.0 + 2e-16.
    assert 0.0 - 1e-9 <= summary["prob_van_negative"] <= 1.0 + 1e-9
    assert summary["max_funding_gap"] >= summary["expected_funding_gap"] >= 0.0
    # Milestone probabilities are present for the backend-static client counts.
    for milestone in (500, 1000, 2000):
        assert 0.0 - 1e-9 <= summary[f"prob_hit_final_active_clients_{milestone}"] <= 1.0 + 1e-9

    artifacts = write_outputs(evaluation, summary, tmp_path, solution=solution)
    for key in ("scenarios", "summary", "diagnostics", "unit_economics", "saa_solution"):
        assert Path(artifacts[key]).exists()

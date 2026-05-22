"""Smoke tests for the isolated stochastic prototype (Phase A -> Phase B).

Uses a small horizon and scenario sample so CBC stays fast.
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
        "terminal_multiple": 1.0,
        "scenario_generation": {"mode": "saa", "scenario_count": 8, "seed": 7},
        "evaluation": {"n_scenarios": 50, "seed": 99},
    }
    return config


def test_saa_scenarios_are_reproducible() -> None:
    config = _smoke_config()
    first = generate_scenarios(config)
    second = generate_scenarios(config)
    assert len(first) == 8
    assert [s.churn_multiplier for s in first] == [s.churn_multiplier for s in second]
    assert abs(sum(s.probability for s in first) - 1.0) < 1e-9


def test_explicit_scenarios_normalize_probabilities() -> None:
    config = _smoke_config()
    scenarios = generate_scenarios(config, mode="explicit")
    assert {s.name for s in scenarios} >= {"base", "retention_stress", "funding_stress"}
    assert abs(sum(s.probability for s in scenarios) - 1.0) < 1e-9


def test_phase_a_then_phase_b(tmp_path: Path) -> None:
    config = _smoke_config()

    scenarios = generate_scenarios(config)
    bundle = build_saa_model(config, scenarios)
    solution = solve_saa_model(bundle, time_limit=60)
    assert solution["status"] == "Optimal"
    assert solution["expected_objective"] is not None

    strategy = solution["strategy"]
    # First-stage acquisition is committed for every service-period.
    assert all(value >= -1e-6 for value in strategy["A"].values())

    eval_scenarios = generate_evaluation_scenarios(config)
    evaluation = evaluate_strategy(config, strategy, eval_scenarios)
    assert len(evaluation) == 50
    assert {"VAN", "funding_gap", "breakeven_month"}.issubset(evaluation.columns)

    summary = summarize_distribution(evaluation)
    assert summary["n_scenarios"] == 50
    assert summary["van_p10"] <= summary["van_p50"] <= summary["van_p90"]
    assert 0.0 <= summary["prob_van_negative"] <= 1.0
    assert summary["max_funding_gap"] >= summary["expected_funding_gap"] >= 0.0

    artifacts = write_outputs(evaluation, summary, tmp_path)
    assert Path(artifacts["scenarios"]).exists()
    assert Path(artifacts["summary"]).exists()
    assert Path(artifacts["breakeven"]).exists()

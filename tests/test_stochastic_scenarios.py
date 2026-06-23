"""Unit tests for M4 scenario generation: triangular ICDF + LHS.

Model-independent (no CBC). See ADR 0009 and the M4 plan.
"""

from __future__ import annotations

import random

import pytest

from adventure_capital.config import default_config
from adventure_capital.stochastic.defaults import SCENARIO_DIMENSIONS
from adventure_capital.stochastic.scenarios import (
    generate_evaluation_scenarios,
    generate_scenarios,
    latin_hypercube,
    triangular_icdf,
)


# --- triangular ICDF -------------------------------------------------------


def test_triangular_icdf_bounds() -> None:
    assert triangular_icdf(0.0, 0.8, 1.0, 1.3) == pytest.approx(0.8)
    assert triangular_icdf(1.0, 0.8, 1.0, 1.3) == pytest.approx(1.3)


def test_triangular_icdf_at_mode_quantile() -> None:
    # F(mode) = (c - a) / (b - a); the ICDF there must return the mode.
    low, mode, high = 0.8, 1.0, 1.3
    f_c = (mode - low) / (high - low)
    assert triangular_icdf(f_c, low, mode, high) == pytest.approx(mode)


def test_triangular_icdf_monotone_and_in_range() -> None:
    low, mode, high = 0.5, 1.0, 1.3
    qs = [i / 20 for i in range(21)]
    xs = [triangular_icdf(q, low, mode, high) for q in qs]
    assert all(low - 1e-12 <= x <= high + 1e-12 for x in xs)
    assert all(b >= a for a, b in zip(xs, xs[1:]))


def test_triangular_icdf_median_is_central() -> None:
    # Symmetric triangle: median equals the mode.
    assert triangular_icdf(0.5, 0.0, 1.0, 2.0) == pytest.approx(1.0)


def test_triangular_icdf_validates_inputs() -> None:
    with pytest.raises(ValueError):
        triangular_icdf(0.5, 1.0, 0.5, 1.3)  # mode < low
    with pytest.raises(ValueError):
        triangular_icdf(0.5, 1.0, 1.0, 1.0)  # high not > low
    with pytest.raises(ValueError):
        triangular_icdf(1.5, 0.8, 1.0, 1.3)  # p out of [0, 1]


# --- Latin Hypercube -------------------------------------------------------


def test_lhs_shape_and_range() -> None:
    sample = latin_hypercube(10, 3, random.Random(0))
    assert len(sample) == 10
    assert all(len(row) == 3 for row in sample)
    assert all(0.0 <= v < 1.0 for row in sample for v in row)


def test_lhs_reproducible() -> None:
    a = latin_hypercube(20, 4, random.Random(42))
    b = latin_hypercube(20, 4, random.Random(42))
    assert a == b


def test_lhs_is_stratified() -> None:
    # Exactly one sample per equal-width bin in every column.
    n, d = 25, 5
    sample = latin_hypercube(n, d, random.Random(7))
    for col in range(d):
        bins = sorted(int(sample[row][col] * n) for row in range(n))
        assert bins == list(range(n))


def test_lhs_rejects_nonpositive() -> None:
    with pytest.raises(ValueError):
        latin_hypercube(0, 3, random.Random(0))
    with pytest.raises(ValueError):
        latin_hypercube(5, 0, random.Random(0))


# --- generated scenarios ---------------------------------------------------


def _config() -> dict:
    config = default_config()
    config["stochastic"] = {"saa_scenario_count": 16, "evaluation_scenario_count": 32}
    return config


def test_generated_scenarios_have_all_dimensions() -> None:
    scenarios = generate_scenarios(_config())
    assert len(scenarios) == 16
    row = scenarios[0].as_row()
    for dim in SCENARIO_DIMENSIONS:
        assert dim in row
    assert abs(sum(s.probability for s in scenarios) - 1.0) < 1e-9


def test_generated_scenarios_carry_channel_efficiencies() -> None:
    scenarios = generate_scenarios(_config())
    expected = {
        "churn_multiplier",
        "salesforce_efficiency",
        "advertising_efficiency",
        "third_party_efficiency",
        "wacc_multiplier",
    }
    assert expected == set(SCENARIO_DIMENSIONS)
    for s in scenarios:
        for dim in expected:
            assert getattr(s, dim) > 0.0


def test_no_financing_multiplier() -> None:
    # Financing/VC is fixed across scenarios (ADR 0009): the field must be gone.
    scenario = generate_scenarios(_config())[0]
    assert not hasattr(scenario, "financing_multiplier")
    assert "financing_multiplier" not in scenario.as_row()


def test_scenarios_are_reproducible() -> None:
    first = generate_scenarios(_config())
    second = generate_scenarios(_config())
    assert [s.as_row() for s in first] == [s.as_row() for s in second]


def test_evaluation_sample_independent_of_saa() -> None:
    config = _config()
    saa = generate_scenarios(config)
    ev = generate_evaluation_scenarios(config)
    assert len(ev) == 32
    # Different seeds -> first draws differ.
    assert saa[0].churn_multiplier != ev[0].churn_multiplier

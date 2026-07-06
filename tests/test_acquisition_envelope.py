"""ADR 0014 amendment — aggregate acquisition envelope (core, paired with the
growth_commitment floor).

Same horizon rationale as test_growth_commitment.py: the envelope binds months
13..H and the commitment checkpoints sit at 24/36, so these tests solve at H=36.
"""

from __future__ import annotations

import copy

import pulp
import pytest

from adventure_capital.config import default_config, load_config, validate_config
from adventure_capital.instance import compute_growth_suggestions, generate_instance
from adventure_capital.model import build_model, solve_model
from adventure_capital.results import extract_results
from adventure_capital.stochastic.model import build_saa_model, solve_saa_model
from adventure_capital.stochastic.scenarios import Scenario


_TIME_LIMIT = 60
TOL = 1e-3


def _base_config(**overrides) -> dict:
    config = load_config("configs/base.yaml")
    config["H"] = 36
    config["solver"] = {"name": "cbc", "time_limit": _TIME_LIMIT, "verbose": False}
    for key, value in overrides.items():
        config[key] = value
    return config


def _solve(config: dict) -> dict:
    inst = generate_instance(config)
    bundle = build_model(inst)
    solved = solve_model(bundle, time_limit=_TIME_LIMIT)
    return {"instance": inst, "bundle": bundle, "solved": solved}


def test_envelope_off_is_noop():
    """enabled: false (or absent block) -> bit-for-bit identical solve."""
    cfg_absent = _base_config()
    cfg_absent.pop("acquisition_envelope", None)
    result_absent = _solve(cfg_absent)

    cfg_off = _base_config(acquisition_envelope={"enabled": False})
    result_off = _solve(cfg_off)

    assert result_absent["solved"]["status"] == "Optimal"
    assert result_off["solved"]["status"] == "Optimal"
    assert result_absent["solved"]["objective"] == pytest.approx(
        result_off["solved"]["objective"], rel=1e-9
    )

    df_absent = extract_results(result_absent["instance"], result_absent["solved"])
    df_off = extract_results(result_off["instance"], result_off["solved"])
    assert (df_absent["Adq_clientes"] == df_off["Adq_clientes"]).all()
    assert (df_absent["Vendedores"] == df_off["Vendedores"]).all()


def test_envelope_path_construction():
    """U_t = max(U_plan, U_vc) * (1+delta_t); delta steps 0.25 -> 0.50 at t=25."""
    config = _base_config(
        acquisition_envelope={
            "enabled": True,
            "source": "max_plan_vc",
            "slack_year2": 0.25,
            "slack_year3": 0.50,
        }
    )
    inst = generate_instance(config)
    env = inst["acquisition_envelope"]
    assert env["enabled"] is True
    assert set(env["path"].keys()) == set(range(13, 37))
    for t in range(13, 37):
        delta = 0.25 if t <= 24 else 0.50
        expected = max(env["U_plan"][t], env["U_vc"][t]) * (1.0 + delta)
        assert env["path"][t] == pytest.approx(expected, rel=1e-9)
    # U_plan is the consensuated-plan momentum path: Abar12 * (1+g_mom)^(t-12).
    assert env["U_plan"][13] == pytest.approx(env["abar12"] * (1.0 + env["g_mom"]), rel=1e-9)
    # All bounds strictly positive on base.yaml (growing plan, positive stock).
    assert all(v > 0 for v in env["path"].values())


def test_envelope_respected_when_enabled():
    """Solution total acquisition <= U_t for every optimized month."""
    config = _base_config(
        acquisition_envelope={"enabled": True, "source": "max_plan_vc"},
    )
    result = _solve(config)
    assert result["solved"]["status"] == "Optimal"
    env = result["instance"]["acquisition_envelope"]
    df = extract_results(result["instance"], result["solved"])
    for t, u_t in env["path"].items():
        total_acq = float(df.loc[df["t"] == t, "Adq_clientes"].sum())
        assert total_acq <= u_t + TOL


def test_envelope_coexists_with_log_ceiling():
    """Envelope + legacy log ceiling both active -> tighter bound binds, still
    Optimal (documented coexistence, not an error)."""
    config = _base_config(
        acquisition_ceiling={"enabled": True, "target_stock_multiplier": 3.0, "slack": 0.15},
        acquisition_envelope={"enabled": True, "source": "max_plan_vc"},
    )
    result = _solve(config)
    assert result["solved"]["status"] == "Optimal"
    env = result["instance"]["acquisition_envelope"]
    log_ceiling = result["instance"]["log_ceiling"]
    slack = result["instance"]["ceiling_slack"]
    df = extract_results(result["instance"], result["solved"])
    for t in env["path"]:
        total_acq = float(df.loc[df["t"] == t, "Adq_clientes"].sum())
        tighter = min(env["path"][t], log_ceiling[t] * (1 + slack))
        assert total_acq <= tighter + TOL


def test_envelope_conflict_with_floor_is_business_diagnosis():
    """A custom envelope too small to ever reach the commitment checkpoints
    fails EARLY (instance generation) with the business-diagnosis message —
    not a raw solver Infeasible."""
    config = _base_config(
        growth_commitment={
            "enabled": True,
            "source": "vc_minimum",
            "multiple_3y": 3.0,
            "checkpoints": "annual",
        },
        acquisition_envelope={
            "enabled": True,
            "source": "custom",
            "custom_path": [0.1] * 24,
            "custom_justification": "synthetic conflict case for testing",
        },
    )
    with pytest.raises(ValueError, match="business diagnosis"):
        generate_instance(config)


def test_envelope_with_floor_solves():
    """Core methodology end-to-end: commitment floor + envelope, both on ->
    Optimal, checkpoints hold AND envelope holds simultaneously. The legacy log
    ceiling is disabled: the envelope supersedes it in the core methodology
    (coexistence is allowed but the exogenous ceiling's year-3 decay chokes the
    floor's front-load, see test_envelope_coexists_with_log_ceiling)."""
    config = _base_config(
        acquisition_ceiling={"enabled": False},
        growth_commitment={
            "enabled": True,
            "source": "vc_minimum",
            "multiple_3y": 3.0,
            "checkpoints": "annual",
        },
        acquisition_envelope={"enabled": True, "source": "max_plan_vc"},
    )
    result = _solve(config)
    assert result["solved"]["status"] == "Optimal"
    inst = result["instance"]
    df = extract_results(inst, result["solved"])
    targets = inst["growth_commitment"]["checkpoint_targets"]
    for cp, target in targets.items():
        stock = float(df.loc[df["t"] == cp, "Clientes_activos"].iloc[0])
        assert stock >= target - TOL
    for t, u_t in inst["acquisition_envelope"]["path"].items():
        total_acq = float(df.loc[df["t"] == t, "Adq_clientes"].sum())
        assert total_acq <= u_t + TOL


def test_parity_det_stoch_envelope():
    """Single deterministic scenario -> same V-path; envelope binds identically
    on the stochastic first-stage plan_total."""
    config = _base_config(
        acquisition_envelope={"enabled": True, "source": "max_plan_vc"},
    )
    det = _solve(config)
    assert det["solved"]["status"] == "Optimal"

    scenarios = [Scenario(name="base", probability=1.0)]
    stoch_bundle = build_saa_model(config, scenarios)
    stoch_solution = solve_saa_model(stoch_bundle, time_limit=_TIME_LIMIT)
    assert stoch_solution["status"] == "Optimal"

    det_v = {t: pulp.value(det["bundle"]["variables"]["V"][t]) for t in det["instance"]["T"]}
    stoch_v = stoch_solution["strategy"]["V"]
    for t in det["instance"]["T"]:
        assert stoch_v[t] == pytest.approx(det_v[t], abs=1e-6)

    # First-stage planned total acquisition respects U_t.
    env = det["instance"]["acquisition_envelope"]
    plan_total = stoch_bundle["variables"]["A_plan"]
    service_count = det["instance"]["S"]
    for t, u_t in env["path"].items():
        planned = sum(pulp.value(plan_total[(s, t)]) or 0.0 for s in range(service_count))
        assert planned <= u_t + TOL


def test_config_validation_envelope():
    """source enum, slack >= 0, custom_path length/values, justification, tp cap."""
    base = default_config()

    cfg = copy.deepcopy(base)
    cfg["acquisition_envelope"] = {"enabled": True, "source": "not_a_source"}
    with pytest.raises(ValueError, match="acquisition_envelope.source"):
        validate_config(cfg)

    cfg = copy.deepcopy(base)
    cfg["acquisition_envelope"] = {"enabled": True, "slack_year2": -0.1}
    with pytest.raises(ValueError, match="slack_year2"):
        validate_config(cfg)

    cfg = copy.deepcopy(base)
    cfg["acquisition_envelope"] = {"enabled": True, "source": "custom", "custom_path": None}
    with pytest.raises(ValueError, match="custom_path"):
        validate_config(cfg)

    cfg = copy.deepcopy(base)
    cfg["acquisition_envelope"] = {
        "enabled": True,
        "source": "custom",
        "custom_path": [10.0] * 3,  # wrong length: H - 12 values required
    }
    with pytest.raises(ValueError, match="custom_path"):
        validate_config(cfg)

    cfg = copy.deepcopy(base)
    cfg["acquisition_envelope"] = {
        "enabled": True,
        "source": "custom",
        "custom_path": [10.0] * (cfg["H"] - 12),
        "custom_justification": None,
    }
    with pytest.raises(ValueError, match="custom_justification"):
        validate_config(cfg)


def test_third_party_active_without_cap_raises():
    """third_party.active without A_tp_cap -> validation error (unbounded-path
    MVP fix); with the cap declared it validates and the cap is wired into the
    instance."""
    cfg = default_config()
    cfg["channels"]["third_party"] = {
        "active": True,
        "commission": 0.1,
        "min_share": 0.0,
        "max_share": 0.5,
    }
    with pytest.raises(ValueError, match="A_tp_cap"):
        validate_config(cfg)

    cfg["channels"]["third_party"]["A_tp_cap"] = 50
    validate_config(cfg)
    inst = generate_instance(cfg)
    assert inst["channels"]["third_party"]["A_tp_cap"] == 50.0


def test_envelope_exported_in_growth_suggestions():
    """growth_suggestions carries the auditable U_t derivation when enabled."""
    config = _base_config(
        acquisition_envelope={"enabled": True, "source": "max_plan_vc"},
    )
    suggestions = compute_growth_suggestions(config)
    env = suggestions["acquisition_envelope"]
    assert env["source"] == "max_plan_vc"
    assert set(env["U_t"].keys()) == {str(t) for t in range(13, 37)}
    assert env["slack_year2"] == 0.25 and env["slack_year3"] == 0.50

    config_off = _base_config()
    suggestions_off = compute_growth_suggestions(config_off)
    assert "acquisition_envelope" not in suggestions_off


def test_envelope_vc_path_uses_investment_thesis_multiple():
    config = _base_config(
        investment_thesis={
            "multiple": 4.0,
            "horizon_months": 36,
            "base_month": 12,
            "dd_revenue_gate_usd": 1_000_000,
            "interpolation": "geometric",
        },
        acquisition_ceiling={"enabled": False},
        growth_commitment={"enabled": True, "source": "vc_minimum", "checkpoints": "annual"},
        acquisition_envelope={"enabled": True, "source": "vc_minimum"},
    )
    inst = generate_instance(config)
    c12 = inst["growth_commitment"]["C12"]
    assert inst["growth_commitment"]["checkpoint_targets"][36] == pytest.approx(4.0 * c12)
    assert inst["acquisition_envelope"]["multiple_3y"] == pytest.approx(4.0)
    suggestions = compute_growth_suggestions(config)
    assert suggestions["investment_thesis"]["multiple"] == pytest.approx(4.0)


def test_demo_growth_core_profile_flags():
    config = load_config("configs/demo-growth-core.yaml")
    inst = generate_instance(config)
    assert inst["log_ceiling"] == {}
    assert inst["acquisition_envelope"]["enabled"] is True
    assert inst["acquisition_envelope"]["source"] == "vc_minimum"
    assert inst["acquisition_envelope"]["slack_year2"] == 0.0
    assert inst["acquisition_envelope"]["slack_year3"] == 0.0

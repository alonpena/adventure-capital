"""ADR 0014 — growth_commitment (investment-thesis floor) + hiring friction.

Horizon choice: the commitment checkpoints are at months 24/36, so these tests
solve at H=36 (not the usual H=14 ``_fast_config`` used by
``test_model_behavior.py``) — a shorter horizon cannot even express the
checkpoints (``model.py`` raises ``ValueError`` if a checkpoint month exceeds
H). ``configs/base.yaml`` at H=36 solves in well under a second (measured:
~0.1s), so a 60s CBC time_limit is generous headroom, not a bottleneck; no
H=26/intermediate-checkpoint fallback was needed in practice.
"""

from __future__ import annotations

import copy

import pulp
import pytest

from adventure_capital.config import default_config, load_config, validate_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import build_model, solve_model
from adventure_capital.results import extract_results
from adventure_capital.stochastic.model import build_saa_model, solve_saa_model
from adventure_capital.stochastic.scenarios import Scenario


_TIME_LIMIT = 60


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


def test_commitment_off_is_noop():
    """enabled: false (or absent keys entirely) must yield a bit-for-bit identical
    solve to the current baseline — no golden touched, no default flipped."""
    cfg_absent = _base_config()
    cfg_absent.pop("growth_commitment", None)
    cfg_absent.pop("hiring", None)
    result_absent = _solve(cfg_absent)

    cfg_explicit_off = _base_config(
        growth_commitment={"enabled": False}, hiring={"enabled": False}
    )
    result_explicit = _solve(cfg_explicit_off)

    assert result_absent["solved"]["status"] == "Optimal"
    assert result_explicit["solved"]["status"] == "Optimal"
    assert result_absent["solved"]["objective"] == pytest.approx(
        result_explicit["solved"]["objective"], rel=1e-9
    )

    df_absent = extract_results(result_absent["instance"], result_absent["solved"])
    df_explicit = extract_results(result_explicit["instance"], result_explicit["solved"])
    assert (df_absent["Adq_clientes"] == df_explicit["Adq_clientes"]).all()
    assert (df_absent["Vendedores"] == df_explicit["Vendedores"]).all()


def test_commitment_checkpoints_hold():
    """on -> C24 >= (1-slack)*sqrt(3)*C12 and C36 >= (1-slack)*3*C12 in the solution."""
    config = _base_config(
        growth_commitment={
            "enabled": True,
            "source": "vc_minimum",
            "multiple_3y": 3.0,
            "checkpoints": "annual",
        }
    )
    result = _solve(config)
    assert result["solved"]["status"] == "Optimal"
    inst = result["instance"]
    targets = inst["growth_commitment"]["checkpoint_targets"]
    assert set(targets.keys()) == {24, 36}

    df = extract_results(inst, result["solved"])
    stock_24 = float(df.loc[df["t"] == 24, "Clientes_activos"].iloc[0])
    stock_36 = float(df.loc[df["t"] == 36, "Clientes_activos"].iloc[0])
    assert stock_24 >= targets[24] - 1e-6
    assert stock_36 >= targets[36] - 1e-6
    # Sanity: matches the closed-form m = multiple_3y, sqrt(m) at year 2.
    c12 = inst["growth_commitment"]["C12"]
    assert targets[36] == pytest.approx(3.0 * c12, rel=1e-9)
    assert targets[24] == pytest.approx((3.0 ** 0.5) * c12, rel=1e-9)


def test_commitment_terminal_only_mode():
    """checkpoints: terminal -> only C36 is restricted (no C24 constraint)."""
    config = _base_config(
        growth_commitment={
            "enabled": True,
            "source": "vc_minimum",
            "multiple_3y": 3.0,
            "checkpoints": "terminal",
        }
    )
    inst = generate_instance(config)
    targets = inst["growth_commitment"]["checkpoint_targets"]
    assert set(targets.keys()) == {36}

    result = _solve(config)
    assert result["solved"]["status"] == "Optimal"
    df = extract_results(inst, result["solved"])
    stock_36 = float(df.loc[df["t"] == 36, "Clientes_activos"].iloc[0])
    assert stock_36 >= targets[36] - 1e-6


def test_commitment_infeasible_reported():
    """h=0 (zero hiring headroom) + vc_minimum in a tight case -> Infeasible
    reported cleanly, no crash. Uses a synthetic tight case: ceiling capped at
    exactly the commitment multiple (no slack) + hiring frozen at month-12
    headcount, so the commitment cannot be met by growing the sales team."""
    config = _base_config(
        acquisition_ceiling={"enabled": True, "target_stock_multiplier": 3.0, "slack": 0.0},
        hiring={"enabled": True, "max_new_sellers_per_month": 0, "max_new_leaders_per_month": 0},
        growth_commitment={
            "enabled": True,
            "source": "vc_minimum",
            "multiple_3y": 3.0,
            "checkpoints": "annual",
        },
    )
    result = _solve(config)
    assert result["solved"]["status"] == "Infeasible"


def test_hiring_friction_limits_jump():
    """V13 <= V12 + h_v; L13 <= L12 + h_l."""
    config = _base_config(
        hiring={"enabled": True, "max_new_sellers_per_month": 1, "max_new_leaders_per_month": 1}
    )
    result = _solve(config)
    assert result["solved"]["status"] == "Optimal"
    df = extract_results(result["instance"], result["solved"])
    v12 = float(df.loc[df["t"] == 12, "Vendedores"].iloc[0])
    v13 = float(df.loc[df["t"] == 13, "Vendedores"].iloc[0])
    l12 = float(df.loc[df["t"] == 12, "Lideres"].iloc[0])
    l13 = float(df.loc[df["t"] == 13, "Lideres"].iloc[0])
    assert v13 <= v12 + 1 + 1e-9
    assert l13 <= l12 + 1 + 1e-9


def test_hiring_off_is_noop():
    """hiring: enabled false (or absent) must not add any headcount constraint
    beyond the existing monotonicity — identical solve to baseline."""
    cfg_absent = _base_config()
    cfg_absent.pop("hiring", None)
    cfg_off = _base_config(hiring={"enabled": False})

    result_absent = _solve(cfg_absent)
    result_off = _solve(cfg_off)
    assert result_absent["solved"]["objective"] == pytest.approx(
        result_off["solved"]["objective"], rel=1e-9
    )


def test_parity_det_stoch_first_stage():
    """Same params (single deterministic scenario, no perturbation) -> same
    V-path, and the commitment floor binds identically in the stochastic
    plan_total (first-stage, pre-efficiency) stock."""
    config = _base_config(
        growth_commitment={
            "enabled": True,
            "source": "vc_minimum",
            "multiple_3y": 3.0,
            "checkpoints": "annual",
        }
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


def test_config_validation_commitment():
    """multiple<=1, invalid source, custom without g, slack>=1, h<0 -> ValueError."""
    base = default_config()

    cfg = copy.deepcopy(base)
    cfg["growth_commitment"] = {"enabled": True, "multiple_3y": 1.0}
    with pytest.raises(ValueError, match="multiple_3y"):
        validate_config(cfg)

    cfg = copy.deepcopy(base)
    cfg["growth_commitment"] = {"enabled": True, "source": "not_a_source"}
    with pytest.raises(ValueError, match="source"):
        validate_config(cfg)

    cfg = copy.deepcopy(base)
    cfg["growth_commitment"] = {"enabled": True, "source": "custom"}
    with pytest.raises(ValueError, match="custom_g_annual"):
        validate_config(cfg)

    cfg = copy.deepcopy(base)
    cfg["growth_commitment"] = {"enabled": True, "floor_slack": 1.0}
    with pytest.raises(ValueError, match="floor_slack"):
        validate_config(cfg)

    cfg = copy.deepcopy(base)
    cfg["hiring"] = {"enabled": True, "max_new_sellers_per_month": -1}
    with pytest.raises(ValueError, match="max_new_sellers_per_month"):
        validate_config(cfg)

    cfg = copy.deepcopy(base)
    cfg["hiring"] = {"enabled": True, "max_new_leaders_per_month": -1}
    with pytest.raises(ValueError, match="max_new_leaders_per_month"):
        validate_config(cfg)


def test_suggestions_values():
    """base.yaml: C12~=55.8, g_vc=73.2%+-eps, g_mom(acquisition)=15.8%/mes+-eps."""
    from adventure_capital.instance import compute_growth_suggestions

    config = load_config("configs/base.yaml")
    suggestions = compute_growth_suggestions(config)
    assert suggestions["C12"] == pytest.approx(55.8, abs=0.1)
    assert suggestions["g_vc_minimum"] == pytest.approx(0.732, abs=0.001)
    assert suggestions["g_plan_mom_monthly_acquisition"] == pytest.approx(0.158, abs=0.001)
    # Stock MoM is reported alongside acquisition MoM (supervisor correction B):
    # the commitment binds on stock, so this is the comparable number.
    assert "g_plan_mom_stock" in suggestions
    assert suggestions["g_plan_mom_stock"] > suggestions["g_vc_minimum"]


def test_diagnosis_routine_smoke():
    """Synthetic infeasible case -> JSON with >=1 feasible relaxation and the
    expected R1 diagnosis (hiring friction removed restores feasibility)."""
    from scripts.diagnose_infeasibility import diagnose_infeasibility

    config = _base_config(
        acquisition_ceiling={"enabled": True, "target_stock_multiplier": 3.0, "slack": 0.0},
        hiring={"enabled": True, "max_new_sellers_per_month": 0, "max_new_leaders_per_month": 0},
        growth_commitment={
            "enabled": True,
            "source": "vc_minimum",
            "multiple_3y": 3.0,
            "checkpoints": "annual",
        },
    )
    diagnosis = diagnose_infeasibility(config, time_limit=_TIME_LIMIT)
    assert diagnosis["base_status"] == "Infeasible"
    assert len(diagnosis["feasible_relaxations"]) >= 1
    assert "R1" in diagnosis["feasible_relaxations"]
    r1 = next(r for r in diagnosis["relaxations"] if r["relaxation"] == "R1")
    assert r1["feasible"] is True
    assert "contrataci" in r1["diagnosis"] or "onboarding" in r1["diagnosis"]


def test_dd_chain_emits_w_warnings_and_survives_infeasible(tmp_path):
    """W1-W5 wired into run_due_diligence (follow-up closed): the calibration
    warnings appear as findings, and an Infeasible commitment produces a clean
    DD17 report instead of the consistency-check crash."""
    from pathlib import Path

    from adventure_capital.due_diligence.workflow import run_due_diligence

    # Feasible case with source plan_mom (base.yaml stock MoM 33.6x/yr >> 2x
    # the VC minimum): expect W1 (DD13) present and normal chain completion.
    config = _base_config(
        growth_commitment={
            "enabled": True,
            "source": "plan_mom",
            "multiple_3y": 3.0,
            "checkpoints": "annual",
        },
    )
    result = run_due_diligence(config, output_dir=tmp_path / "feasible")
    ids = {f.id for f in result["verdict"].findings}
    assert "DD13" in ids  # W1 fired from suggestions
    assert result["ran_model"] is True

    # Infeasible commitment (recipe from test_commitment_infeasible_reported):
    # chain must not crash; DD17 (W3) reported; artifacts written.
    config_inf = _base_config(
        acquisition_ceiling={"enabled": True, "target_stock_multiplier": 3.0, "slack": 0.0},
        hiring={"enabled": True, "max_new_sellers_per_month": 0, "max_new_leaders_per_month": 0},
        growth_commitment={
            "enabled": True,
            "source": "vc_minimum",
            "multiple_3y": 3.0,
            "checkpoints": "annual",
        },
    )
    result_inf = run_due_diligence(config_inf, output_dir=tmp_path / "infeasible")
    ids_inf = {f.id for f in result_inf["verdict"].findings}
    assert "DD17" in ids_inf
    dd17 = next(f for f in result_inf["verdict"].findings if f.id == "DD17")
    assert dd17.evidence["solver_status"] in {"Infeasible", "Undefined"}
    assert Path(result_inf["artifacts"]["json"]).exists()


def test_dd18_flags_conservative_core_plan():
    from adventure_capital.due_diligence.rules import rule_conservative_plan_diagnostic

    config = load_config("configs/demo-growth-core.yaml")
    finding = rule_conservative_plan_diagnostic(config)
    assert finding is not None
    assert finding.id == "DD18"
    assert finding.passed is True
    assert finding.evidence["classification"] == "Conservative"
    assert finding.evidence["M_star_feasible"] > finding.evidence["target_multiple"]
    assert finding.evidence["upper_bound_hit"] is True
    assert "feasible up to tested cap" in finding.message


def test_dd18_does_not_fire_when_higher_m_is_van_destructive():
    from adventure_capital.due_diligence.rules import rule_conservative_plan_diagnostic

    config = load_config("configs/demo-growth-core.yaml")
    config["servicios"][0]["ticket"] = 80
    config["servicios"][0]["c_u"] = 70
    config["rem_v"] = 5000
    config["rem_l"] = 7000
    config["g_adm"] = 5000
    finding = rule_conservative_plan_diagnostic(config)
    assert finding is not None
    assert finding.id == "DD18"
    assert finding.passed is True
    assert finding.evidence["classification"] == "Calibrated"

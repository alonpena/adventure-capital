"""ADR 0010 R3 — pre-feasibility heuristics."""

from adventure_capital.config import default_config
from adventure_capital.instance import check_pre_feasibility, generate_instance


def test_healthy_instance_has_no_warnings():
    config = default_config()
    config["VC"] = 5_000_000  # amply funded vs year-1 fixed cost
    instance = generate_instance(config)
    assert check_pre_feasibility(instance) == []


def test_underfunded_vc_warns():
    config = default_config()
    config["VC"] = 1_000  # far below 12*(g_adm + RRHH[1])
    instance = generate_instance(config)
    warnings = check_pre_feasibility(instance)
    assert any("VC=" in w and "fixed cost" in w for w in warnings)


def test_negative_unit_margin_warns():
    config = default_config()
    config["VC"] = 5_000_000  # isolate the margin warning
    config["servicios"][0]["ticket"] = 30
    config["servicios"][0]["c_u"] = 30  # ticket <= c_u
    instance = generate_instance(config)
    warnings = check_pre_feasibility(instance)
    assert any("negative unit margin" in w for w in warnings)

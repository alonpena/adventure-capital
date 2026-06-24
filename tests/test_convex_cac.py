"""ADR 0013 — convex-CAC endogenous growth law."""

from adventure_capital.config import load_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import solve_growth_plan
from adventure_capital.results import extract_results


def _y2_over_y1(config):
    inst = generate_instance(config)
    sol = solve_growth_plan(inst)
    assert sol["status"] == "Optimal"
    df = extract_results(inst, sol)
    y1 = sum(inst["A_base"][(0, t)] for t in range(1, 13))
    y2 = df[df["t"].between(13, 24)]["Adq_clientes"].sum()
    return y2 / y1, inst


def test_convex_disabled_by_default():
    """Convex CAC is opt-in; absent block leaves the log-ceiling growth law intact."""
    config = load_config("configs/base.yaml")
    inst = generate_instance(config)
    assert inst["convex_cac"]["enabled"] is False


def test_convex_instance_params_traceable():
    """LTV, batch (year-1 run-rate) and base CAC are derived deterministically."""
    config = load_config("configs/base.yaml")
    config["convex_cac"] = {"enabled": True, "theta": 1.0}
    inst = generate_instance(config)
    cx = inst["convex_cac"]
    assert cx["enabled"] is True
    assert cx["ltv"][0] > 0
    assert cx["base_cac"][0] > 0
    # batch = mean of year-1 monthly acquisition
    expected_batch = sum(inst["A_base"][(0, t)] for t in range(1, 13)) / 12
    assert cx["batch"][0] == max(1.0, expected_batch)


def test_convex_higher_theta_limits_growth():
    """Higher theta (faster channel saturation) yields strictly less growth — the law is
    endogenous and self-limiting, not an exogenous cap."""
    base = load_config("configs/base.yaml")

    g_low, _ = _y2_over_y1({**base, "convex_cac": {"enabled": True, "theta": 5.0}})
    g_high, _ = _y2_over_y1({**base, "convex_cac": {"enabled": True, "theta": 50.0}})

    assert g_high < g_low  # more saturation -> less growth
    assert g_high >= 1.0  # still grows somewhat

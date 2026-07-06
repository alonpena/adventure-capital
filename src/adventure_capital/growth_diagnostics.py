"""Growth-thesis post-solve diagnostics.

These helpers sweep the investment-thesis multiple as an external parameter.
The multiple is never a solver variable, and VAN is observed after each solve.
"""

from __future__ import annotations

import copy
from typing import Any

from adventure_capital.config import resolve_investment_thesis


def _configured_cash_floor(config: dict[str, Any]) -> float | None:
    working_capital = config.get("working_capital", {}) or {}
    if working_capital.get("enabled", False):
        return -float(config.get("VC", 0.0))
    policy = config.get("liquidity_policy", {"type": "none"}) or {}
    if policy.get("type", "none") == "nonnegative":
        return 0.0
    if policy.get("type") == "minimum_cash":
        return float(policy.get("value", 0.0))
    return None


def _with_multiple(config: dict[str, Any], multiple: float) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    thesis = dict(cfg.get("investment_thesis") or {})
    thesis["multiple"] = float(multiple)
    cfg["investment_thesis"] = thesis
    if (cfg.get("growth_commitment") or {}).get("enabled", False):
        cfg["growth_commitment"] = dict(cfg["growth_commitment"])
        cfg["growth_commitment"]["multiple_3y"] = float(multiple)
    return cfg


def _probe(config: dict[str, Any], multiple: float, *, time_limit: int | None) -> dict[str, Any]:
    from adventure_capital.instance import generate_instance
    from adventure_capital.model import build_model, solve_model
    from adventure_capital.results import extract_results
    from adventure_capital.valuation import calculate_dcf

    cfg = _with_multiple(config, multiple)
    floor = _configured_cash_floor(cfg)
    try:
        inst = generate_instance(cfg)
        solved = solve_model(build_model(inst), time_limit=time_limit)
    except Exception as exc:
        return {
            "multiple": float(multiple),
            "status": "Error",
            "feasible": False,
            "error": str(exc),
        }
    if solved["status"] != "Optimal":
        return {
            "multiple": float(multiple),
            "status": solved["status"],
            "feasible": False,
        }
    df = extract_results(inst, solved)
    min_cash = float(df["Caja"].min())
    cash_ok = True if floor is None else min_cash >= floor - 1e-6
    dcf = calculate_dcf(df, inst)
    stock_h = float(df.loc[df["t"] == inst["investment_thesis"]["horizon_months"], "Clientes_activos"].sum())
    c12 = float(inst.get("growth_commitment", {}).get("C12", 0.0))
    return {
        "multiple": float(multiple),
        "status": solved["status"],
        "feasible": bool(cash_ok),
        "min_cash": min_cash,
        "cash_floor": floor,
        "van": float(dcf["VAN"]),
        "stock_horizon": stock_h,
        "ratio_horizon": stock_h / c12 if c12 > 0 else None,
    }


def compute_conservative_plan_diagnostic(
    config: dict[str, Any],
    *,
    max_iterations: int = 8,
    upper_multiple: float = 10.0,
    time_limit: int | None = None,
) -> dict[str, Any]:
    """Estimate feasible thesis headroom and VAN monotonicity.

    Returns JSON-serializable diagnostics. No-op unless the core growth
    commitment + acquisition envelope are both enabled.
    """
    if not (config.get("growth_commitment") or {}).get("enabled", False):
        return {"enabled": False, "reason": "growth_commitment disabled"}
    if not (config.get("acquisition_envelope") or {}).get("enabled", False):
        return {"enabled": False, "reason": "acquisition_envelope disabled"}

    thesis = resolve_investment_thesis(config)
    target = float(thesis["multiple"])
    upper = max(float(upper_multiple), target)
    probes: dict[str, dict[str, Any]] = {}

    def record(multiple: float) -> dict[str, Any]:
        key = f"{multiple:.6g}"
        if key not in probes:
            probes[key] = _probe(config, multiple, time_limit=time_limit)
        return probes[key]

    target_probe = record(target)
    if not target_probe.get("feasible"):
        low = 1.0
        low_probe = record(low)
        if not low_probe.get("feasible"):
            m_star = None
        else:
            high = target
            for _ in range(max_iterations):
                mid = (low + high) / 2.0
                if record(mid).get("feasible"):
                    low = mid
                else:
                    high = mid
            m_star = low
        classification = "Infeasible"
        conservative = False
    else:
        low = target
        high = upper
        record(high)
        for _ in range(max_iterations):
            mid = (low + high) / 2.0
            if record(mid).get("feasible"):
                low = mid
            else:
                high = mid
        m_star = low
        upward = [
            p
            for p in probes.values()
            if p.get("feasible") and p.get("van") is not None and p["multiple"] >= target - 1e-9
        ]
        upward.sort(key=lambda p: p["multiple"])
        van_non_decreasing = all(
            upward[i]["van"] >= upward[i - 1]["van"] - 1e-6 for i in range(1, len(upward))
        )
        headroom = m_star > target + 1e-3
        conservative = bool(headroom and van_non_decreasing)
        classification = "Conservative" if conservative else "Calibrated"

    van_at_probe = {
        key: value.get("van")
        for key, value in sorted(probes.items(), key=lambda item: float(item[0]))
        if value.get("van") is not None
    }
    thesis_gap = None if m_star is None else float(m_star - target)
    cap_tolerance = (upper - target) / (2**max_iterations) + 1e-9
    upper_bound_hit = bool(m_star is not None and abs(float(m_star) - upper) <= cap_tolerance)
    return {
        "enabled": True,
        "classification": classification,
        "target_multiple": target,
        "M_star_feasible": m_star,
        "thesis_gap": thesis_gap,
        "upper_bound_hit": upper_bound_hit,
        "upper_bound_tolerance": cap_tolerance,
        "van_at_probe": van_at_probe,
        "probes": probes,
        "conservative": conservative,
        "iterations": max_iterations,
        "upper_multiple": upper,
    }

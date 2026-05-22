"""Phase-B ex-post Monte Carlo evaluation of a fixed strategy.

Given the first-stage strategy chosen by Phase A (acquisition ``A``, sellers
``V``, leaders ``L``), evaluate it across a large scenario sample WITHOUT
re-solving the MILP. The recourse is closed-form:

    m_op[s,t]    = ceil(Q[s,t] / u_max[s])         # smallest feasible capacity step
    Cost_op[s,t] = max(c_u*Q, c_min*m_op)          # operational cost floor

Everything downstream (EBITDA, cash, DCF VAN, funding gap, breakeven) is pure
arithmetic per scenario, so this scales to thousands of draws cheaply.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from adventure_capital.instance import generate_instance
from adventure_capital.stochastic.scenarios import Scenario, apply_scenario


def _liquidity_floor(config: dict[str, Any]) -> float:
    policy = (config.get("liquidity_policy", {}) or {}).get("type", "none")
    if policy == "minimum_cash":
        return float(config.get("liquidity_policy", {}).get("value", 0.0))
    return 0.0


def _evaluate_one(
    config: dict[str, Any],
    scenario: Scenario,
    strategy: dict[str, dict[Any, float]],
    *,
    floor: float,
) -> dict[str, Any]:
    inst = generate_instance(apply_scenario(config, scenario))
    services = inst["servicios"]
    service_count = inst["S"]
    periods = inst["T"]
    horizon = inst["H"]
    phi, delta, alpha = inst["phi"], inst["delta"], inst["alpha"]
    monthly_discount = inst["beta"]
    vc = float(inst["VC"])
    tax = float(config.get("tax", 0.125))
    terminal_multiple_vd = float(config.get("mult_vd_ebitda", 1.0))

    acquisition = strategy["A"]
    sellers = strategy["V"]
    leaders = strategy["L"]

    cumulative_ebitda = 0.0
    cash = 0.0
    pv_cashflows = 0.0
    max_gap = 0.0
    breakeven_month: int | None = None
    last_ebitda = 0.0

    for t in periods:
        period_revenue = 0.0
        period_op_cost = 0.0
        for s in range(service_count):
            new_sales = acquisition.get((s, t), 0.0)
            recurring = sum(
                delta.get((s, cohort, t), 0)
                * phi.get((s, cohort, t), 0.0)
                * alpha.get((s, t), 0.0)
                * acquisition.get((s, cohort), 0.0)
                for cohort in range(1, t)
            )
            quantity = new_sales + recurring
            steps = math.ceil(quantity / services[s]["u_max"]) if quantity > 0 else 0
            op_cost = max(services[s]["c_u"] * quantity, services[s]["c_min"] * steps)
            period_revenue += services[s]["ticket"] * quantity
            period_op_cost += op_cost

        cac = (
            inst["rem_v"] * sellers.get(t, 0.0)
            + inst["rem_l"] * leaders.get(t, 0.0)
            + sum(
                (inst["com_v"] + inst["com_l"]) * services[s]["ticket"] * acquisition.get((s, t), 0.0)
                for s in range(service_count)
            )
        )
        ebitda = period_revenue - period_op_cost - cac - inst["g_adm"] - inst["RRHH"][t]

        cumulative_ebitda += ebitda
        cash += ebitda
        max_gap = max(max_gap, floor - cash)
        if breakeven_month is None and cumulative_ebitda >= 0:
            breakeven_month = t

        tax_amount = max(ebitda * tax, 0.0)
        net_cashflow = ebitda - tax_amount
        pv_cashflows += net_cashflow / (1 + monthly_discount) ** t
        last_ebitda = ebitda

    terminal_nominal = max(last_ebitda * 12 * terminal_multiple_vd, 0.0)
    terminal_pv = terminal_nominal / (1 + monthly_discount) ** horizon
    van = -vc + pv_cashflows + terminal_pv
    funding_gap = max(max_gap, 0.0)

    return {
        "scenario": scenario.name,
        "probability": scenario.probability,
        "churn_multiplier": scenario.churn_multiplier,
        "productivity_multiplier": scenario.productivity_multiplier,
        "financing_multiplier": scenario.financing_multiplier,
        "wacc": float(inst["beta_anual"]),
        "VAN": van,
        "total_ebitda": cumulative_ebitda,
        "final_cash": cash,
        "funding_gap": funding_gap,
        "gap_positive": funding_gap > 0,
        "breakeven_month": breakeven_month,
    }


def evaluate_strategy(
    config: dict[str, Any],
    strategy: dict[str, dict[Any, float]],
    scenarios: list[Scenario],
) -> pd.DataFrame:
    """Evaluate a fixed first-stage ``strategy`` over ``scenarios``.

    Returns one row per scenario (the full distribution). ``strategy`` is the
    dict returned by :func:`stochastic.model.solve_saa_model`.
    """
    floor = _liquidity_floor(config)
    rows = [_evaluate_one(config, scenario, strategy, floor=floor) for scenario in scenarios]
    return pd.DataFrame(rows)

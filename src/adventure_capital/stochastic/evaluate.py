"""Ex-post LHS evaluation of a fixed first-stage strategy.

Given the first-stage plan chosen by the SAA solve (per-channel acquisition
plans, sellers/leaders, advertising investment), evaluate it across a large
*out-of-sample* LHS scenario sample WITHOUT re-solving the MILP. The recourse
is closed-form and mirrors the SAA model exactly:

    A[s,t,w]     = channel-efficiency * plan        (realized acquisition)
    m_op[s,t,w]  = ceil(Q[s,t,w] / u_max[s])        # smallest feasible step
    Cost_op      = max(c_u*Q, c_min*m_op)

Everything downstream (CAC by channel, EBITDA, tax, cash, DCF VAN, funding gap,
breakeven, runway, unit economics) is pure arithmetic per scenario, so this
scales to thousands of LHS draws cheaply.

The scenarios passed in MUST come from
``stochastic.scenarios.generate_evaluation_scenarios`` (LHS, separate seed,
larger N). This is an ex-post LHS evaluation, not plain random Monte Carlo.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from adventure_capital.instance import generate_instance
from adventure_capital.stochastic.defaults import M4_DEFAULTS
from adventure_capital.stochastic.scenarios import Scenario, apply_scenario
from adventure_capital.unit_economics import annual_ltv


def _stochastic_block(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("stochastic", {}) or {}


def _terminal_multiple(config: dict[str, Any]) -> float:
    return float(_stochastic_block(config).get("terminal_multiple", 1.0))


def _commission_periods(config: dict[str, Any]) -> int:
    block = _stochastic_block(config).get("third_party_defaults", {}) or {}
    return int(
        block.get(
            "commission_periods",
            M4_DEFAULTS["third_party_defaults"]["commission_periods"],
        )
    )


def _plan_lookup(plan: dict[str, float]) -> dict[tuple[int, int], float]:
    """Parse a ``{"s_t": value}`` plan dict into ``{(s, t): value}``."""
    parsed: dict[tuple[int, int], float] = {}
    for key, value in (plan or {}).items():
        s_str, t_str = key.split("_")
        parsed[(int(s_str), int(t_str))] = float(value)
    return parsed


def _evaluate_one(
    config: dict[str, Any],
    scenario: Scenario,
    strategy: dict[str, Any],
    *,
    commission_periods: int,
    terminal_multiple: float,
    milestones: list[int],
) -> dict[str, Any]:
    inst = generate_instance(apply_scenario(config, scenario))
    services = inst["servicios"]
    service_count = inst["S"]
    periods = inst["T"]
    horizon = inst["H"]
    phi, delta, alpha = inst["phi"], inst["delta"], inst["alpha"]
    discount = inst["descuento"]
    vc = float(inst["VC"])
    tax_rate = float(inst["tax"])
    floor = -vc

    channels = inst["channels"]
    ad_active = bool(channels["advertising"]["active"])
    tp_active = bool(channels["third_party"]["active"])
    tp_commission = float(channels["third_party"].get("commission", 0.0)) if tp_active else 0.0

    sf_plan = _plan_lookup(strategy["A_sf_plan"])
    ad_plan = _plan_lookup(strategy["A_ad_plan"]) if ad_active else {}
    tp_plan = _plan_lookup(strategy["A_tp_plan"]) if tp_active else {}
    sellers = {int(t): float(v) for t, v in strategy["V"].items()}
    leaders = {int(t): float(v) for t, v in strategy["L"].items()}
    ad_investment = {int(t): float(v) for t, v in strategy["I_ad"].items()}

    sf_eff = scenario.salesforce_efficiency
    ad_eff = scenario.advertising_efficiency
    tp_eff = scenario.third_party_efficiency

    def a_sf(s: int, t: int) -> float:
        if t <= 12:
            return sf_plan.get((s, t), 0.0)
        return sf_eff * sf_plan.get((s, t), 0.0)

    def a_ad(s: int, t: int) -> float:
        if not ad_active or t <= 12:
            return 0.0
        return ad_eff * ad_plan.get((s, t), 0.0)

    def a_tp(s: int, t: int) -> float:
        if not tp_active or t <= 12:
            return 0.0
        return tp_eff * tp_plan.get((s, t), 0.0)

    def a_real(s: int, t: int) -> float:
        return a_sf(s, t) + a_ad(s, t) + a_tp(s, t)

    cumulative_ebitda = 0.0
    cash = 0.0
    pv_cashflows = 0.0
    max_gap = 0.0
    breakeven_month: int | None = None
    runway_month: int | None = None
    last_ebitda = 0.0

    total_acquisition = 0.0
    total_revenue = 0.0
    total_recurring_revenue = 0.0
    total_cac = 0.0
    active_clients_sum = 0.0
    final_active_clients = 0.0

    for t in periods:
        period_revenue = 0.0
        period_op_cost = 0.0
        period_active = 0.0
        for s in range(service_count):
            ticket = services[s]["ticket"]
            new_sales = a_real(s, t)
            recurring = sum(
                delta.get((s, cohort, t), 0)
                * phi.get((s, cohort, t), 0.0)
                * alpha.get((s, t), 0.0)
                * a_real(s, cohort)
                for cohort in range(1, t)
            )
            quantity = new_sales + recurring
            steps = math.ceil(quantity / services[s]["u_max"]) if quantity > 0 else 0
            op_cost = max(services[s]["c_u"] * quantity, services[s]["c_min"] * steps)
            active = sum(
                phi.get((s, cohort, t), 0.0) * a_real(s, cohort)
                for cohort in range(1, t + 1)
            )
            period_revenue += ticket * quantity
            period_op_cost += op_cost
            period_active += active
            total_acquisition += new_sales
            total_recurring_revenue += ticket * recurring
            if t == horizon:
                final_active_clients += active

        # CAC by channel.
        cac_sf = (
            inst["rem_v"] * sellers.get(t, 0.0)
            + inst["rem_l"] * leaders.get(t, 0.0)
            + sum(
                (inst["com_v"] + inst["com_l"]) * services[s]["ticket"] * a_sf(s, t)
                for s in range(service_count)
            )
        )
        cac_ad = ad_investment.get(t, 0.0) if ad_active else 0.0
        cac_tp = 0.0
        if tp_active and tp_commission > 0.0:
            low = max(1, t - commission_periods + 1)
            window_rev = 0.0
            for s in range(service_count):
                ticket = services[s]["ticket"]
                for cohort in range(low, t + 1):
                    if cohort == t:
                        units = a_tp(s, cohort)
                    else:
                        units = (
                            delta.get((s, cohort, t), 0)
                            * phi.get((s, cohort, t), 0.0)
                            * alpha.get((s, t), 0.0)
                            * a_tp(s, cohort)
                        )
                    window_rev += ticket * units
            cac_tp = tp_commission * window_rev
        cac = cac_sf + cac_ad + cac_tp

        ebitda = period_revenue - period_op_cost - cac - inst["g_adm"] - inst["RRHH"][t]

        cumulative_ebitda += ebitda
        cash += ebitda
        max_gap = max(max_gap, floor - cash)
        if breakeven_month is None and cumulative_ebitda >= 0:
            breakeven_month = t
        if runway_month is None and cash < floor:
            runway_month = t

        tax_amount = max(ebitda * tax_rate, 0.0)
        net_cashflow = ebitda - tax_amount
        pv_cashflows += discount[t] * net_cashflow
        last_ebitda = ebitda

        total_revenue += period_revenue
        total_cac += cac
        active_clients_sum += period_active

    # Linear terminal value (matches the SAA objective; no max()).
    terminal_pv = discount[horizon] * terminal_multiple * 12 * last_ebitda
    van = -vc + pv_cashflows + terminal_pv
    funding_gap = max(max_gap, 0.0)

    # Unit economics (annual; service lines summed) for this scenario.
    cac_per_customer = total_cac / total_acquisition if total_acquisition > 0 else 0.0
    ltv = annual_ltv(services)
    ltv_cac = ltv / cac_per_customer if cac_per_customer > 0 else float("nan")
    avg_active = active_clients_sum / len(periods) if periods else 0.0
    arpu = total_revenue / (avg_active * len(periods)) if avg_active > 0 else 0.0
    arr = total_recurring_revenue / total_revenue if total_revenue > 0 else 0.0

    row: dict[str, Any] = {
        "scenario": scenario.name,
        "probability": scenario.probability,
        "churn_multiplier": scenario.churn_multiplier,
        "salesforce_efficiency": scenario.salesforce_efficiency,
        "advertising_efficiency": scenario.advertising_efficiency,
        "third_party_efficiency": scenario.third_party_efficiency,
        "wacc_multiplier": scenario.wacc_multiplier,
        "wacc": float(inst["beta_anual"]),
        "VAN": van,
        "total_ebitda": cumulative_ebitda,
        "final_cash": cash,
        "funding_gap": funding_gap,
        "cash_below_floor": runway_month is not None,
        "breakeven_month": breakeven_month,
        "runway_month": runway_month,
        "final_active_clients": final_active_clients,
        "cac_per_customer": cac_per_customer,
        "ltv_cac": ltv_cac,
        "arpu": arpu,
        "arr": arr,
    }
    for milestone in milestones:
        row[f"hit_final_active_clients_{milestone}"] = final_active_clients >= milestone
    return row


def evaluate_strategy(
    config: dict[str, Any],
    strategy: dict[str, Any],
    scenarios: list[Scenario],
) -> pd.DataFrame:
    """Evaluate a fixed first-stage ``strategy`` over ex-post LHS ``scenarios``.

    Returns one row per scenario (the full distribution). ``strategy`` is the
    dict returned by :func:`stochastic.model.solve_saa_model`.
    """
    milestones = list(
        _stochastic_block(config).get("milestones", {}).get(
            "client_counts", M4_DEFAULTS["milestones"]["client_counts"]
        )
    )
    # Growth commitment (ADR 0014): auto-add the terminal (C36) target as a
    # milestone so P(C36_realized >= multiple_3y*C12) is reported ex-post as a
    # KPI (summarize_distribution already turns any milestone into
    # prob_hit_final_active_clients_{milestone}). No-op when disabled.
    growth_commitment = config.get("growth_commitment", {}) or {}
    if growth_commitment.get("enabled", False):
        from adventure_capital.instance import generate_instance as _gen_instance

        base_inst = _gen_instance(config)
        terminal_target = base_inst.get("growth_commitment", {}).get(
            "checkpoint_targets", {}
        ).get(base_inst["H"])
        if terminal_target is not None:
            rounded_target = int(round(terminal_target))
            if rounded_target not in milestones:
                milestones = sorted(milestones + [rounded_target])
    rows = [
        _evaluate_one(
            config,
            scenario,
            strategy,
            commission_periods=_commission_periods(config),
            terminal_multiple=_terminal_multiple(config),
            milestones=milestones,
        )
        for scenario in scenarios
    ]
    return pd.DataFrame(rows)

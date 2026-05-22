"""Phase-A two-stage SAA stochastic MILP.

Builds one MILP over a scenario sample. First-stage decisions (acquisition
``A``, sellers ``V``, leaders ``L``) are shared across all scenarios. Recourse
(operational capacity steps ``m_op`` and all financial outcomes) is indexed by
scenario. The objective is expected discounted EBITDA plus a linear terminal
proxy. There is no hard liquidity floor; a per-scenario funding gap is measured.

This module does not import or modify the deterministic ``model.py``. It reuses
``generate_instance`` to derive per-scenario survival/recurrence/discount data.
"""

from __future__ import annotations

import math
from typing import Any

import pulp

from adventure_capital.instance import generate_instance
from adventure_capital.stochastic.scenarios import Scenario, apply_scenario

ModelBundle = dict[str, Any]


def _terminal_multiple(config: dict[str, Any]) -> float:
    block = config.get("stochastic", {}) or {}
    return float(block.get("terminal_multiple", 1.0))


def _liquidity_floor(config: dict[str, Any]) -> float:
    policy = (config.get("liquidity_policy", {}) or {}).get("type", "none")
    if policy == "minimum_cash":
        return float(config.get("liquidity_policy", {}).get("value", 0.0))
    return 0.0


def build_saa_model(config: dict[str, Any], scenarios: list[Scenario]) -> ModelBundle:
    """Build the SAA MILP for ``config`` over ``scenarios``."""
    if not scenarios:
        raise ValueError("At least one scenario is required.")

    base_instance = generate_instance(config)
    horizon = base_instance["H"]
    service_count = base_instance["S"]
    periods = base_instance["T"]
    services = base_instance["servicios"]
    fixed_periods = base_instance["T_base"]
    growth_limit = base_instance["g_max_suavizado"]
    terminal_multiple = _terminal_multiple(config)
    floor = _liquidity_floor(config)

    # Per-scenario instances (survival/recurrence/discount/VC vary by scenario).
    scenario_instances = [generate_instance(apply_scenario(config, sc)) for sc in scenarios]
    scenario_keys = list(range(len(scenarios)))

    problem = pulp.LpProblem("optimizacion_pca_estocastico", pulp.LpMaximize)

    # ----- First-stage (shared across scenarios) -----
    acquisition = {
        (s, t): pulp.LpVariable(f"A_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    sellers = {t: pulp.LpVariable(f"V_{t}", lowBound=0, cat="Integer") for t in periods}
    leaders = {t: pulp.LpVariable(f"L_{t}", lowBound=0, cat="Integer") for t in periods}

    # ----- Recourse (per scenario) -----
    def rvar(prefix: str, *, integer: bool = False, low: float | None = 0.0):
        cat = "Integer" if integer else "Continuous"
        return {
            (s, t, w): pulp.LpVariable(f"{prefix}_{s}_{t}_{w}", lowBound=low, cat=cat)
            for s in range(service_count)
            for t in periods
            for w in scenario_keys
        }

    op_steps = rvar("m_op", integer=True)
    active_clients = rvar("C")
    recurring_sales = rvar("R")
    total_services = rvar("Q")
    revenue = rvar("I")
    operational_cost = rvar("Cost_op")

    cac = {
        (t, w): pulp.LpVariable(f"CAC_{t}_{w}", lowBound=0)
        for t in periods
        for w in scenario_keys
    }
    ebitda = {
        (t, w): pulp.LpVariable(f"EBITDA_{t}_{w}", lowBound=None)
        for t in periods
        for w in scenario_keys
    }
    cash = {
        (t, w): pulp.LpVariable(f"Caja_{t}_{w}", lowBound=None)
        for t in periods
        for w in scenario_keys
    }
    funding_gap = {
        (t, w): pulp.LpVariable(f"Gap_{t}_{w}", lowBound=0)
        for t in periods
        for w in scenario_keys
    }

    # ----- Objective: expected discounted EBITDA + linear terminal proxy -----
    objective_terms = []
    for w in scenario_keys:
        prob = scenarios[w].probability
        discount = scenario_instances[w]["descuento"]
        scenario_value = pulp.lpSum(discount[t] * ebitda[(t, w)] for t in periods)
        scenario_value += discount[horizon] * terminal_multiple * ebitda[(horizon, w)]
        objective_terms.append(prob * scenario_value)
    problem += pulp.lpSum(objective_terms), "FO_E_VPL_EBITDA"

    # ----- First-stage acquisition constraints -----
    for s in range(service_count):
        for t in fixed_periods:
            problem += acquisition[(s, t)] == base_instance["A_base"][(s, t)]

    for s in range(service_count):
        base_average = sum(base_instance["A_base"][(s, t)] for t in fixed_periods) / len(fixed_periods)
        transition_base = max(base_instance["A_base"][(s, 12)], base_average)
        problem += acquisition[(s, 13)] <= (1 + growth_limit) * transition_base
        problem += acquisition[(s, 14)] <= (1 + growth_limit) * acquisition[(s, 13)]
        for t in range(15, horizon + 1):
            problem += acquisition[(s, t)] <= ((1 + growth_limit) / 3) * (
                acquisition[(s, t - 1)] + acquisition[(s, t - 2)] + acquisition[(s, t - 3)]
            )

    # ----- First-stage commercial team (months 1-12 fixed from BASE meta) -----
    for t in periods:
        if t <= 12:
            base_acquisition = sum(base_instance["A_base"][(s, t)] for s in range(service_count))
            fixed_sellers = math.ceil(base_acquisition / base_instance["meta"]) if base_acquisition > 0 else 0
            fixed_leaders = math.ceil(fixed_sellers / base_instance["sup"]) if fixed_sellers > 0 else 0
            problem += sellers[t] == fixed_sellers
            problem += leaders[t] == fixed_leaders
        else:
            problem += sellers[t] <= base_instance["sup"] * leaders[t]
        if t >= 13:
            problem += sellers[t] >= sellers[t - 1]
            problem += leaders[t] >= leaders[t - 1]

    lag = base_instance["commercial_productivity_lag"]

    # ----- Per-scenario recourse + financials -----
    for w in scenario_keys:
        inst = scenario_instances[w]
        phi, delta, alpha = inst["phi"], inst["delta"], inst["alpha"]
        scenario_meta = inst["meta"]
        for s in range(service_count):
            for t in periods:
                problem += active_clients[(s, t, w)] == pulp.lpSum(
                    phi.get((s, cohort, t), 0.0) * acquisition[(s, cohort)]
                    for cohort in range(1, t + 1)
                )
                problem += recurring_sales[(s, t, w)] == pulp.lpSum(
                    delta.get((s, cohort, t), 0)
                    * phi.get((s, cohort, t), 0.0)
                    * alpha.get((s, t), 0.0)
                    * acquisition[(s, cohort)]
                    for cohort in range(1, t)
                )
                problem += total_services[(s, t, w)] == acquisition[(s, t)] + recurring_sales[(s, t, w)]
                problem += revenue[(s, t, w)] == services[s]["ticket"] * total_services[(s, t, w)]
                problem += total_services[(s, t, w)] <= services[s]["u_max"] * op_steps[(s, t, w)]
                problem += operational_cost[(s, t, w)] >= services[s]["c_u"] * total_services[(s, t, w)]
                problem += operational_cost[(s, t, w)] >= services[s]["c_min"] * op_steps[(s, t, w)]

        for t in periods:
            if t > 12:
                capacity_period = max(1, t - lag)
                problem += pulp.lpSum(
                    acquisition[(s, t)] for s in range(service_count)
                ) <= scenario_meta * sellers[capacity_period]

            problem += cac[(t, w)] == (
                inst["rem_v"] * sellers[t]
                + inst["rem_l"] * leaders[t]
                + pulp.lpSum(
                    (inst["com_v"] + inst["com_l"]) * services[s]["ticket"] * acquisition[(s, t)]
                    for s in range(service_count)
                )
            )
            problem += ebitda[(t, w)] == (
                pulp.lpSum(revenue[(s, t, w)] for s in range(service_count))
                - pulp.lpSum(operational_cost[(s, t, w)] for s in range(service_count))
                - cac[(t, w)]
                - inst["g_adm"]
                - inst["RRHH"][t]
            )

        problem += cash[(1, w)] == inst["VC"] + ebitda[(1, w)]
        for t in periods:
            if t > 1:
                problem += cash[(t, w)] == cash[(t - 1, w)] + ebitda[(t, w)]
            # Funding gap is diagnostic only: no cash >= floor constraint.
            problem += funding_gap[(t, w)] >= floor - cash[(t, w)]

    variables = {
        "A": acquisition,
        "V": sellers,
        "L": leaders,
        "C": active_clients,
        "R": recurring_sales,
        "Q": total_services,
        "I": revenue,
        "m_op": op_steps,
        "Cost_op": operational_cost,
        "CAC": cac,
        "EBITDA": ebitda,
        "Caja": cash,
        "Gap": funding_gap,
    }
    return {
        "problem": problem,
        "variables": variables,
        "scenarios": scenarios,
        "scenario_instances": scenario_instances,
        "base_instance": base_instance,
    }


def solve_saa_model(
    model_bundle: ModelBundle,
    *,
    verbose: bool = False,
    time_limit: int | None = 300,
) -> dict[str, Any]:
    """Solve the SAA MILP and extract the first-stage strategy."""
    problem = model_bundle["problem"]
    solver = pulp.PULP_CBC_CMD(msg=1 if verbose else 0, timeLimit=time_limit)
    problem.solve(solver)

    acquisition = model_bundle["variables"]["A"]
    sellers = model_bundle["variables"]["V"]
    leaders = model_bundle["variables"]["L"]
    base_instance = model_bundle["base_instance"]

    def _val(variable: Any) -> float:
        value = pulp.value(variable)
        return 0.0 if value is None else float(value)

    strategy = {
        "A": {key: _val(var) for key, var in acquisition.items()},
        "V": {t: _val(var) for t, var in sellers.items()},
        "L": {t: _val(var) for t, var in leaders.items()},
    }
    return {
        "status": pulp.LpStatus[problem.status],
        "expected_objective": pulp.value(problem.objective),
        "strategy": strategy,
        "base_instance": base_instance,
        "problem": problem,
    }


def solve_stochastic_plan(
    config: dict[str, Any],
    scenarios: list[Scenario],
    *,
    verbose: bool = False,
    time_limit: int | None = 300,
) -> dict[str, Any]:
    """Build and solve the Phase-A SAA model for ``config``."""
    bundle = build_saa_model(config, scenarios)
    return solve_saa_model(bundle, verbose=verbose, time_limit=time_limit)

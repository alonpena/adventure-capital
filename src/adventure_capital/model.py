"""PuLP/CBC accelerated growth optimization model."""

from __future__ import annotations

import math
from typing import Any

import pulp


ModelBundle = dict[str, Any]


def build_model(instance: dict[str, Any]) -> ModelBundle:
    """Build full-horizon MILP.

    Months 1-12 acquisition fixed from A_base. Months 13-H optimized.
    """
    horizon = instance["H"]
    service_count = instance["S"]
    periods = instance["T"]
    services = instance["servicios"]

    problem = pulp.LpProblem("optimizacion_pca", pulp.LpMaximize)

    acquisition = {
        (s, t): pulp.LpVariable(f"A_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    sellers = {t: pulp.LpVariable(f"V_{t}", lowBound=0, cat="Integer") for t in periods}
    leaders = {t: pulp.LpVariable(f"L_{t}", lowBound=0, cat="Integer") for t in periods}
    op_steps = {
        (s, t): pulp.LpVariable(f"m_op_{s}_{t}", lowBound=0, cat="Integer")
        for s in range(service_count)
        for t in periods
    }
    active_clients = {
        (s, t): pulp.LpVariable(f"C_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    cash = {t: pulp.LpVariable(f"Caja_{t}", lowBound=None) for t in periods}
    recurring_sales = {
        (s, t): pulp.LpVariable(f"R_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    total_services = {
        (s, t): pulp.LpVariable(f"Q_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    revenue = {
        (s, t): pulp.LpVariable(f"I_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    operational_cost = {
        (s, t): pulp.LpVariable(f"Cost_op_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    cac = {t: pulp.LpVariable(f"CAC_{t}", lowBound=0) for t in periods}
    ebitda = {t: pulp.LpVariable(f"EBITDA_{t}", lowBound=None) for t in periods}

    problem += pulp.lpSum(instance["descuento"][t] * ebitda[t] for t in periods), "FO_VPL_EBITDA"

    for s in range(service_count):
        for t in instance["T_base"]:
            problem += acquisition[(s, t)] == instance["A_base"][(s, t)]

    growth_limit = instance["g_max_suavizado"]
    for s in range(service_count):
        base_average = sum(instance["A_base"][(s, t)] for t in instance["T_base"]) / len(instance["T_base"])
        transition_base = max(instance["A_base"][(s, 12)], base_average)
        problem += acquisition[(s, 13)] <= (1 + growth_limit) * transition_base
        problem += acquisition[(s, 14)] <= (1 + growth_limit) * acquisition[(s, 13)]
        for t in range(15, horizon + 1):
            problem += acquisition[(s, t)] <= ((1 + growth_limit) / 3) * (
                acquisition[(s, t - 1)] + acquisition[(s, t - 2)] + acquisition[(s, t - 3)]
            )

    for s in range(service_count):
        for t in periods:
            problem += active_clients[(s, t)] == pulp.lpSum(
                instance["phi"].get((s, cohort, t), 0.0) * acquisition[(s, cohort)]
                for cohort in range(1, t + 1)
            )
            problem += recurring_sales[(s, t)] == pulp.lpSum(
                instance["delta"].get((s, cohort, t), 0)
                * instance["phi"].get((s, cohort, t), 0.0)
                * instance["alpha"].get((s, t), 0.0)
                * acquisition[(s, cohort)]
                for cohort in range(1, t)
            )
            problem += total_services[(s, t)] == acquisition[(s, t)] + recurring_sales[(s, t)]
            problem += revenue[(s, t)] == services[s]["ticket"] * total_services[(s, t)]
            problem += total_services[(s, t)] <= services[s]["u_max"] * op_steps[(s, t)]
            problem += operational_cost[(s, t)] >= services[s]["c_u"] * total_services[(s, t)]
            problem += operational_cost[(s, t)] >= services[s]["c_min"] * op_steps[(s, t)]

    for t in periods:
        if t <= 12:
            base_acquisition = sum(instance["A_base"][(s, t)] for s in range(service_count))
            fixed_sellers = math.ceil(base_acquisition / instance["meta"]) if base_acquisition > 0 else 0
            fixed_leaders = math.ceil(fixed_sellers / instance["sup"]) if fixed_sellers > 0 else 0
            problem += sellers[t] == fixed_sellers
            problem += leaders[t] == fixed_leaders
        else:
            lag = instance.get("commercial_productivity_lag", 0)
            capacity_period = max(1, t - lag)
            problem += pulp.lpSum(acquisition[(s, t)] for s in range(service_count)) <= instance["meta"] * sellers[capacity_period]
            problem += sellers[t] <= instance["sup"] * leaders[t]

        problem += cac[t] == (
            instance["rem_v"] * sellers[t]
            + instance["rem_l"] * leaders[t]
            + pulp.lpSum(
                (instance["com_v"] + instance["com_l"]) * services[s]["ticket"] * acquisition[(s, t)]
                for s in range(service_count)
            )
        )
        problem += ebitda[t] == (
            pulp.lpSum(revenue[(s, t)] for s in range(service_count))
            - pulp.lpSum(operational_cost[(s, t)] for s in range(service_count))
            - cac[t]
            - instance["g_adm"]
            - instance["RRHH"][t]
        )

    for t in periods:
        if t >= 13:
            problem += sellers[t] >= sellers[t - 1]
            problem += leaders[t] >= leaders[t - 1]

    problem += cash[1] == instance["VC"] + ebitda[1]
    for t in periods:
        if t > 1:
            problem += cash[t] == cash[t - 1] + ebitda[t]

    liquidity_policy = instance.get("parametros", {}).get("liquidity_policy", {"type": "none"})
    policy_type = liquidity_policy.get("type", "none")
    if policy_type == "nonnegative":
        for t in periods:
            problem += cash[t] >= 0
    elif policy_type == "minimum_cash":
        floor = float(liquidity_policy.get("value", 0.0))
        for t in periods:
            problem += cash[t] >= floor
    elif policy_type != "none":
        raise ValueError(f"Unsupported liquidity policy: {policy_type}")

    variables = {
        "A": acquisition,
        "C": active_clients,
        "R": recurring_sales,
        "Q": total_services,
        "I": revenue,
        "V": sellers,
        "L": leaders,
        "m_op": op_steps,
        "Cost_op": operational_cost,
        "CAC": cac,
        "EBITDA": ebitda,
        "Caja": cash,
    }
    return {"problem": problem, "variables": variables}


def solve_model(
    model_bundle: ModelBundle,
    *,
    solver_name: str = "cbc",
    verbose: bool = False,
    time_limit: int | None = 120,
) -> dict[str, Any]:
    """Solve built MILP with configured solver."""
    if solver_name.lower() != "cbc":
        raise ValueError(f"Unsupported solver: {solver_name}")

    problem = model_bundle["problem"]
    solver = pulp.PULP_CBC_CMD(msg=1 if verbose else 0, timeLimit=time_limit)
    problem.solve(solver)
    return {
        "status": pulp.LpStatus[problem.status],
        "objective": pulp.value(problem.objective),
        "problem": problem,
        "variables": model_bundle["variables"],
    }


def solve_growth_plan(
    instance: dict[str, Any],
    *,
    verbose: bool | None = None,
    time_limit: int | None = None,
) -> dict[str, Any]:
    """Build and solve full-horizon growth plan."""
    solver_config = instance.get("parametros", {}).get("solver", {})
    model_bundle = build_model(instance)
    return solve_model(
        model_bundle,
        solver_name=solver_config.get("name", "cbc"),
        verbose=solver_config.get("verbose", False) if verbose is None else verbose,
        time_limit=solver_config.get("time_limit", 120) if time_limit is None else time_limit,
    )


# Legacy Spanish API alias.
def construir_y_resolver_modelo(inst: dict[str, Any], verbose: bool = False, time_limit: int = 120):
    solution = solve_growth_plan(inst, verbose=verbose, time_limit=time_limit)
    return solution["status"], solution["problem"], solution["variables"]

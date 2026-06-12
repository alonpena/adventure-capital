"""PuLP/CBC accelerated growth optimization model."""

from __future__ import annotations

import math
from typing import Any

import pulp


ModelBundle = dict[str, Any]


def build_model(instance: dict[str, Any], *, elastic_floor: bool = False) -> ModelBundle:
    """Build full-horizon MILP.

    Months 1-12 acquisition fixed from A_base. Months 13-H optimized.

    When ``elastic_floor`` is True (diagnostic mode), the hard working-capital floor is
    relaxed with non-negative shortfall variables and the objective is replaced by
    minimizing total shortfall. This is used only to measure the financing gap after the
    main model is infeasible; it never mutates the main model.
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

    # Channel split (Phase 2). A[s,t] = A_sf[s,t] + A_ad[s,t] + A_tp[s,t].
    # Salesforce variables always exist (mechanical refactor); advertising and
    # third-party variables exist only when those channels are active.
    channels = instance.get("channels", {})
    sf_active = channels.get("salesforce", {}).get("active", True)
    ad_active = channels.get("advertising", {}).get("active", False)
    tp_active = channels.get("third_party", {}).get("active", False)

    acq_sf = {
        (s, t): pulp.LpVariable(f"A_sf_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    acq_ad = (
        {
            (s, t): pulp.LpVariable(f"A_ad_{s}_{t}", lowBound=0)
            for s in range(service_count)
            for t in periods
        }
        if ad_active
        else {}
    )
    acq_tp = (
        {
            (s, t): pulp.LpVariable(f"A_tp_{s}_{t}", lowBound=0)
            for s in range(service_count)
            for t in periods
        }
        if tp_active
        else {}
    )
    ad_investment = (
        {t: pulp.LpVariable(f"I_ad_{t}", lowBound=0) for t in periods} if ad_active else {}
    )
    advertising_cac_cost = (
        {t: pulp.LpVariable(f"adv_cac_{t}", lowBound=0) for t in periods} if ad_active else {}
    )
    salesforce_cac_cost = {t: pulp.LpVariable(f"sf_cac_{t}", lowBound=0) for t in periods}
    third_party_cost = (
        {t: pulp.LpVariable(f"tp_cac_{t}", lowBound=0) for t in periods} if tp_active else {}
    )
    total_acquisition_cost = {t: pulp.LpVariable(f"tot_cac_{t}", lowBound=0) for t in periods}

    def sf_term(s, t):
        return acq_sf[(s, t)]

    def ad_term(s, t):
        return acq_ad[(s, t)] if ad_active else 0

    def tp_term(s, t):
        return acq_tp[(s, t)] if tp_active else 0

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

    # Optional logarithmic acquisition ceiling: additional upper bound on TOTAL
    # acquisition across all services for t >= 13. Does not replace smoothing.
    log_ceiling = instance.get("log_ceiling", {})
    ceiling_slack = instance.get("ceiling_slack", 0.0)
    for t, ceiling_value in log_ceiling.items():
        problem += pulp.lpSum(
            acquisition[(s, t)] for s in range(service_count)
        ) <= ceiling_value * (1 + ceiling_slack)

    # Channel split identity and per-channel mechanics (Phase 2).
    for s in range(service_count):
        for t in periods:
            problem += acquisition[(s, t)] == sf_term(s, t) + ad_term(s, t) + tp_term(s, t)
            if not sf_active:
                problem += acq_sf[(s, t)] == 0

    if ad_active:
        ad_params = channels["advertising"]
        a_coef = ad_params["a"]
        b_coef = ad_params["b"]
        i_min = ad_params["I_min"]
        i_max = ad_params["I_max"]
        a_ad_cap = ad_params["A_ad_cap"]
        for t in periods:
            ad_total_t = pulp.lpSum(acq_ad[(s, t)] for s in range(service_count))
            # Linear advertising recta holds every period; investment range applies
            # only to the optimized horizon (year 1 is the exogenous fixed period).
            problem += ad_total_t == a_coef + b_coef * ad_investment[t]
            problem += ad_total_t <= a_ad_cap
            problem += advertising_cac_cost[t] == ad_investment[t]
            if t >= 13:
                problem += ad_investment[t] >= i_min
                problem += ad_investment[t] <= i_max

    # Linear channel share bounds (parameters * variable total; no bilinearities).
    if channels.get("any_split", ad_active or tp_active):
        channel_totals = {
            "salesforce": lambda t: pulp.lpSum(sf_term(s, t) for s in range(service_count)),
            "advertising": lambda t: pulp.lpSum(ad_term(s, t) for s in range(service_count)),
            "third_party": lambda t: pulp.lpSum(tp_term(s, t) for s in range(service_count)),
        }
        for name, total_fn in channel_totals.items():
            ch = channels.get(name, {})
            if not ch.get("active", False):
                continue
            min_share = ch.get("min_share", 0.0)
            max_share = ch.get("max_share", 1.0)
            for t in periods:
                a_total_t = pulp.lpSum(acquisition[(s, t)] for s in range(service_count))
                if min_share > 0.0:
                    problem += total_fn(t) >= min_share * a_total_t
                if max_share < 1.0:
                    problem += total_fn(t) <= max_share * a_total_t

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
        if not sf_active:
            # Advertising-/third-party-only models carry no salesforce.
            problem += sellers[t] == 0
            problem += leaders[t] == 0
        elif t <= 12:
            base_acquisition = sum(instance["A_base"][(s, t)] for s in range(service_count))
            fixed_sellers = math.ceil(base_acquisition / instance["meta"]) if base_acquisition > 0 else 0
            fixed_leaders = math.ceil(fixed_sellers / instance["sup"]) if fixed_sellers > 0 else 0
            problem += sellers[t] == fixed_sellers
            problem += leaders[t] == fixed_leaders
        else:
            lag = instance.get("commercial_productivity_lag", 0)
            capacity_period = max(1, t - lag)
            # Salesforce capacity binds only salesforce acquisition, not total.
            problem += pulp.lpSum(sf_term(s, t) for s in range(service_count)) <= instance["meta"] * sellers[capacity_period]
            problem += sellers[t] <= instance["sup"] * leaders[t]

        # CAC cost components (linear; ratios are computed post-solve in results.py).
        problem += salesforce_cac_cost[t] == (
            instance["rem_v"] * sellers[t]
            + instance["rem_l"] * leaders[t]
            + pulp.lpSum(
                (instance["com_v"] + instance["com_l"]) * services[s]["ticket"] * sf_term(s, t)
                for s in range(service_count)
            )
        )
        if tp_active:
            tp_commission = channels["third_party"]["commission"]
            problem += third_party_cost[t] == pulp.lpSum(
                tp_commission * services[s]["ticket"] * acq_tp[(s, t)]
                for s in range(service_count)
            )
        problem += total_acquisition_cost[t] == (
            salesforce_cac_cost[t]
            + (advertising_cac_cost[t] if ad_active else 0)
            + (third_party_cost[t] if tp_active else 0)
        )
        # CAC remains the canonical alias for total acquisition cost.
        problem += cac[t] == total_acquisition_cost[t]
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

    params = instance.get("parametros", {})
    working_capital = params.get("working_capital", {})
    cash_shortfall: dict[int, Any] = {}
    if working_capital.get("enabled", False):
        # Working-capital floor indexed to the financing ticket: cash may fall to -VC
        # (all financing consumed) but no further. Supersedes liquidity_policy.
        floor_value = -float(instance["VC"])
        if elastic_floor:
            cash_shortfall = {
                t: pulp.LpVariable(f"cash_shortfall_{t}", lowBound=0) for t in periods
            }
            for t in periods:
                problem += cash[t] + cash_shortfall[t] >= floor_value
            # Diagnostic objective: minimize total financing shortfall (separate from
            # the main discounted-EBITDA objective).
            problem.setObjective(pulp.lpSum(cash_shortfall[t] for t in periods))
            problem.sense = pulp.LpMinimize
        else:
            for t in periods:
                problem += cash[t] >= floor_value
    else:
        liquidity_policy = params.get("liquidity_policy", {"type": "none"})
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
        "A_sf": acq_sf,
        "A_ad": acq_ad,
        "A_tp": acq_tp,
        "I_ad": ad_investment,
        "advertising_cac_cost": advertising_cac_cost,
        "salesforce_cac_cost": salesforce_cac_cost,
        "third_party_cost": third_party_cost,
        "total_acquisition_cost": total_acquisition_cost,
        "cash_shortfall": cash_shortfall,
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


def diagnose_financing_gap(
    instance: dict[str, Any], *, time_limit: int | None = None
) -> dict[str, Any]:
    """Measure the working-capital financing gap via a secondary elastic solve.

    Builds a fresh diagnostic model (hard floor relaxed with non-negative shortfall,
    objective = minimize total shortfall). Does not touch the main model.
    """
    solver_config = instance.get("parametros", {}).get("solver", {})
    bundle = build_model(instance, elastic_floor=True)
    solution = solve_model(
        bundle,
        solver_name=solver_config.get("name", "cbc"),
        verbose=False,
        time_limit=solver_config.get("time_limit", 120) if time_limit is None else time_limit,
    )
    shortfall = solution["variables"]["cash_shortfall"]
    periods = instance["T"]
    values = {t: max(0.0, _shortfall_value(shortfall[t])) for t in periods}
    breaches = [t for t in periods if values[t] > 1e-6]
    return {
        "feasible": False,
        "financing_gap_usd": max(values.values()) if values else 0.0,
        "first_breach_month": breaches[0] if breaches else None,
        "total_gap": float(sum(values.values())),
        "diagnostic_status": solution["status"],
    }


def solve_with_working_capital(
    instance: dict[str, Any], *, verbose: bool | None = None, time_limit: int | None = None
) -> dict[str, Any]:
    """Solve the main model; on infeasibility, run the financing-gap diagnostic.

    Returns a structured dict for due diligence. The pipeline does not break: a feasible
    run continues normally, an infeasible run reports the gap.
    """
    solution = solve_growth_plan(instance, verbose=verbose, time_limit=time_limit)
    if solution["status"] == "Optimal":
        cash = solution["variables"]["Caja"]
        periods = instance["T"]
        cash_values = {t: _shortfall_value(cash[t]) for t in periods}
        min_month = min(periods, key=lambda t: cash_values[t])
        return {
            "feasible": True,
            "min_cash_balance": cash_values[min_month],
            "min_cash_month": min_month,
            "financing_gap_usd": 0.0,
            "solution": solution,
        }
    diagnostic = diagnose_financing_gap(instance, time_limit=time_limit)
    diagnostic["solution"] = solution
    return diagnostic


def _shortfall_value(variable: Any) -> float:
    value = pulp.value(variable)
    return 0.0 if value is None else float(value)


# Legacy Spanish API alias.
def construir_y_resolver_modelo(inst: dict[str, Any], verbose: bool = False, time_limit: int = 120):
    solution = solve_growth_plan(inst, verbose=verbose, time_limit=time_limit)
    return solution["status"], solution["problem"], solution["variables"]

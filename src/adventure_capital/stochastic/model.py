"""Canonical M4 two-stage SAA stochastic MILP with channel parity + CVaR.

This solves the *same* commercial/financial problem as the deterministic PCA
(``adventure_capital.model``) but under uncertainty:

- First-stage (shared across scenarios): the committed growth plan
  ``V[t]``, ``L[t]``, ``I_ad[t]`` and the per-channel acquisition plans
  ``A_sf_plan``, ``A_ad_plan``, ``A_tp_plan`` (months 13..H). Months 1-12 stay
  fixed from ``A_base`` (salesforce-only, unperturbed).
- Recourse (per scenario ``w``): realized acquisition equals the plan scaled by
  the scenario's per-channel efficiency multiplier, so active clients
  ``C[s,t,w]`` and all downstream financials vary by scenario.
- Objective: conditional value at risk of the per-scenario VAN
  (``CVaR_alpha(VAN)``), with a tiny expected-VAN tie-break.

The investment ticket ``VC`` is fixed across scenarios (ADR 0009): financing
stress is measured through funding gap and runway, not by changing capital.

This module does not import or modify the deterministic ``model.py``; it reuses
``generate_instance`` to derive per-scenario survival/discount data. See
``docs/M4_STOCHASTIC_PARITY_PLAN.md`` and ADR 0009.
"""

from __future__ import annotations

import math
from typing import Any

import pulp

from adventure_capital.instance import generate_instance
from adventure_capital.stochastic.defaults import M4_DEFAULTS
from adventure_capital.stochastic.scenarios import Scenario, apply_scenario

ModelBundle = dict[str, Any]

_FIXED_MONTHS = 12


def _stochastic_block(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("stochastic", {}) or {}


def _terminal_multiple(config: dict[str, Any]) -> float:
    return float(_stochastic_block(config).get("terminal_multiple", 1.0))


def _cvar_alpha(config: dict[str, Any]) -> float:
    alpha = float(_stochastic_block(config).get("cvar_alpha", M4_DEFAULTS["cvar_alpha"]))
    if not (0.0 < alpha <= 1.0):
        raise ValueError(f"cvar_alpha must be in (0, 1], got {alpha}.")
    return alpha


def _mean_cvar_lambda(config: dict[str, Any]) -> float:
    """Mean-CVaR weight (ADR 0011). lambda=0 -> pure CVaR (worst-tail only);
    lambda=1 -> risk-neutral expectation. Default 0.5: robust without leaving
    expected value on the table."""
    lam = float(_stochastic_block(config).get("mean_cvar_lambda", M4_DEFAULTS["mean_cvar_lambda"]))
    if not (0.0 <= lam <= 1.0):
        raise ValueError(f"mean_cvar_lambda must be in [0, 1], got {lam}.")
    return lam


def _commission_periods(config: dict[str, Any]) -> int:
    block = _stochastic_block(config).get("third_party_defaults", {}) or {}
    return int(
        block.get(
            "commission_periods",
            M4_DEFAULTS["third_party_defaults"]["commission_periods"],
        )
    )


def build_saa_model(config: dict[str, Any], scenarios: list[Scenario]) -> ModelBundle:
    """Build the channel-parity SAA MILP for ``config`` over ``scenarios``."""
    if not scenarios:
        raise ValueError("At least one scenario is required.")

    base_instance = generate_instance(config)
    horizon = base_instance["H"]
    service_count = base_instance["S"]
    periods = base_instance["T"]
    services = base_instance["servicios"]
    fixed_periods = base_instance["T_base"]
    lag = base_instance["commercial_productivity_lag"]
    terminal_multiple = _terminal_multiple(config)
    tax_rate = float(base_instance["tax"])
    vc = float(base_instance["VC"])
    floor = -vc  # working-capital floor indexed to the financing ticket.

    channels = base_instance["channels"]
    ad_active = bool(channels["advertising"]["active"])
    tp_active = bool(channels["third_party"]["active"])
    commission_periods = _commission_periods(config)

    # Churn/WACC enter through per-scenario instances; channel efficiencies are
    # applied directly to the plan below (not folded into the config).
    scenario_instances = [generate_instance(apply_scenario(config, sc)) for sc in scenarios]
    scenario_keys = list(range(len(scenarios)))

    problem = pulp.LpProblem("optimizacion_pca_estocastico", pulp.LpMaximize)

    # ----- First-stage plan variables (shared across scenarios) -----
    plan_sf = {
        (s, t): pulp.LpVariable(f"A_sf_plan_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    plan_ad = (
        {
            (s, t): pulp.LpVariable(f"A_ad_plan_{s}_{t}", lowBound=0)
            for s in range(service_count)
            for t in periods
        }
        if ad_active
        else {}
    )
    plan_tp = (
        {
            (s, t): pulp.LpVariable(f"A_tp_plan_{s}_{t}", lowBound=0)
            for s in range(service_count)
            for t in periods
        }
        if tp_active
        else {}
    )
    plan_total = {
        (s, t): pulp.LpVariable(f"A_plan_{s}_{t}", lowBound=0)
        for s in range(service_count)
        for t in periods
    }
    sellers = {t: pulp.LpVariable(f"V_{t}", lowBound=0, cat="Integer") for t in periods}
    leaders = {t: pulp.LpVariable(f"L_{t}", lowBound=0, cat="Integer") for t in periods}
    ad_investment = {t: pulp.LpVariable(f"I_ad_{t}", lowBound=0) for t in periods}

    def sf_plan(s: int, t: int) -> Any:
        return plan_sf[(s, t)]

    def ad_plan(s: int, t: int) -> Any:
        return plan_ad[(s, t)] if ad_active else 0

    def tp_plan(s: int, t: int) -> Any:
        return plan_tp[(s, t)] if tp_active else 0

    # ----- First-stage: months 1-12 fixed from A_base (salesforce only) -----
    for s in range(service_count):
        for t in fixed_periods:
            base = base_instance["A_base"][(s, t)]
            problem += plan_sf[(s, t)] == base
            problem += plan_total[(s, t)] == base
            if ad_active:
                problem += plan_ad[(s, t)] == 0
            if tp_active:
                problem += plan_tp[(s, t)] == 0
    for t in fixed_periods:
        base_acq = sum(base_instance["A_base"][(s, t)] for s in range(service_count))
        fixed_sellers = math.ceil(base_acq / base_instance["meta"]) if base_acq > 0 else 0
        fixed_leaders = math.ceil(fixed_sellers / base_instance["sup"]) if fixed_sellers > 0 else 0
        problem += sellers[t] == fixed_sellers
        problem += leaders[t] == fixed_leaders
        problem += ad_investment[t] == 0

    # ----- First-stage: plan identity (months 13..H) -----
    for s in range(service_count):
        for t in periods:
            problem += plan_total[(s, t)] == sf_plan(s, t) + ad_plan(s, t) + tp_plan(s, t)

    # ----- First-stage: logarithmic growth ceiling (ADR 0010/0011 parity) -----
    # The deterministic active-stock saturation ceiling replaces the legacy
    # moving-average smoothing. Bounds TOTAL plan acquisition for t >= 13.
    log_ceiling = base_instance.get("log_ceiling", {})
    ceiling_slack = base_instance.get("ceiling_slack", 0.0)
    for t, ceiling_value in log_ceiling.items():
        problem += pulp.lpSum(
            plan_total[(s, t)] for s in range(service_count)
        ) <= ceiling_value * (1 + ceiling_slack)

    # ----- First-stage: commercial team + salesforce capacity (months 13..H) -----
    for t in periods:
        if t <= _FIXED_MONTHS:
            continue
        capacity_period = max(1, t - lag)
        problem += pulp.lpSum(
            sf_plan(s, t) for s in range(service_count)
        ) <= base_instance["meta"] * sellers[capacity_period]
        problem += sellers[t] <= base_instance["sup"] * leaders[t]
        problem += sellers[t] >= sellers[t - 1]
        problem += leaders[t] >= leaders[t - 1]

    # ----- First-stage: hiring friction (ADR 0014, opt-in, default off) -----
    # Parity with the deterministic model: caps the monthly headcount jump on
    # the shared first-stage V/L plan. Strict no-op when disabled.
    hiring = base_instance.get("hiring", {})
    if bool(hiring.get("enabled", False)):
        max_new_sellers = hiring["max_new_sellers_per_month"]
        max_new_leaders = hiring["max_new_leaders_per_month"]
        for t in periods:
            if t <= _FIXED_MONTHS:
                continue
            problem += sellers[t] <= sellers[t - 1] + max_new_sellers
            problem += leaders[t] <= leaders[t - 1] + max_new_leaders

    # ----- First-stage: advertising recta + cap (months 13..H) -----
    if ad_active:
        ad = channels["advertising"]
        a_coef, b_coef = ad["a"], ad["b"]
        i_min, i_max, a_ad_cap = ad["I_min"], ad["I_max"], ad["A_ad_cap"]
        for t in periods:
            if t <= _FIXED_MONTHS:
                continue
            ad_total_t = pulp.lpSum(plan_ad[(s, t)] for s in range(service_count))
            problem += ad_total_t == a_coef + b_coef * ad_investment[t]
            problem += ad_total_t <= a_ad_cap
            problem += ad_investment[t] >= i_min
            problem += ad_investment[t] <= i_max

    # ----- First-stage: channel share bounds on the plan (months 13..H) -----
    if channels.get("any_split", ad_active or tp_active):
        channel_plan = {
            "salesforce": lambda t: pulp.lpSum(sf_plan(s, t) for s in range(service_count)),
            "advertising": lambda t: pulp.lpSum(ad_plan(s, t) for s in range(service_count)),
            "third_party": lambda t: pulp.lpSum(tp_plan(s, t) for s in range(service_count)),
        }
        for name, total_fn in channel_plan.items():
            ch = channels.get(name, {})
            if not ch.get("active", False):
                continue
            min_share = ch.get("min_share", 0.0)
            max_share = ch.get("max_share", 1.0)
            for t in periods:
                if t <= _FIXED_MONTHS:
                    continue
                plan_t = pulp.lpSum(plan_total[(s, t)] for s in range(service_count))
                if min_share > 0.0:
                    problem += total_fn(t) >= min_share * plan_t
                if max_share < 1.0:
                    problem += total_fn(t) <= max_share * plan_t

    # ----- First-stage: growth commitment (ADR 0014, opt-in, default off) -----
    # Parity with the deterministic model, but the floor binds on the PLANNED
    # (pre-efficiency, first-stage) client stock, not the realized per-scenario
    # stock — the here-and-now decision is the plan, so the commitment is a
    # first-stage constraint like everything else in this block. The realized
    # P(C36_real >= multiple_3y*C12) is reported ex-post as a KPI (evaluate.py),
    # never enforced as a per-scenario constraint (that would break here-and-now).
    growth_commitment = base_instance.get("growth_commitment", {})
    if bool(growth_commitment.get("enabled", False)):
        checkpoint_targets = growth_commitment.get("checkpoint_targets", {})
        phi_base = base_instance["phi"]
        for checkpoint_month, target in checkpoint_targets.items():
            if checkpoint_month > horizon:
                raise ValueError(
                    f"growth_commitment checkpoint at month {checkpoint_month} exceeds "
                    f"H={horizon}: raise H or use checkpoints: terminal with H >= 36, or "
                    "disable growth_commitment for short horizons."
                )
            planned_stock = pulp.lpSum(
                phi_base.get((s, cohort, checkpoint_month), 0.0) * plan_total[(s, cohort)]
                for s in range(service_count)
                for cohort in range(1, checkpoint_month + 1)
            )
            problem += planned_stock >= target

    # ----- Realized acquisition expressions (per scenario, linear in plan) -----
    def a_sf_real(s: int, t: int, w: int) -> Any:
        if t <= _FIXED_MONTHS:
            return plan_total[(s, t)]  # salesforce-only base, unperturbed
        return scenarios[w].salesforce_efficiency * plan_sf[(s, t)]

    def a_ad_real(s: int, t: int, w: int) -> Any:
        if not ad_active or t <= _FIXED_MONTHS:
            return 0
        return scenarios[w].advertising_efficiency * plan_ad[(s, t)]

    def a_tp_real(s: int, t: int, w: int) -> Any:
        if not tp_active or t <= _FIXED_MONTHS:
            return 0
        return scenarios[w].third_party_efficiency * plan_tp[(s, t)]

    def a_real(s: int, t: int, w: int) -> Any:
        return a_sf_real(s, t, w) + a_ad_real(s, t, w) + a_tp_real(s, t, w)

    # ----- Recourse variables (per scenario) -----
    op_steps = {
        (s, t, w): pulp.LpVariable(f"m_op_{s}_{t}_{w}", lowBound=0, cat="Integer")
        for s in range(service_count)
        for t in periods
        for w in scenario_keys
    }
    operational_cost = {
        (s, t, w): pulp.LpVariable(f"Cost_op_{s}_{t}_{w}", lowBound=0)
        for s in range(service_count)
        for t in periods
        for w in scenario_keys
    }
    cac = {(t, w): pulp.LpVariable(f"CAC_{t}_{w}", lowBound=0) for t in periods for w in scenario_keys}
    ebitda = {
        (t, w): pulp.LpVariable(f"EBITDA_{t}_{w}", lowBound=None)
        for t in periods
        for w in scenario_keys
    }
    tax = {(t, w): pulp.LpVariable(f"Tax_{t}_{w}", lowBound=0) for t in periods for w in scenario_keys}
    fcf = {(t, w): pulp.LpVariable(f"FCF_{t}_{w}", lowBound=None) for t in periods for w in scenario_keys}
    cash = {(t, w): pulp.LpVariable(f"Caja_{t}_{w}", lowBound=None) for t in periods for w in scenario_keys}
    funding_gap = {
        (t, w): pulp.LpVariable(f"Gap_{t}_{w}", lowBound=0) for t in periods for w in scenario_keys
    }
    van = {w: pulp.LpVariable(f"VAN_{w}", lowBound=None) for w in scenario_keys}

    # ----- Per-scenario recourse constraints + financials -----
    for w in scenario_keys:
        inst = scenario_instances[w]
        phi, delta, alpha = inst["phi"], inst["delta"], inst["alpha"]
        discount = inst["descuento"]

        for s in range(service_count):
            ticket = services[s]["ticket"]
            for t in periods:
                recurring = pulp.lpSum(
                    delta.get((s, cohort, t), 0)
                    * phi.get((s, cohort, t), 0.0)
                    * alpha.get((s, t), 0.0)
                    * a_real(s, cohort, w)
                    for cohort in range(1, t)
                )
                q_expr = a_real(s, t, w) + recurring
                problem += q_expr <= services[s]["u_max"] * op_steps[(s, t, w)]
                problem += operational_cost[(s, t, w)] >= services[s]["c_u"] * q_expr
                problem += operational_cost[(s, t, w)] >= services[s]["c_min"] * op_steps[(s, t, w)]

        for t in periods:
            # CAC: salesforce remuneration/commission + advertising spend +
            # third-party cohort-revenue commission window.
            cac_sf = (
                inst["rem_v"] * sellers[t]
                + inst["rem_l"] * leaders[t]
                + pulp.lpSum(
                    (inst["com_v"] + inst["com_l"]) * services[s]["ticket"] * a_sf_real(s, t, w)
                    for s in range(service_count)
                )
            )
            cac_ad = ad_investment[t] if ad_active else 0
            cac_tp = 0
            if tp_active:
                commission = channels["third_party"]["commission"]
                window_terms = []
                low = max(1, t - commission_periods + 1)
                for s in range(service_count):
                    ticket = services[s]["ticket"]
                    for cohort in range(low, t + 1):
                        if cohort == t:
                            units = a_tp_real(s, cohort, w)
                        else:
                            units = (
                                delta.get((s, cohort, t), 0)
                                * phi.get((s, cohort, t), 0.0)
                                * alpha.get((s, t), 0.0)
                                * a_tp_real(s, cohort, w)
                            )
                        window_terms.append(ticket * units)
                cac_tp = commission * pulp.lpSum(window_terms)

            problem += cac[(t, w)] == cac_sf + cac_ad + cac_tp

            revenue_t = pulp.lpSum(
                services[s]["ticket"] * (a_real(s, t, w) + pulp.lpSum(
                    delta.get((s, cohort, t), 0)
                    * phi.get((s, cohort, t), 0.0)
                    * alpha.get((s, t), 0.0)
                    * a_real(s, cohort, w)
                    for cohort in range(1, t)
                ))
                for s in range(service_count)
            )
            problem += ebitda[(t, w)] == (
                revenue_t
                - pulp.lpSum(operational_cost[(s, t, w)] for s in range(service_count))
                - cac[(t, w)]
                - inst["g_adm"]
                - inst["RRHH"][t]
            )
            # Linear tax: solver minimizes Tax >= max(tax*EBITDA, 0) under max objective.
            problem += tax[(t, w)] >= tax_rate * ebitda[(t, w)]
            problem += fcf[(t, w)] == ebitda[(t, w)] - tax[(t, w)]

        # Cash recursion uses EBITDA (pre-tax); VAN discounts FCF (post-tax).
        problem += cash[(1, w)] == vc + ebitda[(1, w)]
        for t in periods:
            if t > 1:
                problem += cash[(t, w)] == cash[(t - 1, w)] + ebitda[(t, w)]
            problem += funding_gap[(t, w)] >= floor - cash[(t, w)]

        terminal = discount[horizon] * terminal_multiple * 12 * ebitda[(horizon, w)]
        problem += van[w] == (
            -vc
            + pulp.lpSum(discount[t] * fcf[(t, w)] for t in periods)
            + terminal
        )

    # ----- Mean-CVaR objective (ADR 0011) -----
    # maximize  lambda*E[VAN] + (1-lambda)*CVaR_alpha(VAN). lambda is a real risk
    # knob (replaces the negligible 1e-6 expected-VAN tie-break): it recovers
    # expected value left on the table by pure CVaR at flat worst-case cost.
    alpha_cvar = _cvar_alpha(config)
    lam = _mean_cvar_lambda(config)
    eta = pulp.LpVariable("eta", lowBound=None)
    z = {w: pulp.LpVariable(f"z_{w}", lowBound=0) for w in scenario_keys}
    for w in scenario_keys:
        problem += z[w] >= eta - van[w]
    cvar = eta - (1.0 / alpha_cvar) * pulp.lpSum(scenarios[w].probability * z[w] for w in scenario_keys)
    expected_van = pulp.lpSum(scenarios[w].probability * van[w] for w in scenario_keys)
    problem += lam * expected_van + (1.0 - lam) * cvar, "FO_mean_CVaR_VAN"

    variables = {
        "A_sf_plan": plan_sf,
        "A_ad_plan": plan_ad,
        "A_tp_plan": plan_tp,
        "A_plan": plan_total,
        "V": sellers,
        "L": leaders,
        "I_ad": ad_investment,
        "VAN": van,
        "eta": eta,
        "z": z,
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
        "cvar_alpha": alpha_cvar,
        "mean_cvar_lambda": lam,
        "channels": {"advertising": ad_active, "third_party": tp_active},
    }


def solve_saa_model(
    model_bundle: ModelBundle,
    *,
    verbose: bool = False,
    time_limit: int | None = 300,
) -> dict[str, Any]:
    """Solve the SAA MILP and extract the first-stage strategy + risk metrics."""
    problem = model_bundle["problem"]
    solver = pulp.PULP_CBC_CMD(msg=1 if verbose else 0, timeLimit=time_limit)
    problem.solve(solver)

    variables = model_bundle["variables"]
    scenarios = model_bundle["scenarios"]

    def _val(variable: Any) -> float:
        value = pulp.value(variable)
        return 0.0 if value is None else float(value)

    def _plan(mapping: dict[Any, Any]) -> dict[str, float]:
        return {f"{key[0]}_{key[1]}": _val(var) for key, var in mapping.items()}

    strategy = {
        "A_sf_plan": _plan(variables["A_sf_plan"]),
        "A_ad_plan": _plan(variables["A_ad_plan"]),
        "A_tp_plan": _plan(variables["A_tp_plan"]),
        "A_plan": _plan(variables["A_plan"]),
        "V": {t: _val(var) for t, var in variables["V"].items()},
        "L": {t: _val(var) for t, var in variables["L"].items()},
        "I_ad": {t: _val(var) for t, var in variables["I_ad"].items()},
    }

    status = pulp.LpStatus[problem.status]
    van_values = {w: _val(var) for w, var in variables["VAN"].items()}
    expected_van = (
        sum(scenarios[w].probability * van_values[w] for w in van_values)
        if van_values
        else None
    )
    eta = _val(variables["eta"])
    alpha = model_bundle["cvar_alpha"]
    cvar_van = (
        eta - (1.0 / alpha) * sum(
            scenarios[w].probability * max(0.0, eta - van_values[w]) for w in van_values
        )
        if van_values
        else None
    )

    return {
        "status": status,
        "objective": "cvar_van",
        "cvar_alpha": alpha,
        "mean_cvar_lambda": model_bundle.get("mean_cvar_lambda"),
        "cvar_van": cvar_van,
        "expected_van": expected_van,
        # Back-compat: consumers historically read ``expected_objective``.
        "expected_objective": cvar_van,
        "strategy": strategy,
        "base_instance": model_bundle["base_instance"],
        "problem": problem,
    }


def solve_stochastic_plan(
    config: dict[str, Any],
    scenarios: list[Scenario],
    *,
    verbose: bool = False,
    time_limit: int | None = 300,
) -> dict[str, Any]:
    """Build and solve the SAA model for ``config``."""
    bundle = build_saa_model(config, scenarios)
    return solve_saa_model(bundle, verbose=verbose, time_limit=time_limit)

"""Model instance preprocessing."""

from __future__ import annotations

import math
from typing import Any

from adventure_capital.config import resolve_investment_thesis, validate_config


def generate_instance(config: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic model instance from raw config."""
    validate_config(config)

    H = config["H"]
    services = config["servicios"]
    service_count = len(services)
    annual_discount = config["beta"]
    monthly_discount = (1 + annual_discount) ** (1 / 12) - 1
    investment_thesis = resolve_investment_thesis(config)

    periods = list(range(1, H + 1))
    fixed_periods = list(range(1, 13))

    monthly_churn: dict[tuple[int, int], float] = {}
    for s, service in enumerate(services):
        for t in periods:
            year = min((t - 1) // 12, len(service["churn_anual"]) - 1)
            annual_churn = service["churn_anual"][year]
            monthly_churn[(s, t)] = 1 - (1 - annual_churn) ** (1 / 12)

    survival: dict[tuple[int, int, int], float] = {}
    for s in range(service_count):
        for cohort in periods:
            survival[(s, cohort, cohort)] = 1.0
            for t in range(cohort + 1, H + 1):
                survival[(s, cohort, t)] = survival[(s, cohort, t - 1)] * (
                    1 - monthly_churn[(s, t)]
                )

    repurchase_window: dict[tuple[int, int, int], int] = {}
    for s, service in enumerate(services):
        frequency = service["frecuencia"]
        for cohort in periods:
            for t in periods:
                repurchase_window[(s, cohort, t)] = int(
                    t > cohort and (t - cohort) % frequency == 0
                )

    alpha = {
        (s, t): service["alpha"]
        for s, service in enumerate(services)
        for t in periods
    }

    base_acquisition = {
        (s, t): float(service["A_base"][t - 1])
        for s, service in enumerate(services)
        for t in fixed_periods
    }

    hr = {}
    for t in periods:
        year = min((t - 1) // 12, len(config["RRHH_mensual"]) - 1)
        hr[t] = config["RRHH_mensual"][year]

    discount_factor = {t: 1 / (1 + monthly_discount) ** t for t in periods}

    # Logarithmic market-saturation growth law (ADR 0010). The PRIMARY, default-on
    # acquisition bound for t >= 13. The ANCHOR is the active client stock: by t = H the
    # projected net stock (clients, net of churn) reaches target_stock_multiplier x the
    # end-of-year-1 active stock (the VC "triple your clients" benchmark). The net stock
    # follows a logarithm (saturation); the per-period acquisition cap is the net stock
    # increment PLUS churn replacement, so it does not collapse in year 3.
    # Default-on: an absent block enables it with defaults; only an explicit
    # enabled: false opts out (then only physical/cash bounds remain). There is no
    # moving-average smoothing fallback.
    ceiling_config = config.get("acquisition_ceiling", {})
    log_ceiling: dict[int, float] = {}
    ceiling_slack = 0.0
    if ceiling_config.get("enabled", True):
        ceiling_slack = float(ceiling_config.get("slack", 0.15))
        target_multiplier = float(ceiling_config.get("target_stock_multiplier", 3.0))
        # Active client stock at end of year 1 (net of churn), aggregated over services.
        C_0 = sum(
            survival[(s, cohort, 12)] * base_acquisition[(s, cohort)]
            for s in range(service_count)
            for cohort in fixed_periods
        )
        if C_0 > 0:
            C_target = C_0 * target_multiplier
            H_post = H - 12  # months in years 2+ (post fixed-acquisition period)
            K = (C_target - C_0) / math.log(1 + H_post)
            # Aggregate monthly churn proxy (mean across services) for replacement.
            churn_agg = {
                t: sum(monthly_churn[(s, t)] for s in range(service_count)) / service_count
                for t in range(13, H + 1)
            }
            prev_stock = C_0
            for t in range(13, H + 1):
                stock_t = C_0 + K * math.log(1 + (t - 12))
                # Gross acquisition cap = net stock increment + churn replacement.
                gross = stock_t - prev_stock * (1 - churn_agg[t])
                log_ceiling[t] = max(0.0, gross)
                prev_stock = stock_t

    # Convex-CAC endogenous growth law (ADR 0013). Diminishing returns: per-period
    # acquisition is decomposed into batches of the year-1 run-rate, and each further
    # batch carries a rising marginal CAC premium base_cac * theta * k. Growth self-limits
    # where marginal CAC meets LTV (k* = (LTV/base_cac - 1)/theta), with no exogenous cap.
    convex_cfg = config.get("convex_cac", {})
    convex_enabled = bool(convex_cfg.get("enabled", False))
    convex: dict[str, Any] = {"enabled": convex_enabled}
    if convex_enabled:
        theta = float(convex_cfg.get("theta", 1.0))
        if theta <= 0.0:
            raise ValueError("convex_cac.theta must be > 0.")
        # Per-service LTV (representative cohort t=13), year-1 batch width, base CAC.
        ltv: dict[int, float] = {}
        batch: dict[int, float] = {}
        base_cac: dict[int, float] = {}
        ref = 13
        for s, service in enumerate(services):
            ticket = float(service["ticket"])
            a = float(service["alpha"])
            value = ticket
            for t in range(ref + 1, H + 1):
                value += (
                    ticket
                    * a
                    * repurchase_window.get((s, ref, t), 0)
                    * survival.get((s, ref, t), 0.0)
                    * discount_factor[t]
                    / discount_factor[ref]
                )
            ltv[s] = value
            batch[s] = max(
                1.0, sum(base_acquisition[(s, t)] for t in fixed_periods) / len(fixed_periods)
            )
            base_cac[s] = config["rem_v"] / config["meta"] + (
                config["com_v"] + config["com_l"]
            ) * ticket
        # Segment count must cover the economic limit k* = (LTV/base_cac - 1)/theta so the
        # number of batches never artificially caps growth; the economics (or capacity /
        # cash) bind first. Capped to bound model size.
        max_cap = int(convex_cfg.get("max_segments", 80))
        k_star = max(
            (ltv[s] / base_cac[s] - 1.0) / theta for s in range(service_count)
        )
        n_segments = int(convex_cfg.get("segments", min(max_cap, math.ceil(k_star) + 2)))
        convex.update(
            {
                "theta": theta,
                "segments": n_segments,
                "ltv": ltv,
                "batch": batch,
                "base_cac": base_cac,
            }
        )

    # Growth commitment (ADR 0014): investment-thesis FLOOR on the net client
    # stock (never a ceiling). Opt-in, default off — an absent block or an
    # explicit enabled: false leaves the instance byte-for-byte unaffected
    # (growth_commitment key below is informational only when disabled).
    #
    # C12 = net active-client stock at month 12 (same survival/phi mechanics as
    # the log-ceiling C_0 above), precomputed deterministically from A_base and
    # churn — no solve required. Checkpoints:
    #   annual:   C24 >= (1-slack)*sqrt(m)*C12  and  C36 >= (1-slack)*m*C12
    #   terminal: only C36 >= (1-slack)*m*C12
    # "C36 >= multiple_3y * C12" means: triple the client stock between the end
    # of the consensuated year 1 (month 12) and the end of year 3 (month 36).
    c12_stock = sum(
        survival.get((s, cohort, 12), 0.0) * base_acquisition.get((s, cohort), 0.0)
        for s in range(service_count)
        for cohort in fixed_periods
    )

    growth_commitment_cfg = config.get("growth_commitment", {})
    growth_commitment_enabled = bool(growth_commitment_cfg.get("enabled", False))
    growth_commitment: dict[str, Any] = {"enabled": growth_commitment_enabled, "C12": c12_stock}
    if growth_commitment_enabled:
        source = growth_commitment_cfg.get("source", "vc_minimum")
        checkpoints_mode = growth_commitment_cfg.get("checkpoints", "annual")
        floor_slack = float(growth_commitment_cfg.get("floor_slack", 0.0))

        if source == "custom":
            g_annual = float(growth_commitment_cfg["custom_g_annual"])
            m = (1.0 + g_annual) ** 2
        elif source == "plan_mom":
            g_annual = _stock_mom_annual(base_acquisition, survival, service_count, fixed_periods)
            m = (1.0 + g_annual) ** 2
        else:  # vc_minimum or none: use the investment-thesis multiple directly
            m = float(investment_thesis["multiple"])

        checkpoint_targets: dict[int, float] = {}
        base_month = int(investment_thesis["base_month"])
        horizon_month = int(investment_thesis["horizon_months"])
        span_months = horizon_month - base_month
        if checkpoints_mode == "annual":
            checkpoint_month = base_month + 12
            checkpoint_targets[checkpoint_month] = (
                (1.0 - floor_slack)
                * m ** ((checkpoint_month - base_month) / span_months)
                * c12_stock
            )
        checkpoint_targets[horizon_month] = (1.0 - floor_slack) * m * c12_stock

        growth_commitment.update(
            {
                "source": source,
                "multiple_3y": float(investment_thesis["multiple"]),
                "checkpoints": checkpoints_mode,
                "floor_slack": floor_slack,
                "m": m,
                "checkpoint_targets": checkpoint_targets,
                "custom_justification": growth_commitment_cfg.get("custom_justification"),
            }
        )

    # Aggregate acquisition envelope (ADR 0014 amendment): opt-in maximum path
    # U_t on TOTAL acquisition for t >= 13, precomputed here as constants so the
    # MILP stays linear (same pattern as checkpoint_targets above). Derivation:
    #   U_plan_t = Abar12 * (1+g_mom)^(t-12)   (consensuated-plan momentum)
    #   U_vc_t   = B_t - B_{t-1}*(1-churn_t)   (acquisition required by the
    #              VC-minimum stock path B_t = C12 * m^((t-12)/24), churn-net)
    #   U_t      = max/either(U_plan, U_vc) * (1 + delta_t)
    #   delta_t  = declared growing slack (thesis assumption: 0.25 y2, 0.50 y3)
    # Aggregation conventions (declared approximations): Abar12 and g_mom come
    # from TOTAL acquisition across services; churn_t is the C12-stock-weighted
    # aggregate of per-service monthly churn (falls back to the simple mean when
    # C12 = 0). custom source uses the declared path verbatim (no slack applied).
    envelope_cfg = config.get("acquisition_envelope", {})
    envelope_enabled = bool(envelope_cfg.get("enabled", False))
    envelope: dict[str, Any] = {"enabled": envelope_enabled}
    if envelope_enabled:
        env_source = envelope_cfg.get("source", "max_plan_vc")
        slack_year2 = float(envelope_cfg.get("slack_year2", 0.25))
        slack_year3 = float(envelope_cfg.get("slack_year3", 0.50))

        total_acq = {
            t: sum(base_acquisition[(s, t)] for s in range(service_count))
            for t in fixed_periods
        }
        abar12 = sum(total_acq.values()) / len(fixed_periods)
        first_acq_total = total_acq[fixed_periods[0]]
        last_acq_total = total_acq[fixed_periods[-1]]
        span = fixed_periods[-1] - fixed_periods[0]
        if first_acq_total > 0 and span > 0:
            g_mom = (last_acq_total / first_acq_total) ** (1.0 / span) - 1.0
        else:
            g_mom = 0.0

        # C12-stock-weighted aggregate churn (per-service stock at month 12).
        c12_by_service = {
            s: sum(
                survival.get((s, cohort, 12), 0.0) * base_acquisition.get((s, cohort), 0.0)
                for cohort in fixed_periods
            )
            for s in range(service_count)
        }
        churn_env: dict[int, float] = {}
        for t in range(13, H + 1):
            if c12_stock > 0:
                churn_env[t] = sum(
                    (c12_by_service[s] / c12_stock) * monthly_churn[(s, t)]
                    for s in range(service_count)
                )
            else:
                churn_env[t] = sum(
                    monthly_churn[(s, t)] for s in range(service_count)
                ) / service_count

        # VC-minimum multiple: single source of truth is investment_thesis.multiple
        # (growth_commitment.multiple_3y remains a deprecated config alias).
        m_env = float(investment_thesis["multiple"])
        thesis_base_month = int(investment_thesis["base_month"])
        thesis_horizon_month = int(investment_thesis["horizon_months"])
        thesis_span = thesis_horizon_month - thesis_base_month

        u_plan: dict[int, float] = {}
        u_vc: dict[int, float] = {}
        u_path: dict[int, float] = {}
        if env_source == "custom":
            custom_path = list(envelope_cfg["custom_path"])
            for offset, t in enumerate(range(13, H + 1)):
                u_path[t] = float(custom_path[offset])
        else:
            b_prev = c12_stock
            for t in range(13, H + 1):
                u_plan[t] = abar12 * (1.0 + g_mom) ** (t - 12)
                b_t = c12_stock * m_env ** ((t - thesis_base_month) / thesis_span)
                u_vc[t] = max(0.0, b_t - b_prev * (1.0 - churn_env[t]))
                b_prev = b_t
                if env_source == "plan_mom":
                    base_u = u_plan[t]
                elif env_source == "vc_minimum":
                    base_u = u_vc[t]
                else:  # max_plan_vc
                    base_u = max(u_plan[t], u_vc[t])
                delta_t = slack_year2 if t <= 24 else slack_year3
                u_path[t] = base_u * (1.0 + delta_t)

        # Early compatibility check against the growth_commitment floor: simulate
        # the MAXIMUM reachable stock under U_t (acquire U_t every month, churn-net).
        # If a checkpoint target is unreachable, the solve is infeasible by
        # construction — fail early with the business-diagnosis message instead
        # of paying for a MILP solve (same spirit as the ceiling/commitment check
        # in config.py).
        if growth_commitment_enabled:
            b_max = c12_stock
            for t in range(13, H + 1):
                b_max = b_max * (1.0 - churn_env[t]) + u_path[t]
                target = growth_commitment["checkpoint_targets"].get(t)
                if target is not None and b_max < target * (1.0 - 1e-9):
                    raise ValueError(
                        "acquisition_envelope is incompatible with the growth_commitment "
                        f"floor: acquiring the full envelope U_t every month reaches at most "
                        f"{b_max:,.1f} clients by month {t}, below the checkpoint target "
                        f"{target:,.1f}. This is a business diagnosis, not a solver failure: "
                        "the consensuated plan's momentum (and declared slack) cannot support "
                        "the VC thesis — recalibrate the year-1 plan, raise the slack with "
                        "justification, or lower the commitment multiple."
                    )

        envelope.update(
            {
                "source": env_source,
                "slack_year2": slack_year2,
                "slack_year3": slack_year3,
                "abar12": abar12,
                "g_mom": g_mom,
                "multiple_3y": m_env,
                "U_plan": u_plan,
                "U_vc": u_vc,
                "path": u_path,
                "custom_justification": envelope_cfg.get("custom_justification"),
            }
        )

    # Hiring friction (ADR 0014): opt-in monthly headcount cap on new sellers /
    # leaders for t >= 13 (V_t <= V_{t-1} + h_v, L_t <= L_{t-1} + h_l). Default off.
    hiring_cfg = config.get("hiring", {})
    hiring_enabled = bool(hiring_cfg.get("enabled", False))
    hiring: dict[str, Any] = {"enabled": hiring_enabled}
    if hiring_enabled:
        hiring.update(
            {
                "max_new_sellers_per_month": int(hiring_cfg.get("max_new_sellers_per_month", 1)),
                "max_new_leaders_per_month": int(hiring_cfg.get("max_new_leaders_per_month", 1)),
            }
        )

    # Acquisition channels (optional). Default: salesforce-only, no split.
    raw_channels = config.get("channels") or {}
    sf_cfg = raw_channels.get("salesforce", {"active": True, "min_share": 0.0, "max_share": 1.0})
    ad_cfg = raw_channels.get("advertising", {"active": False})
    tp_cfg = raw_channels.get("third_party", {"active": False})
    ad_active = bool(ad_cfg.get("active", False))
    tp_active = bool(tp_cfg.get("active", False))
    channels = {
        "salesforce": {
            "active": bool(sf_cfg.get("active", True)),
            "min_share": float(sf_cfg.get("min_share", 0.0)),
            "max_share": float(sf_cfg.get("max_share", 1.0)),
        },
        "advertising": {
            "active": ad_active,
            "min_share": float(ad_cfg.get("min_share", 0.0)),
            "max_share": float(ad_cfg.get("max_share", 1.0)),
        },
        "third_party": {
            "active": tp_active,
            "commission": float(tp_cfg.get("commission", 0.0)),
            "min_share": float(tp_cfg.get("min_share", 0.0)),
            "max_share": float(tp_cfg.get("max_share", 1.0)),
            # Required by validate_config when active (unbounded-path MVP fix).
            "A_tp_cap": float(tp_cfg["A_tp_cap"]) if tp_active else None,
        },
        # A channel split exists only when a non-salesforce channel is active.
        "any_split": ad_active or tp_active,
    }
    if ad_active:
        i_min = float(ad_cfg["I_min"])
        i_max = float(ad_cfg["I_max"])
        a_min = float(ad_cfg["A_min"])
        a_max = float(ad_cfg["A_max"])
        b = (a_max - a_min) / (i_max - i_min)
        a = a_min - b * i_min
        channels["advertising"].update(
            {
                "I_min": i_min,
                "I_max": i_max,
                "A_min": a_min,
                "A_max": a_max,
                "A_ad_cap": float(ad_cfg["A_ad_cap"]),
                "a": a,
                "b": b,
            }
        )

    return {
        "H": H,
        "T": periods,
        "S": service_count,
        "servicios": services,
        "beta": monthly_discount,
        "beta_anual": annual_discount,
        "descuento": discount_factor,
        "churn_mensual": monthly_churn,
        "phi": survival,
        "delta": repurchase_window,
        "alpha": alpha,
        "T_base": fixed_periods,
        "A_base": base_acquisition,
        "ciclo_op": config["ciclo_op"],
        "RRHH": hr,
        "VC": config["VC"],
        "g_adm": config["g_adm"],
        "meta": config["meta"],
        "sup": config["sup"],
        "rem_v": config["rem_v"],
        "rem_l": config["rem_l"],
        "com_v": config["com_v"],
        "com_l": config["com_l"],
        "tax": config["tax"],
        "investment_thesis": investment_thesis,
        "parametros": config,
        "g_max_suavizado": config.get("g_max_suavizado", 0.25),
        "commercial_productivity_lag": config.get("commercial_productivity_lag", 0),
        "log_ceiling": log_ceiling,
        "ceiling_slack": ceiling_slack,
        "convex_cac": convex,
        "channels": channels,
        "growth_commitment": growth_commitment,
        "acquisition_envelope": envelope,
        "hiring": hiring,
    }


def _stock_mom_annual(
    base_acquisition: dict[tuple[int, int], float],
    survival: dict[tuple[int, int, int], float],
    service_count: int,
    fixed_periods: list[int],
) -> float:
    """Annualized implied monthly growth of the net client STOCK over year 1.

    The growth commitment binds on client stock (not acquisition), so the
    comparable "plan_mom" growth rate is the geometric monthly growth of the
    net active-client stock C[t] = sum_s sum_{cohort<=t} phi(s,cohort,t)*A_base(s,cohort),
    evaluated at t=1..12, not the raw acquisition MoM. Falls back to 0.0 when the
    stock is degenerate (first month has zero stock) — see W5.
    """
    stock_by_month: dict[int, float] = {}
    for t in fixed_periods:
        stock_by_month[t] = sum(
            survival.get((s, cohort, t), 0.0) * base_acquisition.get((s, cohort), 0.0)
            for s in range(service_count)
            for cohort in fixed_periods
            if cohort <= t
        )
    first_month = fixed_periods[0]
    last_month = fixed_periods[-1]
    first_stock = stock_by_month.get(first_month, 0.0)
    last_stock = stock_by_month.get(last_month, 0.0)
    months = last_month - first_month
    if first_stock <= 0 or months <= 0:
        return 0.0
    monthly_growth = (last_stock / first_stock) ** (1.0 / months) - 1.0
    return (1.0 + monthly_growth) ** 12 - 1.0


def compute_growth_suggestions(config: dict[str, Any]) -> dict[str, Any]:
    """Compute g-suggestions (report-only, never auto-selected) for the growth
    commitment (ADR 0014, plan §3). Returns a JSON-serializable dict suitable
    for the ``growth_suggestions.json`` pipeline artifact.

    - ``g_vc_minimum``: annual growth implied by the ×multiple_3y/3-years VC
      benchmark (``multiple_3y**0.5 - 1``, since checkpoints are annual/sqrt).
    - ``g_plan_mom_acquisition``: MoM growth of the raw A_base acquisition plan
      (auxiliary; NOT the number the commitment is measured against).
    - ``g_plan_mom_stock``: MoM growth of the net client STOCK implied by
      A_base + churn over year 1 — the comparable number to ``g_vc_minimum``,
      since the commitment binds on stock, not acquisition.
    - ``g_required_rev``: annual growth required to hit ``target_revenue_y3``
      (only if the YAML declares that optional key).
    """
    validate_config(config)
    investment_thesis = resolve_investment_thesis(config)
    services = config["servicios"]
    service_count = len(services)
    H = config["H"]
    fixed_periods = list(range(1, 13))
    periods = list(range(1, H + 1))

    monthly_churn: dict[tuple[int, int], float] = {}
    for s, service in enumerate(services):
        for t in periods:
            year = min((t - 1) // 12, len(service["churn_anual"]) - 1)
            annual_churn = service["churn_anual"][year]
            monthly_churn[(s, t)] = 1 - (1 - annual_churn) ** (1 / 12)

    survival: dict[tuple[int, int, int], float] = {}
    for s in range(service_count):
        for cohort in fixed_periods:
            survival[(s, cohort, cohort)] = 1.0
            for t in range(cohort + 1, 13):
                survival[(s, cohort, t)] = survival[(s, cohort, t - 1)] * (
                    1 - monthly_churn[(s, t)]
                )

    base_acquisition = {
        (s, t): float(service["A_base"][t - 1])
        for s, service in enumerate(services)
        for t in fixed_periods
    }

    c12_stock = sum(
        survival.get((s, cohort, 12), 0.0) * base_acquisition.get((s, cohort), 0.0)
        for s in range(service_count)
        for cohort in fixed_periods
    )

    multiple_3y = float(investment_thesis["multiple"])
    thesis_span = int(investment_thesis["horizon_months"]) - int(investment_thesis["base_month"])
    g_vc_minimum = multiple_3y ** (12.0 / thesis_span) - 1.0

    # Auxiliary: raw acquisition MoM (geometric mean over months 1..12 of a
    # single representative service — service 0 — matching the plan's own units).
    a_base_0 = services[0]["A_base"]
    first_acq, last_acq = float(a_base_0[0]), float(a_base_0[-1])
    months = len(a_base_0) - 1
    if first_acq > 0 and months > 0:
        g_mom_acq_monthly = (last_acq / first_acq) ** (1.0 / months) - 1.0
    else:
        g_mom_acq_monthly = 0.0
    g_plan_mom_acquisition = (1.0 + g_mom_acq_monthly) ** 12 - 1.0

    # Comparable number: stock MoM (net client stock, not raw acquisition).
    g_plan_mom_stock = _stock_mom_annual(base_acquisition, survival, service_count, fixed_periods)

    suggestions: dict[str, Any] = {
        "schema_version": "1.0",
        "C12": c12_stock,
        "multiple_3y": multiple_3y,
        "investment_thesis": investment_thesis,
        "g_vc_minimum": g_vc_minimum,
        "g_plan_mom_acquisition": g_plan_mom_acquisition,
        "g_plan_mom_stock": g_plan_mom_stock,
        "g_plan_mom_monthly_acquisition": g_mom_acq_monthly,
        "notes": (
            "g_vc_minimum is the annual growth implied by the x{:.1f}-in-3-years VC "
            "benchmark, applied with geometric interpolation between base_month and "
            "horizon_month. "
            "g_plan_mom_stock is the comparable number for W1/W2 (the commitment binds "
            "on client STOCK); g_plan_mom_acquisition is auxiliary only (raw A_base MoM)."
        ).format(multiple_3y),
    }

    # Aggregate acquisition envelope export (when enabled): the precomputed U_t
    # path and its components, so the artifact makes the derivation auditable
    # (plan momentum vs VC-required acquisition vs declared slack).
    envelope_cfg = config.get("acquisition_envelope", {})
    if envelope_cfg.get("enabled", False):
        instance_envelope = generate_instance(config)["acquisition_envelope"]
        suggestions["acquisition_envelope"] = {
            "source": instance_envelope["source"],
            "slack_year2": instance_envelope["slack_year2"],
            "slack_year3": instance_envelope["slack_year3"],
            "abar12": instance_envelope["abar12"],
            "g_mom": instance_envelope["g_mom"],
            "multiple_3y": instance_envelope["multiple_3y"],
            "U_plan": {str(t): v for t, v in instance_envelope["U_plan"].items()},
            "U_vc": {str(t): v for t, v in instance_envelope["U_vc"].items()},
            "U_t": {str(t): v for t, v in instance_envelope["path"].items()},
            "custom_justification": instance_envelope["custom_justification"],
        }
        if (config.get("growth_commitment") or {}).get("enabled", False):
            from adventure_capital.growth_diagnostics import compute_conservative_plan_diagnostic

            diagnostic = compute_conservative_plan_diagnostic(config, max_iterations=8)
            suggestions["conservative_plan_diagnostic"] = diagnostic
            suggestions["M_star_feasible"] = diagnostic.get("M_star_feasible")
            suggestions["van_at_probe"] = diagnostic.get("van_at_probe")
            suggestions["thesis_gap"] = diagnostic.get("thesis_gap")

    target_revenue_y3 = config.get("target_revenue_y3")
    if target_revenue_y3 is not None and c12_stock > 0:
        # annual_revenue_per_customer approximation: constant-mix, from
        # unit_economics-style ticket*frequency for service 0 (declared approximation).
        ticket = float(services[0]["ticket"])
        frequency = float(services[0]["frecuencia"])
        annual_revenue_per_customer = ticket * (12.0 / frequency) if frequency > 0 else 0.0
        if annual_revenue_per_customer > 0:
            required_customers_y3 = float(target_revenue_y3) / annual_revenue_per_customer
            ratio = required_customers_y3 / c12_stock if c12_stock > 0 else float("inf")
            g_required_rev = ratio ** 0.5 - 1.0 if ratio > 0 else 0.0
            suggestions.update(
                {
                    "target_revenue_y3": float(target_revenue_y3),
                    "annual_revenue_per_customer": annual_revenue_per_customer,
                    "required_customers_y3": required_customers_y3,
                    "g_required_rev": g_required_rev,
                }
            )

    return suggestions


def check_pre_feasibility(instance: dict[str, Any]) -> list[str]:
    """Cheap pre-solve heuristics (ADR 0010, R3).

    Returns a list of human-readable warnings; an empty list means no obvious problem.
    This never replaces the solver's feasibility verdict — it catches the obvious
    underfunded / margin-negative cases before paying for a full MILP solve.
    """
    warnings: list[str] = []

    # 1) Financing vs. year-1 committed fixed cost. RRHH[1] is the month-1 payroll;
    #    g_adm is the fixed monthly admin cost. 12 months is a coarse but cheap proxy.
    fixed_year1 = 12 * (float(instance["g_adm"]) + float(instance["RRHH"][1]))
    vc = float(instance["VC"])
    if vc < fixed_year1:
        warnings.append(
            f"VC={vc:,.0f} < year-1 committed fixed cost≈{fixed_year1:,.0f} "
            "(12*(g_adm+RRHH[1])): cash is likely to breach the -VC floor in year 1."
        )

    # 2) Per-service unit margin sign. A non-positive contribution margin means every
    #    sale destroys cash, so no acquisition plan can be profitable.
    for s, service in enumerate(instance["servicios"]):
        ticket = float(service["ticket"])
        c_u = float(service["c_u"])
        if ticket <= c_u:
            warnings.append(
                f"service {s} ({service.get('nombre', s)}): ticket={ticket:,.0f} "
                f"<= c_u={c_u:,.0f}: negative unit margin, every sale destroys cash."
            )

    return warnings

"""Configuration loading and validation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


_FIXED_ACQUISITION_MONTHS = 12


_DEFAULT_CONFIG: dict[str, Any] = {
    "H": 36,
    "VC": 100_000,
    "beta": 0.35,
    "g_max_suavizado": 0.25,
    "servicios": [
        {
            "nombre": "Servicio",
            "ticket": 700,
            "frecuencia": 3,
            "alpha": 0.9,
            "churn_anual": [0.5, 0.3, 0.15],
            "c_u": 30,
            "c_min": 1000,
            "u_max": 100,
            "A_base": [2, 2, 3, 4, 5, 5, 6, 7, 8, 8, 9, 10],
        }
    ],
    "meta": 8,
    "sup": 3,
    "rem_v": 1_200,
    "rem_l": 1_700,
    "com_v": 0.10,
    "com_l": 0.05,
    "g_adm": 1_500,
    "RRHH_mensual": [10_000, 15_000, 20_000],
    "ciclo_op": [180, 90, 30],
    "buffer_caja": 0,
    "tax": 0.125,
    # Terminal value default: 1x last-year EBITDA (going-concern, conservative).
    "valor_residual_metodo": "ebitda_multiple",
    "ebitda_multiple": 1.0,
    "liquidity_policy": {"type": "none"},
    "working_capital": {"enabled": False, "floor_mode": "ticket"},
    # Logarithmic market-saturation growth law (ADR 0010). Default-on: the curve is
    # fitted so cumulative acquisition reaches target_stock_multiplier x the year-1 base
    # plan by t = H (the VC "triple your clients" benchmark). slack is the upward
    # tolerance band. An explicit enabled: false opts out (only physical/cash bounds remain).
    "acquisition_ceiling": {
        "enabled": True,
        "target_stock_multiplier": 3.0,
        "slack": 0.15,
    },
    # Aggregate acquisition envelope (ADR 0014 amendment): maximum acquisition
    # path derived from the consensuated 12-month plan (U_plan), the VC-minimum
    # stock path net of churn (U_vc), and a declared growing slack. Opt-in,
    # default off — pairs with the growth_commitment floor as the core growth
    # methodology. Never framed as an arbitrary market ceiling: every term of
    # U_t is traceable to the client plan, the investment thesis, or a declared
    # thesis assumption (slack_year2/slack_year3).
    "acquisition_envelope": {
        "enabled": False,
        "source": "max_plan_vc",  # plan_mom | vc_minimum | max_plan_vc | custom
        "slack_year2": 0.25,  # declared thesis assumption, not hidden tuning
        "slack_year3": 0.50,
        "custom_path": None,  # optional monthly list for months 13..H (override)
        "custom_justification": None,
    },
    "channels": {
        "salesforce": {"active": True, "min_share": 0.0, "max_share": 1.0},
        "advertising": {
            "active": False,
            "I_min": 0,
            "I_max": 0,
            "A_min": 0,
            "A_max": 0,
            "A_ad_cap": 0,
            "min_share": 0.0,
            "max_share": 1.0,
        },
        "third_party": {"active": False, "commission": 0.0, "min_share": 0.0, "max_share": 1.0},
    },
    "solver": {"name": "cbc", "time_limit": 300, "verbose": False},
    "commercial_productivity_lag": 0,
}


def default_config() -> dict[str, Any]:
    """Return validated default config."""
    config = deepcopy(_DEFAULT_CONFIG)
    validate_config(config)
    return config


def load_config(path: str | Path) -> dict[str, Any]:
    """Load YAML config and validate it."""
    with Path(path).open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    """Validate basic config shape and domain requirements."""
    required = [
        "H",
        "VC",
        "beta",
        "servicios",
        "meta",
        "sup",
        "rem_v",
        "rem_l",
        "com_v",
        "com_l",
        "g_adm",
        "RRHH_mensual",
        "ciclo_op",
        "tax",
    ]
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"Missing config keys: {missing}")

    if config["H"] < 14:
        raise ValueError(
            "H must be >= 14: the optimized growth horizon starts at month 13 and the "
            "logarithmic acquisition ceiling needs at least one post-year-1 period."
        )

    if not config["servicios"]:
        raise ValueError("At least one service is required.")

    service_required = [
        "nombre",
        "ticket",
        "frecuencia",
        "alpha",
        "churn_anual",
        "c_u",
        "c_min",
        "u_max",
        "A_base",
    ]
    for idx, service in enumerate(config["servicios"]):
        missing_service = [key for key in service_required if key not in service]
        if missing_service:
            raise ValueError(f"Service {idx} missing keys: {missing_service}")
        if len(service["A_base"]) != _FIXED_ACQUISITION_MONTHS:
            raise ValueError(f"A_base for service {idx} must have exactly 12 values.")
        if service["frecuencia"] <= 0:
            raise ValueError(f"Service {idx} frecuencia must be > 0.")
        if service["u_max"] <= 0:
            raise ValueError(f"Service {idx} u_max must be > 0.")
        if not service["churn_anual"]:
            raise ValueError(f"Service {idx} churn_anual must not be empty.")

    if config["meta"] <= 0:
        raise ValueError("meta must be > 0.")
    if config["sup"] <= 0:
        raise ValueError("sup must be > 0.")
    if config.get("commercial_productivity_lag", 0) < 0:
        raise ValueError("commercial_productivity_lag must be >= 0.")

    solver = config.get("solver", {})
    if solver.get("name", "cbc") != "cbc":
        raise ValueError("Only cbc solver is supported.")

    liquidity_policy = config.get("liquidity_policy", {"type": "none"})
    if liquidity_policy.get("type", "none") not in {"none", "nonnegative", "minimum_cash"}:
        raise ValueError("Unsupported liquidity policy.")

    working_capital = config.get("working_capital", {})
    if working_capital.get("enabled", False):
        if working_capital.get("floor_mode", "ticket") not in {"ticket"}:
            raise ValueError("Unsupported working_capital.floor_mode (only 'ticket' supported).")

    ceiling = config.get("acquisition_ceiling", {})
    if ceiling.get("enabled", False):
        multiplier = ceiling.get("target_stock_multiplier")
        if multiplier is None or multiplier <= 1.0:
            raise ValueError("acquisition_ceiling.target_stock_multiplier must be > 1.0 when enabled.")
        slack = ceiling.get("slack", 0.0)
        if slack < 0.0:
            raise ValueError("acquisition_ceiling.slack must be >= 0.")

    # Growth commitment (ADR 0014): investment-thesis FLOOR on the client stock —
    # never a ceiling, never a default. Opt-in; absent block / enabled: false is a
    # bit-for-bit no-op. C36 >= multiple_3y * C12 means "triple the client stock
    # between the end of the consensuated year 1 (month 12) and the end of year 3
    # (month 36)".
    growth_commitment = config.get("growth_commitment", {})
    if growth_commitment.get("enabled", False):
        source = growth_commitment.get("source", "vc_minimum")
        valid_sources = {"vc_minimum", "plan_mom", "custom", "none"}
        if source not in valid_sources:
            raise ValueError(
                f"growth_commitment.source must be one of {sorted(valid_sources)}, got {source!r}."
            )
        multiple_3y = growth_commitment.get("multiple_3y", 3.0)
        if multiple_3y is None or multiple_3y <= 1.0:
            raise ValueError("growth_commitment.multiple_3y must be > 1.0.")
        checkpoints = growth_commitment.get("checkpoints", "annual")
        if checkpoints not in {"annual", "terminal"}:
            raise ValueError(
                f"growth_commitment.checkpoints must be 'annual' or 'terminal', got {checkpoints!r}."
            )
        floor_slack = growth_commitment.get("floor_slack", 0.0)
        if floor_slack is None or not (0.0 <= floor_slack < 1.0):
            raise ValueError("growth_commitment.floor_slack must be in [0, 1).")
        if source == "custom":
            custom_g_annual = growth_commitment.get("custom_g_annual")
            if custom_g_annual is None or custom_g_annual <= 0.0:
                raise ValueError(
                    "growth_commitment.custom_g_annual must be > 0 when source is 'custom'."
                )
        # Ceiling/commitment coexistence (known trap, WORKLOG): if the exogenous
        # log ceiling is active at the same time, it must not make the ×multiple
        # floor structurally unreachable (ceiling target < commitment target).
        if ceiling.get("enabled", False):
            ceiling_multiplier = float(ceiling.get("target_stock_multiplier", 3.0))
            if ceiling_multiplier < float(multiple_3y):
                raise ValueError(
                    "growth_commitment is infeasible by construction: acquisition_ceiling."
                    f"target_stock_multiplier ({ceiling_multiplier}) < growth_commitment."
                    f"multiple_3y ({multiple_3y}). Raise the ceiling multiplier, disable the "
                    "ceiling, or lower the commitment multiple."
                )

    # Aggregate acquisition envelope (ADR 0014 amendment): opt-in upper path on
    # TOTAL acquisition for t >= 13, derived from the consensuated plan and/or
    # the VC-minimum stock path. Absent block / enabled: false is a no-op.
    envelope = config.get("acquisition_envelope", {})
    if envelope.get("enabled", False):
        env_source = envelope.get("source", "max_plan_vc")
        valid_env_sources = {"plan_mom", "vc_minimum", "max_plan_vc", "custom"}
        if env_source not in valid_env_sources:
            raise ValueError(
                f"acquisition_envelope.source must be one of {sorted(valid_env_sources)}, "
                f"got {env_source!r}."
            )
        for slack_key in ("slack_year2", "slack_year3"):
            slack_value = envelope.get(slack_key, 0.0)
            if slack_value is None or slack_value < 0.0:
                raise ValueError(f"acquisition_envelope.{slack_key} must be >= 0.")
        if env_source == "custom":
            custom_path = envelope.get("custom_path")
            expected_len = config["H"] - _FIXED_ACQUISITION_MONTHS
            if not isinstance(custom_path, (list, tuple)) or len(custom_path) != expected_len:
                raise ValueError(
                    "acquisition_envelope.custom_path must be a list with one value per "
                    f"optimized month (months 13..H = {expected_len} values) when source "
                    "is 'custom'."
                )
            if any(v is None or float(v) < 0.0 for v in custom_path):
                raise ValueError("acquisition_envelope.custom_path values must be >= 0.")
            justification = envelope.get("custom_justification")
            if not justification or not str(justification).strip():
                raise ValueError(
                    "acquisition_envelope.custom_justification is required when source is "
                    "'custom' (W4: every override must carry an explicit justification)."
                )

    hiring = config.get("hiring", {})
    if hiring.get("enabled", False):
        max_sellers = hiring.get("max_new_sellers_per_month", 1)
        max_leaders = hiring.get("max_new_leaders_per_month", 1)
        if max_sellers is None or max_sellers < 0:
            raise ValueError("hiring.max_new_sellers_per_month must be >= 0.")
        if max_leaders is None or max_leaders < 0:
            raise ValueError("hiring.max_new_leaders_per_month must be >= 0.")

    channels = config.get("channels")
    if channels is not None:
        active_max_share_sum = 0.0
        active_min_share_sum = 0.0
        any_active = False
        for name in ("salesforce", "advertising", "third_party"):
            ch = channels.get(name)
            if ch is None:
                continue
            if not ch.get("active", False):
                continue
            any_active = True
            min_share = ch.get("min_share", 0.0)
            max_share = ch.get("max_share", 1.0)
            if not (0.0 <= min_share <= max_share <= 1.0):
                raise ValueError(
                    f"channels.{name}: require 0 <= min_share <= max_share <= 1."
                )
            active_max_share_sum += max_share
            active_min_share_sum += min_share
        if any_active and active_max_share_sum < 1.0:
            raise ValueError(
                "Sum of max_share across active channels must be >= 1.0 (mix otherwise infeasible)."
            )
        if any_active and active_min_share_sum > 1.0:
            raise ValueError(
                "Sum of min_share across active channels must be <= 1.0 (mix otherwise infeasible)."
            )

        third_party = channels.get("third_party", {})
        if third_party.get("active", False):
            if third_party.get("commission", 0.0) < 0:
                raise ValueError("channels.third_party.commission must be >= 0.")
            # Third-party has no own capacity mechanism (no salesforce meta, no
            # advertising recta), so an active third-party channel without an
            # explicit cap is a documented unbounded-growth path
            # (unbounded_path_diagnosis §5-6). MVP decision: require the cap.
            tp_cap = third_party.get("A_tp_cap")
            if tp_cap is None:
                raise ValueError(
                    "channels.third_party.A_tp_cap is required when third_party is "
                    "active: the channel has no own capacity, so an explicit monthly "
                    "acquisition cap must be declared (or deactivate the channel)."
                )
            if float(tp_cap) < 0:
                raise ValueError("channels.third_party.A_tp_cap must be >= 0.")

        advertising = channels.get("advertising", {})
        if advertising.get("active", False):
            i_min = advertising.get("I_min", 0)
            i_max = advertising.get("I_max", 0)
            a_min = advertising.get("A_min", 0)
            a_max = advertising.get("A_max", 0)
            a_ad_cap = advertising.get("A_ad_cap", 0)
            if i_max <= i_min:
                raise ValueError("channels.advertising: I_max must be > I_min when active.")
            if a_max <= a_min:
                raise ValueError("channels.advertising: A_max must be > A_min when active.")
            slope = (a_max - a_min) / (i_max - i_min)
            if slope <= 0:
                raise ValueError("channels.advertising: implied slope b must be > 0.")
            if a_ad_cap < 0:
                raise ValueError("channels.advertising: A_ad_cap must be >= 0.")

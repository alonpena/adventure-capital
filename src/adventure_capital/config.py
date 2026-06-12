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
    "liquidity_policy": {"type": "none"},
    "acquisition_ceiling": {
        "enabled": False,
        "target_stock_multiplier": 2.0,
        "slack": 0.15,
    },
    "solver": {"name": "cbc", "time_limit": 120, "verbose": False},
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
        raise ValueError("H must be >= 14 because smoothing constraints reference months 13 and 14.")

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

    ceiling = config.get("acquisition_ceiling", {})
    if ceiling.get("enabled", False):
        multiplier = ceiling.get("target_stock_multiplier")
        if multiplier is None or multiplier <= 1.0:
            raise ValueError("acquisition_ceiling.target_stock_multiplier must be > 1.0 when enabled.")
        slack = ceiling.get("slack", 0.0)
        if slack < 0.0:
            raise ValueError("acquisition_ceiling.slack must be >= 0.")

"""Model instance preprocessing."""

from __future__ import annotations

from typing import Any

from adventure_capital.config import validate_config


def generate_instance(config: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic model instance from raw config."""
    validate_config(config)

    H = config["H"]
    services = config["servicios"]
    service_count = len(services)
    annual_discount = config["beta"]
    monthly_discount = (1 + annual_discount) ** (1 / 12) - 1

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

    minimum_cash = {}
    for t in periods:
        minimum_cash[t] = 0

    discount_factor = {t: 1 / (1 + monthly_discount) ** t for t in periods}

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
        "B_min": minimum_cash,
        "VC": config["VC"],
        "g_adm": config["g_adm"],
        "meta": config["meta"],
        "sup": config["sup"],
        "rem_v": config["rem_v"],
        "rem_l": config["rem_l"],
        "com_v": config["com_v"],
        "com_l": config["com_l"],
        "tax": config["tax"],
        "parametros": config,
        "g_max_suavizado": config.get("g_max_suavizado", 0.25),
    }

"""Post-optimization valuation calculations."""

from __future__ import annotations

from typing import Any

import pandas as pd


def calcular_valor_residual(
    ebitda_last_month: float,
    metodo: str,
    wacc: float,
    ebitda_multiple: float = None,
    gordon_g: float = None
) -> float:
    """
    Calcula el valor residual (terminal value) según el método configurado.

    Args:
        ebitda_last_month: EBITDA del último mes del horizonte de proyección
        metodo: "none" | "ebitda_multiple" | "gordon"
        wacc: tasa de descuento anual (decimal, ej: 0.35)
        ebitda_multiple: múltiplo EV/EBITDA (requerido si metodo="ebitda_multiple")
        gordon_g: tasa de crecimiento perpetuo (requerido si metodo="gordon")

    Returns:
        Valor residual en la misma moneda que ebitda_last_month (no descontado)

    Supuestos documentados:
        - ebitda_multiple: asume EBITDA anualizado = ebitda_last_month * 12
        - gordon: asume EBITDA ≈ FCF (simplificación — documentar como limitación)
        - gordon: requiere wacc > gordon_g, sino lanza ValueError
    """
    if metodo == "none":
        return 0.0

    elif metodo == "ebitda_multiple":
        if ebitda_multiple is None:
            raise ValueError("ebitda_multiple requerido cuando metodo='ebitda_multiple'")
        ebitda_anual = ebitda_last_month * 12
        return max(ebitda_anual * ebitda_multiple, 0.0)

    elif metodo == "gordon":
        if gordon_g is None:
            raise ValueError("gordon_g requerido cuando metodo='gordon'")
        if wacc <= gordon_g:
            raise ValueError(f"WACC ({wacc}) debe ser mayor que g ({gordon_g}) en Gordon Growth")
        ebitda_anual = ebitda_last_month * 12
        # LIMITACIÓN: EBITDA se usa como proxy de FCF. En contexto startup puede sobreestimar VR.
        return max(ebitda_anual * (1 + gordon_g) / (wacc - gordon_g), 0.0)

    else:
        raise ValueError(f"Método de valor residual desconocido: '{metodo}'. Opciones: none, ebitda_multiple, gordon")


def calculate_dcf(df: pd.DataFrame, instance: dict[str, Any]) -> dict[str, Any]:
    """Calculate discounted cashflow valuation from monthly optimization results."""
    monthly_discount = instance["beta"]
    annual_discount = instance["beta_anual"]
    working_capital = float(instance["VC"])
    parameters = instance.get("parametros", instance.get("params", {}))
    tax = float(parameters.get("tax", instance.get("tax", 0.125)))
    terminal_ebitda_multiple = float(parameters.get("mult_vd_ebitda", 1.0))

    # E.1 read residual value params. Default terminal value = 1x last-year EBITDA
    # (ebitda_multiple with multiple 1.0): a conservative going-concern terminal so the
    # company is never worth more "in parts" than operating. Arbitrary high multiples are
    # deliberately not the default; override per instance with documented justification.
    metodo = parameters.get("valor_residual_metodo", "ebitda_multiple")
    ebitda_multiple = parameters.get("ebitda_multiple", terminal_ebitda_multiple)
    gordon_g = parameters.get("gordon_g")

    cashflow = pd.DataFrame(
        {
            "t": df["t"],
            "Año": df["Año"],
            "Ingresos": df["Ingresos"],
            "Costo_operacional": df["Costo_operacional"],
            "CAC": df["CAC"],
            "G_adm": df["G_adm"],
            "RRHH": df["RRHH"],
            "EBITDA": df["EBITDA"],
        }
    )
    cashflow["Impuesto"] = cashflow["EBITDA"].apply(lambda value: max(value * tax, 0.0))
    cashflow["FC_neto"] = cashflow["EBITDA"] - cashflow["Impuesto"]
    cashflow["Factor_desc"] = 1 / (1 + monthly_discount) ** cashflow["t"]
    cashflow["FC_desc"] = cashflow["FC_neto"] * cashflow["Factor_desc"]

    last_month_ebitda = float(cashflow.iloc[-1]["EBITDA"])
    annualized_ebitda = last_month_ebitda * 12
    
    terminal_value_nominal = calcular_valor_residual(
        last_month_ebitda,
        metodo,
        annual_discount,
        ebitda_multiple=ebitda_multiple,
        gordon_g=gordon_g
    )
    
    terminal_discount_factor = 1 / (1 + monthly_discount) ** int(instance["H"])
    terminal_value_pv = terminal_value_nominal * terminal_discount_factor
    pv_cashflows = float(cashflow["FC_desc"].sum())
    npv = -working_capital + pv_cashflows + terminal_value_pv

    annual_summary = cashflow.groupby("Año").agg(
        {
            "Ingresos": "sum",
            "Costo_operacional": "sum",
            "CAC": "sum",
            "G_adm": "sum",
            "RRHH": "sum",
            "EBITDA": "sum",
            "Impuesto": "sum",
            "FC_neto": "sum",
            "FC_desc": "sum",
        }
    )

    return {
        "df_flujo_caja": cashflow,
        "resumen_anual_dcf": annual_summary,
        "vp_flujos": pv_cashflows,
        "valor_desecho_nominal": terminal_value_nominal,
        "valor_desecho_vp": terminal_value_pv,
        "vr_nominal": terminal_value_nominal,
        "vr_pv": terminal_value_pv,
        "VAN": float(npv),
        "ebitda_ultimo_mes": last_month_ebitda,
        "ebitda_anualizado": annualized_ebitda,
        "capital_trabajo_inicial": working_capital,
        "beta_anual": annual_discount,
        "beta_mensual": monthly_discount,
        "tax": tax,
        "mult_vd_ebitda": terminal_ebitda_multiple,
    }


def calculate_multiples_valuation(df: pd.DataFrame, instance: dict[str, Any]) -> dict[str, Any]:
    """Calculate valuation using revenue and EBITDA multiples."""
    parameters = instance.get("parametros", instance.get("params", {}))
    revenue_multiple = float(parameters.get("mult_ingresos", 1.5))
    ebitda_multiple = float(parameters.get("mult_ebitda", 3.0))

    reference_year = int(df["Año"].max())
    reference_df = df[df["Año"] == reference_year]
    annual_revenue = float(reference_df["Ingresos"].sum())
    annual_ebitda = float(reference_df["EBITDA"].sum())
    revenue_value = annual_revenue * revenue_multiple
    ebitda_value = max(annual_ebitda, 0.0) * ebitda_multiple

    multiples_df = pd.DataFrame(
        [
            {
                "Método": "Múltiplo de ingresos",
                "Base": annual_revenue,
                "Múltiplo": revenue_multiple,
                "Valorización": revenue_value,
            },
            {
                "Método": "Múltiplo de EBITDA",
                "Base": annual_ebitda,
                "Múltiplo": ebitda_multiple,
                "Valorización": ebitda_value,
            },
        ]
    )

    return {
        "df_multiplos": multiples_df,
        "valor_por_ingresos": float(revenue_value),
        "valor_por_ebitda": float(ebitda_value),
        "anio_referencia": reference_year,
        "ingresos_anual": annual_revenue,
        "ebitda_anual": annual_ebitda,
        "mult_ingresos": revenue_multiple,
        "mult_ebitda": ebitda_multiple,
    }


# Legacy Spanish API aliases.
def calcular_valorizacion_dcf(df: pd.DataFrame, inst: dict[str, Any]) -> dict[str, Any]:
    return calculate_dcf(df, inst)


def calcular_valorizacion_multiplos(df: pd.DataFrame, inst: dict[str, Any]) -> dict[str, Any]:
    return calculate_multiples_valuation(df, inst)

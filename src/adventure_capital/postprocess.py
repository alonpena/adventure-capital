"""Postprocessed Results View.

A derived, non-canonical presentation layer (see ADR 0007). It reads the flat
artifacts already written to ``output_dir`` and re-presents them as audience-
tagged folders for the entrepreneur/Excel workflow and the future UI. It only
copies existing JSON artifacts or selects/renames columns from the canonical
CSVs; it never recomputes valuation, unit economics, due diligence, or
stochastic metrics. Folders are written only when their source artifacts exist,
so deterministic-only, ``baseline_only``, and rejected-for-stochastic runs all
degrade gracefully.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA_VERSION = "1.0"


# --- small disk helpers ----------------------------------------------------

def _read_csv(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _copy(src: Path, dst: Path) -> bool:
    if src.exists():
        shutil.copyfile(src, dst)
        return True
    return False


def _select(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return only the columns that actually exist, preserving order."""
    present = [c for c in columns if c in df.columns]
    return df[present]


def _service_cols(df: pd.DataFrame, prefix: str) -> list[str]:
    return [c for c in df.columns if c.startswith(prefix)]


# --- accelerated growth plan ----------------------------------------------

def _build_growth_plan(out: Path, dst: Path) -> None:
    df = _read_csv(out / "optimized_results.csv")
    if df is None:
        return
    dst.mkdir(parents=True, exist_ok=True)

    _select(df, ["t", "Año", "Mes"] + _service_cols(df, "A_") + _service_cols(df, "C_")
            + ["Adq_clientes", "Clientes_activos"]).to_csv(dst / "01_customer_flow.csv", index=False)

    _select(df, ["t"] + _service_cols(df, "Q_") + _service_cols(df, "R_")
            + ["Servicios_totales", "Ventas_recurrentes"]).to_csv(dst / "02_service_flow.csv", index=False)

    _select(df, ["t"] + _service_cols(df, "I_")
            + ["Ingresos", "Ingresos_recurrentes_proxy", "ARR_pct"]).to_csv(dst / "03_revenue_flow.csv", index=False)

    _select(df, ["t", "Vendedores", "Lideres", "A_salesforce", "A_advertising", "A_third_party",
                 "advertising_investment"]).to_csv(dst / "04_commercial_plan.csv", index=False)

    _select(df, ["t"] + _service_cols(df, "m_op_") + _service_cols(df, "Cost_op_")
            + ["Costo_operacional"]).to_csv(dst / "05_operational_capacity.csv", index=False)

    _select(df, ["t", "CAC", "salesforce_cac_cost", "advertising_cac_cost", "third_party_cost",
                 "total_acquisition_cost", "period_cac_per_user", "cumulative_cac_per_user",
                 "G_adm", "RRHH"]).to_csv(dst / "06_costs_and_cac.csv", index=False)

    _select(df, ["t", "EBITDA", "EBITDA_acum", "Caja", "MoM_adq",
                 "MoM_ingresos"]).to_csv(dst / "07_cash_and_working_capital.csv", index=False)

    summary = _read_json(out / "growth_plan_summary.json") or {}
    # breakeven_month is a trivial presentation derivation over cumulative EBITDA.
    breakeven = None
    if "EBITDA_acum" in df.columns:
        positive = df[df["EBITDA_acum"] >= 0]
        if not positive.empty:
            breakeven = int(positive.iloc[0]["t"])
    summary = {**summary, "breakeven_month": breakeven}
    _write_json(dst / "08_growth_plan_summary.json", summary)


# --- valuation workbook ----------------------------------------------------

def _build_valuation_workbook(out: Path, dst: Path) -> None:
    valuation = _read_json(out / "valuation_summary.json")
    if valuation is None:
        return
    dst.mkdir(parents=True, exist_ok=True)

    _copy(out / "dcf_cashflow.csv", dst / "01_cashflow_detail.csv")
    _copy(out / "dcf_annual_summary.csv", dst / "03_dcf_calculation.csv")
    _copy(out / "unit_economics.csv", dst / "06_unit_economics_detail.csv")
    _copy(out / "valuation_summary.json", dst / "05_valuation_summary.json")
    _copy(out / "formula_trace.json", dst / "07_formula_trace.json")

    # 02 and 04 are field subsets of the canonical valuation_summary (no recompute).
    _write_json(dst / "02_dcf_inputs.json", {
        "schema_version": SCHEMA_VERSION,
        "beta_anual": valuation.get("beta_anual"),
        "beta_mensual": valuation.get("beta_mensual"),
        "tax": valuation.get("tax"),
        "vc_invested": valuation.get("vc_invested"),
        "terminal_value_method": valuation.get("terminal_value_method"),
    })
    _write_json(dst / "04_terminal_value.json", {
        "schema_version": SCHEMA_VERSION,
        "method": valuation.get("terminal_value_method"),
        "ebitda_ultimo_mes": valuation.get("ebitda_ultimo_mes"),
        "ebitda_anualizado": valuation.get("ebitda_anualizado"),
        "vr_nominal": valuation.get("vr_nominal"),
        "vr_pv": valuation.get("vr_pv"),
    })


# --- due diligence ---------------------------------------------------------

# Static lever map keyed by finding id; deterministic and auditable (ADR-free
# lookup, no DD math change). Falls back to name-keyword heuristics, then to an
# explicit "unmapped" marker so nothing is silently dropped.
_LEVER_BY_ID: dict[str, dict[str, str]] = {
    "DD02": {"lever": "ticket | c_u", "suggested_direction": "increase ticket or reduce c_u", "impact_area": "unit_economics"},
    "DD03": {"lever": "VC", "suggested_direction": "increase", "impact_area": "financing"},
    "DD11": {"lever": "VC | working_capital", "suggested_direction": "increase", "impact_area": "liquidity"},
}

_LEVER_KEYWORDS: list[tuple[tuple[str, ...], dict[str, str]]] = [
    (("churn", "retention"), {"lever": "churn_anual", "suggested_direction": "decrease", "impact_area": "retention"}),
    (("cac", "commission", "comision", "productiv"), {"lever": "meta | commission rates", "suggested_direction": "adjust", "impact_area": "acquisition_cost"}),
    (("cash", "liquid", "financ", "gap"), {"lever": "VC | working_capital", "suggested_direction": "increase", "impact_area": "liquidity"}),
    (("revenue", "growth", "ingres", "adquis"), {"lever": "A_base | acquisition ceiling slack", "suggested_direction": "increase", "impact_area": "growth"}),
]


def _lever_for(finding: dict[str, Any]) -> dict[str, str]:
    fid = str(finding.get("id", ""))
    if fid in _LEVER_BY_ID:
        return _LEVER_BY_ID[fid]
    haystack = f"{finding.get('name', '')} {finding.get('message', '')}".lower()
    for keywords, lever in _LEVER_KEYWORDS:
        if any(k in haystack for k in keywords):
            return lever
    return {"lever": None, "suggested_direction": None, "impact_area": "unmapped"}


def _current_value(finding: dict[str, Any]) -> Any:
    evidence = finding.get("evidence") or {}
    for value in evidence.values():
        if isinstance(value, (int, float, str)):
            return value
    return None


def _build_due_diligence(out: Path, dst: Path) -> None:
    dd_report = _read_json(out / "due_diligence_report.json")
    assessment = _read_json(out / "assessment_summary.json")
    if dd_report is None and assessment is None:
        return
    dst.mkdir(parents=True, exist_ok=True)
    dd_report = dd_report or {}
    findings = dd_report.get("findings", [])

    _write_json(dst / "due_diligence_assessment.json", {
        "schema_version": SCHEMA_VERSION,
        "verdict": dd_report.get("verdict") or (assessment or {}).get("verdict"),
        "allows_stochastic": dd_report.get("allows_stochastic", (assessment or {}).get("allows_stochastic")),
        "valuation_mode": dd_report.get("valuation_mode", (assessment or {}).get("valuation_mode")),
        "findings": findings,
    })

    flags = pd.DataFrame([
        {
            "id": f.get("id"),
            "name": f.get("name"),
            "severity_class": f.get("severity_class"),
            "passed": f.get("passed"),
            "message": f.get("message"),
        }
        for f in findings
    ])
    flags.to_csv(dst / "due_diligence_flags.csv", index=False)

    levers = [
        {"finding_id": f.get("id"), "current_value": _current_value(f), **_lever_for(f)}
        for f in findings
        if not f.get("passed", True)
    ]
    _write_json(dst / "recommended_levers.json", {"schema_version": SCHEMA_VERSION, "levers": levers})

    if assessment is not None:
        _copy(out / "assessment_summary.json", dst / "assessment_summary.json")


# --- stochastic assessment -------------------------------------------------

def _stochastic_method_status() -> dict[str, Any]:
    """Static metadata describing the implemented stochastic method (no overclaim)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "method": "sample_average_approximation",
        "objective": "cvar_van",
        "is_robust_optimization": False,
        "scenario_generation": "latin_hypercube_triangular_icdf",
        "lhs_implemented": True,
        "lhs_status": "implemented",
        "saa_implemented": True,
        "ex_post_evaluation": "ex_post_lhs",
        "monte_carlo_ex_post_implemented": True,
        "known_parity_gaps_vs_deterministic": [
            "first_year_channel_mix",
            "commercial_recourse",
            "due_diligence_vc_proxy_probabilities",
        ],
        "note": (
            "First-stage SAA over LHS scenarios with CVaR(VAN) objective; ex-post "
            "evaluation uses an out-of-sample LHS sample (separate seed, larger N). "
            "Ex-post recourse is closed-form (no MILP re-solve); not worst-case/robust."
        ),
    }


def _build_stochastic(out: Path, dst: Path) -> None:
    summary = _read_csv(out / "stochastic_summary.csv")
    scenarios = _read_csv(out / "stochastic_scenarios.csv")
    if summary is None and scenarios is None:
        return
    dst.mkdir(parents=True, exist_ok=True)

    _copy(out / "stochastic_scenarios.csv", dst / "stochastic_scenarios.csv")
    _copy(out / "stochastic_summary.csv", dst / "stochastic_summary.csv")
    _copy(out / "stochastic_breakeven.csv", dst / "stochastic_breakeven.csv")
    _write_json(dst / "stochastic_method_status.json", _stochastic_method_status())

    diagnostics: dict[str, Any] = {"schema_version": SCHEMA_VERSION}
    if summary is not None and not summary.empty:
        diagnostics["summary"] = summary.iloc[0].to_dict()
    _write_json(dst / "stochastic_diagnostics.json", diagnostics)


# --- entry point -----------------------------------------------------------

def build_postprocessed_view(output_dir: str | Path) -> dict[str, str]:
    """Build the derived ``postprocessed_results/`` view from flat artifacts on disk.

    Idempotent and graceful: each folder is written only when its source
    artifacts exist. Returns a manifest of the folders that were produced.
    """
    out = Path(output_dir)
    root = out / "postprocessed_results"
    root.mkdir(parents=True, exist_ok=True)

    _build_growth_plan(out, root / "accelerated_growth_plan")
    _build_valuation_workbook(out, root / "valuation_workbook")
    _build_due_diligence(out, root / "due_diligence")
    _build_stochastic(out, root / "stochastic_assessment")

    produced = {
        name: str((root / name).relative_to(out))
        for name in ("accelerated_growth_plan", "valuation_workbook", "due_diligence", "stochastic_assessment")
        if (root / name).exists()
    }
    _write_json(root / "postprocessed_manifest.json", {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_canonical": False,
        "derived_from": "flat pipeline outputs (see ADR 0007)",
        "folders": produced,
    })
    return produced

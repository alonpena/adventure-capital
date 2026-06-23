"""Distribution summaries and artifacts for the ex-post LHS evaluation.

Percentiles are summary statistics, not a replacement for the full per-scenario
distribution, which is written out in full. CVaR is the empirical expected
shortfall of VAN at ``cvar_alpha``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from adventure_capital.stochastic.defaults import M4_DEFAULTS


def _milestones(evaluation: pd.DataFrame) -> list[int]:
    prefix = "hit_final_active_clients_"
    found = [int(col[len(prefix):]) for col in evaluation.columns if col.startswith(prefix)]
    return sorted(found)


def _empirical_cvar(van: np.ndarray, prob: np.ndarray, alpha: float) -> float:
    """Expected shortfall: probability-weighted mean of the worst-``alpha`` tail."""
    order = np.argsort(van)
    van_sorted = van[order]
    prob_sorted = prob[order]
    cumulative = np.cumsum(prob_sorted)
    # Include scenarios until the cumulative weight first reaches alpha.
    mask = cumulative <= alpha
    if not mask.any():
        mask[0] = True  # at least the single worst scenario
    weight = prob_sorted[mask].sum()
    if weight <= 0:
        return float(van_sorted[0])
    return float(np.dot(prob_sorted[mask], van_sorted[mask]) / weight)


def _p(series: np.ndarray, q: float) -> float:
    return float(np.percentile(series, q))


def summarize_distribution(
    evaluation: pd.DataFrame, *, cvar_alpha: float | None = None
) -> dict[str, Any]:
    """Compute the M4 summary statistics over the ex-post LHS results."""
    alpha = float(cvar_alpha if cvar_alpha is not None else M4_DEFAULTS["cvar_alpha"])

    van = evaluation["VAN"].to_numpy(dtype=float)
    prob = evaluation["probability"].to_numpy(dtype=float)
    prob = prob / prob.sum() if prob.sum() > 0 else np.full_like(van, 1.0 / len(van))

    gap = evaluation["funding_gap"].to_numpy(dtype=float)
    clients = evaluation["final_active_clients"].to_numpy(dtype=float)
    breakeven = evaluation["breakeven_month"]
    runway = evaluation["runway_month"]
    below_floor = evaluation["cash_below_floor"].to_numpy(dtype=float)

    summary: dict[str, Any] = {
        "n_scenarios": int(len(evaluation)),
        "cvar_alpha": alpha,
        "expected_van": float(np.dot(prob, van)),
        "van_p5": _p(van, 5),
        "van_p10": _p(van, 10),
        "van_p50": _p(van, 50),
        "van_p90": _p(van, 90),
        "cvar_5": _empirical_cvar(van, prob, alpha),
        "prob_van_negative": float(np.dot(prob, (van < 0).astype(float))),
        "final_active_clients_p10": _p(clients, 10),
        "final_active_clients_p50": _p(clients, 50),
        "final_active_clients_p90": _p(clients, 90),
    }

    for milestone in _milestones(evaluation):
        hit = evaluation[f"hit_final_active_clients_{milestone}"].to_numpy(dtype=float)
        summary[f"prob_hit_final_active_clients_{milestone}"] = float(np.dot(prob, hit))

    summary.update(
        {
            "breakeven_month_p50": (
                _p(breakeven.dropna().to_numpy(dtype=float), 50)
                if breakeven.notna().any()
                else None
            ),
            "prob_no_breakeven": float(np.dot(prob, breakeven.isna().to_numpy().astype(float))),
            "runway_month_p50": (
                _p(runway.dropna().to_numpy(dtype=float), 50) if runway.notna().any() else None
            ),
            "prob_cash_below_floor": float(np.dot(prob, below_floor)),
            "expected_funding_gap": float(np.dot(prob, gap)),
            "max_funding_gap": float(gap.max()),
            "cac_p50": _p(evaluation["cac_per_customer"].to_numpy(dtype=float), 50),
            "ltv_cac_p50": float(np.nanpercentile(evaluation["ltv_cac"].to_numpy(dtype=float), 50)),
            "arpu_p50": _p(evaluation["arpu"].to_numpy(dtype=float), 50),
            "arr_p50": _p(evaluation["arr"].to_numpy(dtype=float), 50),
        }
    )
    return summary


def write_outputs(
    evaluation: pd.DataFrame,
    summary: dict[str, Any],
    output_dir: str | Path,
    *,
    solution: dict[str, Any] | None = None,
    saa_scenario_count: int | None = None,
    evaluation_scenario_count: int | None = None,
) -> dict[str, str]:
    """Write the ex-post LHS distribution, summary, and diagnostics artifacts.

    Produces the canonical M4 artifact set:
    ``stochastic_scenarios.csv``, ``stochastic_summary.csv``,
    ``stochastic_diagnostics.json``, ``stochastic_unit_economics.csv`` and, when
    a ``solution`` is supplied, ``saa_solution.json``.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    scenarios_path = out / "stochastic_scenarios.csv"
    summary_path = out / "stochastic_summary.csv"
    diagnostics_path = out / "stochastic_diagnostics.json"
    unit_economics_path = out / "stochastic_unit_economics.csv"

    evaluation.to_csv(scenarios_path, index=False)
    pd.DataFrame([summary]).to_csv(summary_path, index=False)

    ue_columns = [
        "scenario",
        "probability",
        "cac_per_customer",
        "ltv_cac",
        "arpu",
        "arr",
        "final_active_clients",
    ]
    evaluation[ue_columns].to_csv(unit_economics_path, index=False)

    diagnostics = {
        "objective": "cvar_van",
        "evaluation": "ex_post_lhs",
        "milestones": _milestones(evaluation),
        "summary": summary,
    }
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2))

    artifacts = {
        "scenarios": str(scenarios_path),
        "summary": str(summary_path),
        "diagnostics": str(diagnostics_path),
        "unit_economics": str(unit_economics_path),
    }

    if solution is not None:
        saa_path = out / "saa_solution.json"
        # ``n_scenarios`` in the summary is the ex-post evaluation count, not the
        # SAA optimization count. Keep ``scenario_count`` meaning the SAA count
        # for back-compat and surface both counts explicitly.
        eval_count = (
            int(evaluation_scenario_count)
            if evaluation_scenario_count is not None
            else int(summary.get("n_scenarios", 0))
        )
        saa_count = (
            int(saa_scenario_count)
            if saa_scenario_count is not None
            else int(M4_DEFAULTS["saa_scenario_count"])
        )
        saa = {
            "schema_version": "2.0",
            "status": solution.get("status"),
            "objective": solution.get("objective", "cvar_van"),
            "cvar_alpha": solution.get("cvar_alpha"),
            "cvar_van": solution.get("cvar_van"),
            "expected_van": solution.get("expected_van"),
            "scenario_count": saa_count,
            "saa_scenario_count": saa_count,
            "evaluation_scenario_count": eval_count,
            "strategy": {
                "V": solution["strategy"]["V"],
                "L": solution["strategy"]["L"],
                "I_ad": solution["strategy"]["I_ad"],
                "A_sf_plan": solution["strategy"]["A_sf_plan"],
                "A_ad_plan": solution["strategy"]["A_ad_plan"],
                "A_tp_plan": solution["strategy"]["A_tp_plan"],
            },
        }
        saa_path.write_text(json.dumps(saa, indent=2, default=str))
        artifacts["saa_solution"] = str(saa_path)

    return artifacts

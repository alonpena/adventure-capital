"""Distribution summaries and CSV outputs for the stochastic prototype.

Percentiles are summary statistics, not a replacement for the full per-scenario
distribution, which is written out in full.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def summarize_distribution(evaluation: pd.DataFrame) -> dict[str, Any]:
    """Compute summary statistics over the Phase-B per-scenario results.

    Uses scenario probabilities for the expected value (so explicit named
    scenarios with unequal weights are handled), and the empirical sample for
    percentiles and tail probabilities.
    """
    van = evaluation["VAN"].to_numpy(dtype=float)
    prob = evaluation["probability"].to_numpy(dtype=float)
    prob = prob / prob.sum() if prob.sum() > 0 else np.full_like(van, 1.0 / len(van))

    gap = evaluation["funding_gap"].to_numpy(dtype=float)
    breakeven = evaluation["breakeven_month"]

    return {
        "n_scenarios": int(len(evaluation)),
        "expected_van": float(np.dot(prob, van)),
        "van_p10": float(np.percentile(van, 10)),
        "van_p50": float(np.percentile(van, 50)),
        "van_p90": float(np.percentile(van, 90)),
        "van_min": float(van.min()),
        "van_max": float(van.max()),
        "van_std": float(van.std(ddof=0)),
        "prob_van_negative": float(np.dot(prob, (van < 0).astype(float))),
        "prob_funding_gap": float(np.dot(prob, (gap > 0).astype(float))),
        "expected_funding_gap": float(np.dot(prob, gap)),
        "max_funding_gap": float(gap.max()),
        "breakeven_month_p50": (
            float(np.nanpercentile(breakeven.astype(float), 50))
            if breakeven.notna().any()
            else None
        ),
        "prob_no_breakeven": float(np.dot(prob, breakeven.isna().to_numpy().astype(float))),
    }


def breakeven_distribution(evaluation: pd.DataFrame) -> pd.DataFrame:
    """Frequency table of breakeven month (NaN = never breaks even)."""
    counts = evaluation["breakeven_month"].value_counts(dropna=False).sort_index()
    return counts.rename_axis("breakeven_month").reset_index(name="count")


def write_outputs(
    evaluation: pd.DataFrame,
    summary: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, str]:
    """Write the full distribution, summary, and breakeven table to ``output_dir``."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    scenarios_path = out / "stochastic_scenarios.csv"
    summary_path = out / "stochastic_summary.csv"
    breakeven_path = out / "stochastic_breakeven.csv"

    evaluation.to_csv(scenarios_path, index=False)
    pd.DataFrame([summary]).to_csv(summary_path, index=False)
    breakeven_distribution(evaluation).to_csv(breakeven_path, index=False)

    return {
        "scenarios": str(scenarios_path),
        "summary": str(summary_path),
        "breakeven": str(breakeven_path),
    }

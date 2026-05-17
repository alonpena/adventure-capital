"""Pipeline orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adventure_capital.financial_model import build_fixed_period_financial_model
from adventure_capital.instance import generate_instance


def run_pipeline(config: dict[str, Any], *, output_dir: str | None = None, verbose_solver: bool = False) -> dict[str, Any]:
    """Run implemented pipeline phases.

    Phase 1 only currently: fixed-period financial model. No solver required.
    """
    instance = generate_instance(config)
    fixed_cashflow = build_fixed_period_financial_model(instance)
    result = {"instance": instance, "fixed_cashflow": fixed_cashflow}

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        fixed_cashflow.to_csv(out / "fixed_cashflow.csv", index=False)

    return result

"""Pipeline orchestration."""

from __future__ import annotations

from typing import Any

from adventure_capital.financial_model import build_fixed_period_financial_model
from adventure_capital.instance import generate_instance
from adventure_capital.model import solve_growth_plan
from adventure_capital.reporting import generate_report
from adventure_capital.results import extract_results, summarize_results
from adventure_capital.unit_economics import calculate_unit_economics
from adventure_capital.valuation import calculate_dcf, calculate_multiples_valuation


def run_pipeline(config: dict[str, Any], *, output_dir: str | None = None, verbose_solver: bool = False) -> dict[str, Any]:
    """Run full pipeline and optionally generate Phase 4 artifacts."""
    instance = generate_instance(config)
    fixed_cashflow = build_fixed_period_financial_model(instance)
    solution = solve_growth_plan(instance, verbose=verbose_solver)
    optimized_results = extract_results(instance, solution)
    summary = summarize_results(optimized_results)
    dcf = calculate_dcf(optimized_results, instance)
    multiples_valuation = calculate_multiples_valuation(optimized_results, instance)
    unit_economics = calculate_unit_economics(optimized_results, instance, dcf)

    result = {
        "instance": instance,
        "fixed_cashflow": fixed_cashflow,
        "solution": solution,
        "optimized_results": optimized_results,
        "summary": summary,
        "dcf": dcf,
        "multiples_valuation": multiples_valuation,
        "unit_economics": unit_economics,
    }

    if output_dir is not None:
        result["artifacts"] = generate_report(result, output_dir)

    return result

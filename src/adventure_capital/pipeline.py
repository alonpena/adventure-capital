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


def run_pipeline(
    config: dict[str, Any],
    *,
    output_dir: str | None = None,
    verbose_solver: bool = False,
    baseline_only: bool = True,
    document_path: str | None = None,
) -> dict[str, Any]:
    """Run full pipeline and optionally generate Phase 4 artifacts.

    If baseline_only is True, runs only the deterministic model baseline.
    If baseline_only is False, orchestrates the entire due diligence and stochastic assessment flow.
    """
    if not baseline_only:
        from pathlib import Path
        from datetime import datetime
        from adventure_capital.due_diligence.workflow import run_assessment

        out_dir = output_dir
        if out_dir is None:
            stamp = datetime.now().strftime("%y-%d-%m-%H:%M:%S")
            out_dir = str(Path("runs") / stamp)

        return run_assessment(config, output_dir=out_dir, verbose_solver=verbose_solver)

    instance = generate_instance(config)

    # Propagate DCF parameters from document YAML if provided
    if document_path is not None:
        import yaml
        from pathlib import Path
        doc_path = Path(document_path)
        if doc_path.exists():
            doc = yaml.safe_load(doc_path.read_text(encoding="utf-8")) or {}
            dcf_params = doc.get("dcf", {})
            
            # WACC propagation
            tasa_descuento = dcf_params.get("tasa_descuento")
            if tasa_descuento is None:
                # CAPM-based WACC calculation
                beta_capm = float(dcf_params.get("beta_capm", 1.0))
                rf = float(dcf_params.get("Rf_us", dcf_params.get("Rf_local", 0.0)))
                rm = float(dcf_params.get("Rm", 0.0))
                country_risk = float(dcf_params.get("country_risk", 0.0))
                risk_penalty = float(dcf_params.get("castigo_riesgo", 0.0))
                tasa_descuento = rf + beta_capm * (rm - rf) + country_risk + risk_penalty
            
            # Update WACC & beta in instance
            instance["beta_anual"] = float(tasa_descuento)
            instance["beta"] = (1 + instance["beta_anual"]) ** (1 / 12) - 1
            
            # Re-calculate discount factors
            periods = instance.get("T", [])
            instance["descuento"] = {t: 1 / (1 + instance["beta"]) ** t for t in periods}
            
            # Merge DCF parameters into params/parametros
            for p_key in ["parametros", "params"]:
                if p_key in instance:
                    instance[p_key]["valor_residual_metodo"] = dcf_params.get("valor_residual_metodo", "none")
                    if "ebitda_multiple" in dcf_params:
                        instance[p_key]["ebitda_multiple"] = dcf_params["ebitda_multiple"]
                    if "gordon_g" in dcf_params:
                        instance[p_key]["gordon_g"] = dcf_params["gordon_g"]

    # Cross-validation for residual value parameters
    val_method = instance.get("parametros", instance.get("params", {})).get("valor_residual_metodo", "none")
    if val_method == "ebitda_multiple":
        ebitda_mult = instance.get("parametros", instance.get("params", {})).get("ebitda_multiple")
        if ebitda_mult is None:
            raise ValueError("ebitda_multiple es requerido cuando valor_residual_metodo es 'ebitda_multiple'")
    elif val_method == "gordon":
        gordon_g = instance.get("parametros", instance.get("params", {})).get("gordon_g")
        if gordon_g is None:
            raise ValueError("gordon_g es requerido cuando valor_residual_metodo es 'gordon'")

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
        import yaml
        from pathlib import Path
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        config_path = out_path / "config.yaml"
        config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")

        result["artifacts"] = generate_report(result, output_dir)

        from adventure_capital.standard_report.consistency import check_consistency
        doc_path_for_check = document_path if document_path else config_path
        report = check_consistency(output_dir, doc_path_for_check)
        if not report["all_passed"]:
            failed = [c["name"] for c in report["checks"] if not c["passed"] and not c.get("skipped")]
            raise RuntimeError(
                f"Consistency checks fallaron: {failed}. "
                f"Ver {output_dir}/consistency_report.json para detalle."
            )

    return result

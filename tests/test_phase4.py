from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.reporting import generate_report


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_pipeline_generates_phase4_artifacts(tmp_path):
    result = run_pipeline(_fast_config(), output_dir=str(tmp_path))

    expected = {
        "fixed_cashflow.csv",
        "optimized_results.csv",
        "dcf_cashflow.csv",
        "dcf_annual_summary.csv",
        "multiples_valuation.csv",
        "unit_economics.csv",
        "dashboard.png",
        "financial_report.md",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})
    assert expected.issubset({path.name for path in result["artifacts"].values()})
    assert (tmp_path / "dashboard.png").stat().st_size > 0
    assert "Reporte financiero" in (tmp_path / "financial_report.md").read_text(encoding="utf-8")


def test_generate_report_can_be_called_directly(tmp_path):
    result = run_pipeline(_fast_config())
    artifacts = generate_report(result, tmp_path)

    assert artifacts["financial_report"].exists()
    assert artifacts["dashboard"].exists()
    assert artifacts["optimized_results"].exists()

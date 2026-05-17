import subprocess

from adventure_capital.config import default_config
from adventure_capital.pipeline import run_pipeline


def _fast_config():
    config = default_config()
    config["H"] = 14
    config["solver"]["time_limit"] = 30
    return config


def test_cli_report_command_creates_html(tmp_path):
    run_pipeline(_fast_config(), output_dir=str(tmp_path))

    completed = subprocess.run(
        [
            "uv",
            "run",
            "adventure-capital",
            "report",
            "--input",
            str(tmp_path),
            "--document",
            "reports/valuation-base.yaml",
            "--gate",
            "skip",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Report written" in completed.stdout
    assert (tmp_path / "report.html").exists()
    assert (tmp_path / "report_data.json").exists()

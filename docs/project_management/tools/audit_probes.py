"""Read-only functional probes; only writes synthetic files to TemporaryDirectory."""

import copy
import json
import tempfile
from pathlib import Path

from jinja2 import select_autoescape
from adventure_capital.config import default_config, load_config, validate_config
from adventure_capital.pipeline import run_pipeline
from streamlit_pages.components import inline_report_html

out = {}
for key, value in {
    "alpha": 2,
    "ticket": float("nan"),
    "churn_anual": [1.2],
    "A_base": [-1] * 12,
}.items():
    config = copy.deepcopy(default_config())
    config["servicios"][0][key] = value
    try:
        validate_config(config)
        out[f"validation_accepts_{key}"] = True
    except (ValueError, TypeError):
        out[f"validation_accepts_{key}"] = False

config = load_config("configs/demo-mixed-channels.yaml")
config["H"] = 14
result = run_pipeline(config)
fixed = result["fixed_cashflow"]
solved = result["optimized_results"].query("t <= 12")
out["mixed_channels"] = {
    "status": result["solution"]["status"],
    **{
        f"{label}_{metric}": float(df[metric].sum())
        for label, df in [("fixed", fixed), ("milp", solved)]
        for metric in ["CAC", "EBITDA"]
    },
}
out["autoescape_report_html_j2"] = select_autoescape(["html", "xml"])("report.html.j2")
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "public_marker.txt").write_text("synthetic audit marker")
    (root / "run").mkdir()
    report = root / "run" / "report.html"
    report.write_text('<img src="../public_marker.txt">')
    out["inlines_file_outside_run"] = "data:image/txt;base64," in inline_report_html(
        report
    )
Path("docs/project_management/evidence/probes.json").write_text(
    json.dumps(out, indent=2) + "\n"
)
print(json.dumps(out, indent=2))

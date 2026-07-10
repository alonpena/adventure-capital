"""Benchmark/calibration harness for external YAML instances v1.

Usage:
    uv run python scripts/benchmark_instances_v1.py \
      --input-dir /Users/apena/Desktop/instances_yaml_v1 \
      --output outputs/benchmark_instances_v1

The input YAMLs are calibration proxies extracted from Excel/transcripts. This
script never mutates them. Installed base comments are diagnostic only: current
Adventure Capital model counts A_base cohorts, not pre-existing clients.
"""

from __future__ import annotations

import argparse
import copy
import csv
import math
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from adventure_capital.config import load_config  # noqa: E402
from adventure_capital.due_diligence.workflow import run_due_diligence  # noqa: E402
from adventure_capital.instance import generate_instance  # noqa: E402
from adventure_capital.model import build_model, solve_model  # noqa: E402
from adventure_capital.results import extract_results  # noqa: E402
from adventure_capital.unit_economics import compute_unit_economics_metrics  # noqa: E402
from adventure_capital.valuation import calculate_dcf  # noqa: E402


CASES = [
    "godemos.yaml",
    "entrena-en-casa.yaml",
    "beloop.yaml",
    "kavacomex.yaml",
]

EXCEL_TARGETS = {
    "godemos": {"revenue_y1": 303_300.0, "ebitda_y1": 177_100.0, "VAN": 2_005_100.0},
    "entrena-en-casa": {
        "revenue_y1": 173_000.0,
        "ebitda_y1": -17_800.0,
        "VAN": 1_412_850.0,
    },
    "beloop": {"revenue_y1": 827_700.0, "ebitda_y1": 439_600.0, "VAN": 1_923_300.0},
    "kavacomex": {"revenue_y1": 135_300.0, "ebitda_y1": -95_600.0, "VAN": 1_789_200.0},
    "aijourney": {
        "revenue_y1": 1_564_564.3136843578,
        "ebitda_y1": 728_708.7770960075,
        "VAN": 2_183_368.6176998935,
    },
    "entrena-en-casa-calibrated": {
        "revenue_y1": 173_000.0,
        "ebitda_y1": -17_800.0,
        "VAN": 1_412_850.0,
    },
}

CASE_INTERPRETATION = {
    "godemos": "Main validation case: raw YAML is the cleanest Excel-aligned baseline.",
    "entrena-en-casa": "Calibration / initial_clients diagnosis: revenue gap likely reflects installed base and ticket/c_min calibration.",
    "entrena-en-casa-calibrated": "First-pass Entrena proposal: ticket scaled to about 328.8 for revenue calibration; source YAML untouched.",
    "beloop": "Structural stress case: Y1 useful; VAN may diverge due to setup/consulting/downgrades not modelled.",
    "kavacomex": "Structural stress case: logistics/freelance/ABC are not structurally represented.",
    "aijourney": "Additional external validation if Excel target extraction is accepted; current repo config is the proxy.",
}

CSV_COLUMNS = [
    "case",
    "mode",
    "status",
    "revenue_y1",
    "ebitda_y1",
    "revenue_y3",
    "ebitda_y3",
    "VAN",
    "revenue_y1_delta_vs_excel",
    "ebitda_y1_delta_vs_excel",
    "VAN_delta_vs_excel",
    "revenue_y1_pct_error_vs_excel",
    "ebitda_y1_pct_error_vs_excel",
    "VAN_pct_error_vs_excel",
    "stock_m12",
    "stock_m36",
    "C12",
    "ratio_m36_C12",
    "min_cash",
    "final_cash",
    "annual_ltv",
    "cac_per_customer",
    "ltv_cac",
    "gross_margin",
    "DD_verdict",
    "diagnostics",
]


def _pct_error(actual: float | None, target: float) -> float | None:
    if actual is None or target == 0:
        return None
    return (actual - target) / abs(target)


def _has_installed_base_comment(raw_yaml: str) -> bool:
    comments = "\n".join(line for line in raw_yaml.splitlines() if line.lstrip().startswith("#"))
    return bool(
        re.search(
            r"(base actual|base instalada|clientes actuales|clientes existentes|"
            r"installed base|current clients)",
            comments,
            flags=re.IGNORECASE,
        )
    )


def _target_core_overlay(seed: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(seed)
    cfg["investment_thesis"] = {
        "multiple": 3.0,
        "horizon_months": 36,
        "base_month": 12,
        "dd_revenue_gate_usd": 1_000_000,
        "interpolation": "geometric",
    }
    cfg["growth_commitment"] = {
        "enabled": True,
        "source": "vc_minimum",
        "checkpoints": "annual",
    }
    cfg["acquisition_ceiling"] = {"enabled": False}
    cfg["acquisition_envelope"] = {
        "enabled": True,
        "source": "vc_minimum",
        "slack_year2": 0.0,
        "slack_year3": 0.0,
    }
    cfg["solver"] = {**cfg.get("solver", {}), "verbose": False}
    return cfg


def create_entrena_calibrated_proposal(input_dir: Path, output_dir: Path) -> Path:
    """Write first-pass Entrena proposal to output only; never mutate source YAML."""
    source = input_dir / "entrena-en-casa.yaml"
    cfg = load_config(source)
    if not cfg.get("servicios"):
        raise ValueError("entrena-en-casa.yaml has no servicios block")
    cfg["servicios"][0]["ticket"] = 328.8
    proposal_dir = output_dir / "proposed_yaml"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    path = proposal_dir / "entrena-en-casa-ticket3288.yaml"
    header = (
        "# Generated proposal for pre-UI validation.\n"
        "# Source: entrena-en-casa.yaml copied in memory; source YAML not edited.\n"
        "# Change: first service ticket set to 328.8 for first-pass revenue calibration.\n"
        "# initial_clients is not implemented here.\n\n"
    )
    path.write_text(header + yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def _run_dd_verdict(config: dict[str, Any], dd_output_dir: Path, *, enabled: bool) -> str:
    if not enabled:
        return "not_run"
    try:
        result = run_due_diligence(
            config,
            output_dir=dd_output_dir,
            verbose_solver=False,
        )
    except Exception as exc:  # DD is advisory for this calibration harness.
        return f"unavailable: {type(exc).__name__}: {exc}"
    return result["verdict"].verdict


def _run_case_mode(
    *,
    case: str,
    mode: str,
    config: dict[str, Any],
    raw_yaml: str,
    dd_output_dir: Path,
    run_dd: bool,
) -> dict[str, Any]:
    targets = EXCEL_TARGETS[case]
    row: dict[str, Any] = {
        "case": case,
        "mode": mode,
        "status": None,
        "DD_verdict": "not_run",
    }
    row.update({col: None for col in CSV_COLUMNS if col not in row})

    try:
        instance = generate_instance(config)
        solution = solve_model(
            build_model(instance),
            time_limit=int(config.get("solver", {}).get("time_limit", 120)),
            verbose=False,
        )
    except Exception as exc:
        row["status"] = f"error: {type(exc).__name__}: {exc}"
        row["diagnostics"] = "model build/solve failed; inspect YAML schema and constraints"
        return row

    row["status"] = solution["status"]
    if solution["status"] != "Optimal":
        row["DD_verdict"] = _run_dd_verdict(config, dd_output_dir, enabled=run_dd)
        row["diagnostics"] = "non-Optimal solve; inspect infeasibility/unboundedness before calibration"
        return row

    df = extract_results(instance, solution)
    dcf = calculate_dcf(df, instance)
    unit = compute_unit_economics_metrics(df, instance, dcf)

    year_1 = df[df["Año"] == 1]
    year_3 = df[df["Año"] == 3]
    stock = df.groupby("t")["Clientes_activos"].sum()
    revenue_total = float(df["Ingresos"].sum())
    op_cost_total = float(df["Costo_operacional"].sum())
    stock_m12 = float(stock.loc[12]) if 12 in stock.index else None
    stock_m36 = float(stock.loc[36]) if 36 in stock.index else None
    c12 = float(instance.get("growth_commitment", {}).get("C12") or stock_m12 or 0.0)
    van = float(dcf["VAN"])

    row.update(
        {
            "revenue_y1": float(year_1["Ingresos"].sum()),
            "ebitda_y1": float(year_1["EBITDA"].sum()),
            "revenue_y3": float(year_3["Ingresos"].sum()) if not year_3.empty else None,
            "ebitda_y3": float(year_3["EBITDA"].sum()) if not year_3.empty else None,
            "VAN": van,
            "stock_m12": stock_m12,
            "stock_m36": stock_m36,
            "C12": c12,
            "ratio_m36_C12": stock_m36 / c12 if stock_m36 is not None and c12 > 0 else None,
            "min_cash": float(df["Caja"].min()),
            "final_cash": float(df["Caja"].iloc[-1]),
            "annual_ltv": float(unit["annual_ltv"]),
            "cac_per_customer": float(unit["cac_per_customer"]),
            "ltv_cac": float(unit["ltv_cac"]) if not math.isnan(unit["ltv_cac"]) else None,
            "gross_margin": 1 - op_cost_total / revenue_total if revenue_total > 0 else None,
        }
    )
    row["revenue_y1_delta_vs_excel"] = row["revenue_y1"] - targets["revenue_y1"]
    row["ebitda_y1_delta_vs_excel"] = row["ebitda_y1"] - targets["ebitda_y1"]
    row["VAN_delta_vs_excel"] = row["VAN"] - targets["VAN"]
    row["revenue_y1_pct_error_vs_excel"] = _pct_error(row["revenue_y1"], targets["revenue_y1"])
    row["ebitda_y1_pct_error_vs_excel"] = _pct_error(row["ebitda_y1"], targets["ebitda_y1"])
    row["VAN_pct_error_vs_excel"] = _pct_error(row["VAN"], targets["VAN"])
    row["DD_verdict"] = _run_dd_verdict(config, dd_output_dir, enabled=run_dd)
    row["diagnostics"] = " | ".join(_diagnostics(row, raw_yaml))
    return row


def _diagnostics(row: dict[str, Any], raw_yaml: str) -> list[str]:
    messages: list[str] = []
    rev_err = row.get("revenue_y1_pct_error_vs_excel")
    ebitda_err = row.get("ebitda_y1_pct_error_vs_excel")
    van_err = row.get("VAN_pct_error_vs_excel")

    if rev_err is not None and abs(rev_err) > 0.20:
        messages.append("revenue_y1 error >20%; recommend ticket scaling")
    if (
        rev_err is not None
        and rev_err < -0.20
        and _has_installed_base_comment(raw_yaml)
    ):
        messages.append(
            "possible missing installed base / initial_clients; current model only counts A_base cohorts"
        )
    if (
        ebitda_err is not None
        and abs(ebitda_err) > 0.20
        and rev_err is not None
        and abs(rev_err) <= 0.20
    ):
        messages.append("EBITDA_y1 error >20% after revenue close; recommend c_u/c_min/RRHH/g_adm review")
    ltv_cac = row.get("ltv_cac")
    if ltv_cac is not None and ltv_cac > 20:
        messages.append(
            "unit economics inflated; inspect blended ticket, churn, CAC, setup recurrence, fixed costs excluded from LTV"
        )
    if (
        van_err is not None
        and abs(van_err) > 0.20
        and rev_err is not None
        and ebitda_err is not None
        and abs(rev_err) <= 0.20
        and abs(ebitda_err) <= 0.20
    ):
        messages.append(
            "valuation divergence likely due to growth law / terminal value / Excel top-down curve; do not calibrate VAN directly"
        )
    return messages or ["no automatic calibration warning"]


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, rows: list[dict[str, Any]], input_dir: Path, run_dd: bool) -> None:
    lines = [
        "# Benchmark instances v1",
        "",
        f"- Input dir: `{input_dir}`",
        "- Modes: `raw_yaml`, `target_core`",
        f"- DD verdict: {'enabled' if run_dd else 'not_run'}",
        "- Note: installed base comments are diagnostics only; current model counts A_base cohorts.",
        "",
        "## Summary",
        "",
        "| case | mode | status | revenue_y1 | ebitda_y1 | revenue_y3 | ebitda_y3 | VAN | "
        "stock_m12 | stock_m36 | ratio_m36_C12 | min_cash | ltv_cac | DD verdict |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {case} | {mode} | {status} | {revenue_y1} | {ebitda_y1} | {revenue_y3} | "
            "{ebitda_y3} | {van} | {stock_m12} | {stock_m36} | {ratio} | {min_cash} | "
            "{ltv_cac} | {dd} |".format(
                case=row["case"],
                mode=row["mode"],
                status=row["status"],
                revenue_y1=_fmt(row["revenue_y1"]),
                ebitda_y1=_fmt(row["ebitda_y1"]),
                revenue_y3=_fmt(row["revenue_y3"]),
                ebitda_y3=_fmt(row["ebitda_y3"]),
                van=_fmt(row["VAN"]),
                stock_m12=_fmt(row["stock_m12"]),
                stock_m36=_fmt(row["stock_m36"]),
                ratio=_fmt(row["ratio_m36_C12"]),
                min_cash=_fmt(row["min_cash"]),
                ltv_cac=_fmt(row["ltv_cac"]),
                dd=row["DD_verdict"],
            )
        )

    lines += ["", "## Case interpretation", ""]
    rows_by_case = {
        case: [r for r in rows if r["case"] == case]
        for case in EXCEL_TARGETS
        if any(r["case"] == case for r in rows)
    }
    for case, case_rows in rows_by_case.items():
        lines += [f"### {case}", "", CASE_INTERPRETATION[case], ""]
        for row in case_rows:
            lines += [
                f"- `{row['mode']}` diagnostics: {row.get('diagnostics') or '-'}",
                f"- `{row['mode']}` deltas vs Excel: revenue_y1 {_fmt(row['revenue_y1_delta_vs_excel'])}, "
                f"ebitda_y1 {_fmt(row['ebitda_y1_delta_vs_excel'])}, VAN {_fmt(row['VAN_delta_vs_excel'])}",
            ]
        lines.append("")

    lines += [
        "## Extracted external targets",
        "",
        "Targets are taken from `INFORME_CONSISTENCIA.md` for GoDemos/Entrena/Beloop/KavaComex.",
        "",
        "AiJourney targets were extracted from `Planilla Evaluación AiJourney (1).xlsx`: "
        "Revenue Y1 = 1,564,564.31 USD, EBITDA Y1 = 728,708.78 USD, "
        "VAN Chile / post-money reference = 2,183,368.62 USD.",
        "",
        "Asesorías targets were readable from `3) Planilla Modelamiento con asesorías.xlsx`: "
        "Revenue Y1 = 78,395 USD; EBITDA Y1 before fee = 35,039.60 USD; "
        "EBITDA Y1 after fee = 19,360.46 USD; value after fee = 189,470.10 USD. "
        "No Asesorías YAML was generated because a full Adventure Capital config would require "
        "delivery-cost/capacity assumptions not cleanly extractable without inventing unknowns.",
        "",
    ]

    lines += [
        "## Target core overlay",
        "",
        "Applied in memory only:",
        "",
        "```yaml",
        "investment_thesis:",
        "  multiple: 3.0",
        "  horizon_months: 36",
        "  base_month: 12",
        "growth_commitment:",
        "  enabled: true",
        "  source: vc_minimum",
        "  checkpoints: annual",
        "acquisition_ceiling:",
        "  enabled: false",
        "acquisition_envelope:",
        "  enabled: true",
        "  source: vc_minimum",
        "  slack_year2: 0.0",
        "  slack_year3: 0.0",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--extended-pre-ui",
        action="store_true",
        help="Emit extended_benchmark.* and include AiJourney/proposed Entrena calibration.",
    )
    parser.add_argument(
        "--aijourney-config",
        type=Path,
        default=Path("configs/aijourney.yaml"),
        help="AiJourney proxy config used only with --extended-pre-ui.",
    )
    parser.add_argument(
        "--create-entrena-proposal",
        action="store_true",
        help="Create output/proposed_yaml/entrena-en-casa-ticket3288.yaml and benchmark it.",
    )
    parser.add_argument(
        "--skip-dd",
        action="store_true",
        help="Skip due diligence verdict runs; CSV/MD will mark DD_verdict=not_run.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_dir: Path = args.input_dir
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    dd_root = output_dir / "due_diligence"
    with tempfile.TemporaryDirectory(prefix="benchmark_instances_v1_") as tmp:
        dd_base = dd_root if not args.skip_dd else Path(tmp)
        case_paths = [input_dir / filename for filename in CASES]
        if args.extended_pre_ui:
            case_paths.append(args.aijourney_config)
            if args.create_entrena_proposal:
                case_paths.append(create_entrena_calibrated_proposal(input_dir, output_dir))

        for case_path in case_paths:
            case = case_path.stem
            if case == "entrena-en-casa-ticket3288":
                case = "entrena-en-casa-calibrated"
            raw_yaml = case_path.read_text(encoding="utf-8")
            if case == "entrena-en-casa-calibrated":
                raw_yaml = (input_dir / "entrena-en-casa.yaml").read_text(encoding="utf-8")
            seed = load_config(case_path)
            modes = {
                "raw_yaml": copy.deepcopy(seed),
                "target_core": _target_core_overlay(seed),
            }
            for mode, config in modes.items():
                print(f"running {case} / {mode}")
                rows.append(
                    _run_case_mode(
                        case=case,
                        mode=mode,
                        config=config,
                        raw_yaml=raw_yaml,
                        dd_output_dir=dd_base / case / mode,
                        run_dd=not args.skip_dd,
                    )
                )

    stem = "extended_benchmark" if args.extended_pre_ui else "benchmark_instances_v1"
    csv_path = output_dir / f"{stem}.csv"
    md_path = output_dir / f"{stem}.md"
    _write_csv(csv_path, rows)
    _write_markdown(md_path, rows, input_dir, run_dd=not args.skip_dd)
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

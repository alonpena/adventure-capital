"""Scenario sanity matrix for pre-UI validation.

Usage:
    uv run python scripts/scenario_sanity_matrix.py \
      --input-dir /Users/apena/Desktop/instances_yaml_v1 \
      --output outputs/pre_ui_validation

Runs archetype configs through small post-solve parameter overlays. It does not
edit source YAMLs and does not implement initial_clients.
"""

from __future__ import annotations

import argparse
import copy
import csv
import math
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

_ROOT = str(Path(__file__).resolve().parent.parent)
_SCRIPTS = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from adventure_capital.config import load_config  # noqa: E402
from adventure_capital.instance import generate_instance  # noqa: E402
from adventure_capital.model import build_model, solve_model  # noqa: E402
from adventure_capital.results import extract_results, summarize_results  # noqa: E402
from adventure_capital.unit_economics import compute_unit_economics_metrics  # noqa: E402
from adventure_capital.valuation import calculate_dcf  # noqa: E402
from benchmark_instances_v1 import _run_dd_verdict, _target_core_overlay  # noqa: E402


CSV_COLUMNS = [
    "case",
    "archetype",
    "overlay",
    "status",
    "VAN",
    "total_revenue",
    "total_ebitda",
    "revenue_y1",
    "ebitda_y1",
    "revenue_y3",
    "ebitda_y3",
    "min_cash",
    "final_cash",
    "ratio_m36_C12",
    "total_acquisition",
    "annual_ltv",
    "cac_per_customer",
    "ltv_cac",
    "DD_verdict",
    "notes",
]


Overlay = tuple[str, Callable[[dict[str, Any]], dict[str, Any]]]


def _scale_tickets(config: dict[str, Any], factor: float) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    for service in cfg["servicios"]:
        service["ticket"] = float(service["ticket"]) * factor
    return cfg


def _scale_churn(config: dict[str, Any], factor: float) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    for service in cfg["servicios"]:
        service["churn_anual"] = [min(0.99, max(0.0, float(v) * factor)) for v in service["churn_anual"]]
    return cfg


def _scale_meta(config: dict[str, Any], factor: float) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    cfg["meta"] = max(0.1, float(cfg["meta"]) * factor)
    return cfg


def _scale_vc(config: dict[str, Any], factor: float) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    cfg["VC"] = float(cfg["VC"]) * factor
    return cfg


def _target_core_multiple(config: dict[str, Any], multiple: float) -> dict[str, Any]:
    cfg = _target_core_overlay(config)
    cfg["investment_thesis"]["multiple"] = multiple
    return cfg


def _salesforce_only(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    channels = copy.deepcopy(cfg.get("channels", {}))
    if "salesforce" not in channels or "advertising" not in channels:
        raise ValueError("channel overlay requires existing salesforce+advertising config")
    channels["salesforce"] = {"active": True, "min_share": 0.0, "max_share": 1.0}
    channels["advertising"]["active"] = False
    channels.setdefault("third_party", {"active": False, "min_share": 0.0, "max_share": 1.0})
    channels["third_party"]["active"] = False
    cfg["channels"] = channels
    return cfg


def _advertising_only(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    channels = copy.deepcopy(cfg.get("channels", {}))
    if "salesforce" not in channels or "advertising" not in channels:
        raise ValueError("channel overlay requires existing salesforce+advertising config")
    channels["salesforce"] = {"active": False, "min_share": 0.0, "max_share": 1.0}
    channels["advertising"]["active"] = True
    channels["advertising"]["min_share"] = 0.0
    channels["advertising"]["max_share"] = 1.0
    channels.setdefault("third_party", {"active": False, "min_share": 0.0, "max_share": 1.0})
    channels["third_party"]["active"] = False
    cfg["channels"] = channels
    return cfg


def _mixed_channels(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    channels = copy.deepcopy(cfg.get("channels", {}))
    if "salesforce" not in channels or "advertising" not in channels:
        raise ValueError("channel overlay requires existing salesforce+advertising config")
    channels["salesforce"] = {"active": True, "min_share": 0.3, "max_share": 1.0}
    channels["advertising"]["active"] = True
    channels["advertising"]["min_share"] = 0.0
    channels["advertising"]["max_share"] = min(1.0, max(0.4, float(channels["advertising"].get("max_share", 1.0))))
    channels.setdefault("third_party", {"active": False, "min_share": 0.0, "max_share": 1.0})
    channels["third_party"]["active"] = False
    cfg["channels"] = channels
    return cfg


def _base_overlays(config: dict[str, Any]) -> list[Overlay]:
    overlays: list[Overlay] = [
        ("baseline", copy.deepcopy),
        ("ticket_x0.8", lambda c: _scale_tickets(c, 0.8)),
        ("ticket_x1.2", lambda c: _scale_tickets(c, 1.2)),
        ("churn_x0.5", lambda c: _scale_churn(c, 0.5)),
        ("churn_x1.5", lambda c: _scale_churn(c, 1.5)),
        ("meta_x0.5", lambda c: _scale_meta(c, 0.5)),
        ("meta_x1.5", lambda c: _scale_meta(c, 1.5)),
        ("VC_x0.5", lambda c: _scale_vc(c, 0.5)),
        ("VC_x2.0", lambda c: _scale_vc(c, 2.0)),
        ("target_core_M2", lambda c: _target_core_multiple(c, 2.0)),
        ("target_core_M3", lambda c: _target_core_multiple(c, 3.0)),
        ("target_core_M5", lambda c: _target_core_multiple(c, 5.0)),
    ]
    channels = config.get("channels", {})
    if "salesforce" in channels and "advertising" in channels:
        overlays.extend(
            [
                ("channels_salesforce_only", _salesforce_only),
                ("channels_advertising_only", _advertising_only),
                ("channels_mixed", _mixed_channels),
            ]
        )
    return overlays


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(result) else result


def _run_config(
    *,
    case: str,
    archetype: str,
    overlay: str,
    config: dict[str, Any],
    dd_output_dir: Path,
    run_dd: bool,
) -> dict[str, Any]:
    row = {col: None for col in CSV_COLUMNS}
    row.update(
        {
            "case": case,
            "archetype": archetype,
            "overlay": overlay,
            "DD_verdict": "not_run",
        }
    )
    try:
        instance = generate_instance(config)
        solution = solve_model(
            build_model(instance),
            time_limit=int(config.get("solver", {}).get("time_limit", 120)),
            verbose=False,
        )
    except Exception as exc:
        row["status"] = f"error: {type(exc).__name__}: {exc}"
        row["notes"] = "build/solve failed"
        return row

    row["status"] = solution["status"]
    if solution["status"] != "Optimal":
        row["DD_verdict"] = _run_dd_verdict(config, dd_output_dir, enabled=run_dd)
        row["notes"] = "non-Optimal; check infeasible/unbounded path"
        return row

    df = extract_results(instance, solution)
    summary = summarize_results(df)
    dcf = calculate_dcf(df, instance)
    unit = compute_unit_economics_metrics(df, instance, dcf)
    year_1 = df[df["Año"] == 1]
    year_3 = df[df["Año"] == 3]
    stock = df.groupby("t")["Clientes_activos"].sum()
    stock_m36 = _safe_float(stock.loc[36]) if 36 in stock.index else None
    c12 = _safe_float(instance.get("growth_commitment", {}).get("C12"))
    if c12 is None and 12 in stock.index:
        c12 = _safe_float(stock.loc[12])
    row.update(
        {
            "VAN": float(dcf["VAN"]),
            "total_revenue": summary["total_revenue"],
            "total_ebitda": summary["total_ebitda"],
            "revenue_y1": float(year_1["Ingresos"].sum()),
            "ebitda_y1": float(year_1["EBITDA"].sum()),
            "revenue_y3": float(year_3["Ingresos"].sum()) if not year_3.empty else None,
            "ebitda_y3": float(year_3["EBITDA"].sum()) if not year_3.empty else None,
            "min_cash": summary["minimum_cash"],
            "final_cash": summary["final_cash"],
            "ratio_m36_C12": stock_m36 / c12 if stock_m36 is not None and c12 and c12 > 0 else None,
            "total_acquisition": summary["total_acquisition"],
            "annual_ltv": _safe_float(unit["annual_ltv"]),
            "cac_per_customer": _safe_float(unit["cac_per_customer"]),
            "ltv_cac": _safe_float(unit["ltv_cac"]),
            "DD_verdict": _run_dd_verdict(config, dd_output_dir, enabled=run_dd),
            "notes": "ok",
        }
    )
    return row


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _case_specs(input_dir: Path, proposed_dir: Path) -> list[tuple[str, str, Path]]:
    specs = [
        ("aijourney", "B2B SaaS sales-led", Path("configs/aijourney.yaml")),
        ("demo-advertising-only", "Advertising-led", Path("configs/demo-advertising-only.yaml")),
        ("demo-mixed-channels", "Mixed channels", Path("configs/demo-mixed-channels.yaml")),
        ("demo-working-capital", "Capital-constrained", Path("configs/demo-working-capital.yaml")),
        ("demo-growth-core", "Target-driven growth", Path("configs/demo-growth-core.yaml")),
        ("godemos", "B2C subscription", input_dir / "godemos.yaml"),
    ]
    entrena_proposal = proposed_dir / "entrena-en-casa-ticket3288.yaml"
    if entrena_proposal.exists():
        specs.append(("entrena-calibrated", "Services/consulting", entrena_proposal))
    return specs


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _sanity_notes(rows: list[dict[str, Any]]) -> list[str]:
    notes: list[str] = []
    for case in sorted({r["case"] for r in rows}):
        case_rows = {r["overlay"]: r for r in rows if r["case"] == case}
        base = case_rows.get("baseline", {})
        up = case_rows.get("ticket_x1.2", {})
        down = case_rows.get("ticket_x0.8", {})
        churn_up = case_rows.get("churn_x1.5", {})
        if base.get("status") == up.get("status") == down.get("status") == "Optimal":
            if (up.get("VAN") or -math.inf) < (base.get("VAN") or -math.inf):
                notes.append(f"{case}: ticket +20% lowered VAN; inspect proportional costs/constraints.")
        if base.get("status") == churn_up.get("status") == "Optimal":
            if (churn_up.get("ratio_m36_C12") or math.inf) > (base.get("ratio_m36_C12") or math.inf):
                notes.append(f"{case}: churn +50% raised final stock ratio; inspect constraint interaction.")
    return notes or ["No automatic monotonicity warning in basic ticket/churn checks."]


def _write_markdown(path: Path, rows: list[dict[str, Any]], input_dir: Path, run_dd: bool) -> None:
    lines = [
        "# Scenario sanity matrix",
        "",
        f"- Input dir: `{input_dir}`",
        f"- DD verdict: {'enabled' if run_dd else 'not_run'}",
        "- Source YAMLs are not edited.",
        "- `initial_clients` is not implemented.",
        "",
        "## Summary",
        "",
        "| case | archetype | overlay | status | VAN | revenue_y1 | ebitda_y1 | "
        "min_cash | ratio_m36_C12 | ltv_cac |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {case} | {archetype} | {overlay} | {status} | {van} | {rev1} | {ebitda1} | "
            "{min_cash} | {ratio} | {ltv_cac} |".format(
                case=row["case"],
                archetype=row["archetype"],
                overlay=row["overlay"],
                status=row["status"],
                van=_fmt(row["VAN"]),
                rev1=_fmt(row["revenue_y1"]),
                ebitda1=_fmt(row["ebitda_y1"]),
                min_cash=_fmt(row["min_cash"]),
                ratio=_fmt(row["ratio_m36_C12"]),
                ltv_cac=_fmt(row["ltv_cac"]),
            )
        )
    lines += [
        "",
        "## Required interpretation",
        "",
        "- GoDemos = main validation case.",
        "- Entrena calibrated proposal = calibration/initial_clients diagnosis when proposal YAML exists.",
        "- Beloop/KavaComex stay structural stress cases in extended benchmark, not in this matrix.",
        "- AiJourney = additional external validation proxy from `configs/aijourney.yaml`.",
        "- Asesorías = target extraction documented in extended benchmark; YAML pending clean input assumptions.",
        "",
        "## Sanity notes",
        "",
    ]
    lines.extend(f"- {note}" for note in _sanity_notes(rows))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--run-dd",
        action="store_true",
        help="Run full due diligence per matrix row. Default keeps DD_verdict=not_run.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="scenario_sanity_matrix_") as tmp:
        dd_base = output_dir / "sanity_due_diligence" if args.run_dd else Path(tmp)
        for case, archetype, path in _case_specs(args.input_dir, output_dir / "proposed_yaml"):
            seed = load_config(path)
            for overlay, transform in _base_overlays(seed):
                try:
                    cfg = transform(seed)
                except Exception as exc:
                    rows.append(
                        {
                            **{col: None for col in CSV_COLUMNS},
                            "case": case,
                            "archetype": archetype,
                            "overlay": overlay,
                            "status": f"skipped: {type(exc).__name__}: {exc}",
                            "DD_verdict": "not_run",
                            "notes": "overlay not safe for this case",
                        }
                    )
                    continue
                print(f"running {case} / {overlay}")
                rows.append(
                    _run_config(
                        case=case,
                        archetype=archetype,
                        overlay=overlay,
                        config=cfg,
                        dd_output_dir=dd_base / case / overlay,
                        run_dd=args.run_dd,
                    )
                )

    csv_path = output_dir / "sanity_matrix.csv"
    md_path = output_dir / "sanity_matrix.md"
    _write_csv(csv_path, rows)
    _write_markdown(md_path, rows, args.input_dir, run_dd=args.run_dd)
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

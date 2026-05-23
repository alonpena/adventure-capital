"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from adventure_capital.calibration import run_calibration, write_calibration_report
from adventure_capital.config import load_config
from adventure_capital.pipeline import run_pipeline
from adventure_capital.standard_report import build_report_data_package, render_report


VERDICT_EXIT = {"PASS": 0, "WARN": 1, "FAIL": 2}


def _run_calibrate(args: argparse.Namespace) -> int:
    verdict = run_calibration(
        args.input,
        instance_path=args.config,
        document_path=args.document,
        schema_path=args.schema,
        thresholds_path=args.thresholds,
    )
    paths = write_calibration_report(verdict, args.input)
    print(f"Veredicto: {verdict.verdict}")
    print(f"  Cheques: {verdict.total_checks} (passed {verdict.passed}, warnings {verdict.warnings}, errors {verdict.errors}, skipped {verdict.skipped})")
    print(f"  JSON:    {paths['json']}")
    print(f"  Reporte: {paths['markdown']}")
    return VERDICT_EXIT.get(verdict.verdict, 0)


def _run_report(args: argparse.Namespace) -> int:
    gate_mode = args.gate
    if gate_mode != "skip":
        verdict = run_calibration(
            args.input,
            instance_path=args.config,
            document_path=args.document,
            schema_path=args.schema,
            thresholds_path=args.thresholds,
        )
        write_calibration_report(verdict, args.input)
        print(f"Calibración: {verdict.verdict} ({verdict.errors} errors, {verdict.warnings} warnings)")
        if verdict.verdict == "FAIL":
            print("✋ Gate FAIL — se bloquea generación de informe. Revisar calibration_report.md.")
            return 4
        if verdict.verdict == "WARN" and gate_mode == "strict":
            print("✋ Gate STRICT — bloqueado por warnings. Usar --gate warn-ok para forzar o ajustar configs/calibration.yaml.")
            return 3

    artifacts = build_report_data_package(
        args.input,
        document_path=args.document,
        blueprint_path=args.blueprint,
        schema_path=args.schema,
        instance_path=args.config,
    )
    report_path = render_report(args.input, pdf=args.pdf)
    print(f"Report data package written to {artifacts['report_data'].parent}")
    print(f"Report written to {report_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="adventure-capital")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run financial planning pipeline")
    run_parser.add_argument("--config", default="configs/base.yaml")
    run_parser.add_argument("--output", default=None)

    report_parser = subparsers.add_parser("report", help="Build standard valuation report data package")
    report_parser.add_argument("--input", required=True)
    report_parser.add_argument("--document", required=True)
    report_parser.add_argument("--blueprint", default="docs/report-blueprint.md")
    report_parser.add_argument("--schema", default="reports/schema/valuation-document.schema.yaml")
    report_parser.add_argument("--config", default=None,
                               help="Path to the original model config YAML (enables service-aware figures, tables, and calibration)")
    report_parser.add_argument("--thresholds", default="configs/calibration.yaml",
                               help="Path to calibration thresholds YAML")
    report_parser.add_argument("--gate", choices=["strict", "warn-ok", "skip"], default="strict",
                               help="Calibration gate behaviour (default: strict)")
    report_parser.add_argument("--pdf", action="store_true", help="Also render report.pdf")

    cal_parser = subparsers.add_parser("calibrate", help="Run calibration gate against an existing output directory")
    cal_parser.add_argument("--input", required=True)
    cal_parser.add_argument("--config", required=True, help="Path to model config YAML")
    cal_parser.add_argument("--document", default="reports/valuation-base.yaml")
    cal_parser.add_argument("--schema", default="reports/schema/valuation-document.schema.yaml")
    cal_parser.add_argument("--thresholds", default="configs/calibration.yaml")

    args = parser.parse_args()

    if args.command == "run":
        config = load_config(args.config)
        output_dir = args.output
        if output_dir is None:
            stamp = datetime.now().strftime("%y-%d-%m-%H:%M:%S")
            output_dir = str(Path("runs") / stamp)
        run_pipeline(config, output_dir=output_dir, baseline_only=False)
        print(f"Artifacts written to {output_dir}")
        return 0
    if args.command == "report":
        return _run_report(args)
    if args.command == "calibrate":
        return _run_calibrate(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

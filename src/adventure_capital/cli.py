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

_LEGACY_NOTE = (
    "⚠️  Comando legado en deprecación. Usar 'instances' / 'executions' "
    "(ver 'adventure-capital --help')."
)


# --------------------------------------------------------------------------- #
# Workflow MVP: instances + executions (filesystem registry)
# --------------------------------------------------------------------------- #
def _run_instances(args: argparse.Namespace) -> int:
    from adventure_capital import workflow_registry as reg

    if args.instances_command == "create":
        config = load_config(args.config)
        meta = reg.create_instance(config, name=args.name, config_source=args.config)
        print(f"Instancia creada: {meta['id']}")
        print(f"  Nombre: {meta['name']}")
        print(f"  Hash:   {meta['config_hash']}")
        return 0
    if args.instances_command == "list":
        rows = reg.list_instances()
        if not rows:
            print("Sin instancias.")
            return 0
        for m in rows:
            print(f"{m['id']}  {m['config_hash']}  {m['name']}")
        return 0
    if args.instances_command == "show":
        meta = reg.get_instance(args.instance_id)
        for key in ("id", "name", "config_hash", "config_source", "created_at"):
            print(f"{key}: {meta.get(key)}")
        return 0
    return 0


def _confirm_prompt(verdict_str: str) -> bool:
    answer = input(
        f"Veredicto DD '{verdict_str}' requiere confirmación para correr M4. ¿Continuar? [y/N] "
    )
    return answer.strip().lower() in {"y", "yes", "s", "si", "sí"}


def _run_executions(args: argparse.Namespace) -> int:
    from adventure_capital import workflow_registry as reg

    if args.executions_command == "run":
        confirm = None if args.yes else _confirm_prompt
        record = reg.run_execution(
            args.instance,
            name=args.name,
            run_stochastic=not args.no_stochastic,
            stochastic_time_limit=args.stochastic_time_limit,
            confirm=confirm,
        )
        print(f"Ejecución: {record['id']}  estado={record['status']}")
        for stage, state in record["stages"].items():
            print(f"  {stage}: {state}")
        print(f"  Reporte: {record['output_dir']}/report.html")
        return 0
    if args.executions_command == "list":
        rows = reg.list_executions()
        if not rows:
            print("Sin ejecuciones.")
            return 0
        for r in rows:
            print(f"{r['id']}  {r['status']}  {r['name']}")
        return 0
    if args.executions_command == "status":
        record = reg.get_execution(args.run_id)
        print(f"{record['id']}  estado={record['status']}")
        for stage, state in record["stages"].items():
            print(f"  {stage}: {state}")
        return 0
    if args.executions_command == "stochastic":
        record = reg.run_stochastic_only(
            args.run_id, stochastic_time_limit=args.stochastic_time_limit
        )
        print(f"M4 re-ejecutado: {record['id']}  M4={record['stages']['M4_STOCHASTIC']}")
        if record.get("m4_reason"):
            print(f"  Motivo bloqueo: {record['m4_reason']}")
        print(f"  Reporte: {record['output_dir']}/report.html")
        return 0
    if args.executions_command == "report":
        path = reg.regenerate_report(args.run_id)
        print(f"Reporte regenerado: {path}")
        return 0
    return 0


def _resolve_output(output_arg: str | None) -> str:
    if output_arg is not None:
        return output_arg
    stamp = datetime.now().strftime("%y-%d-%m-%H:%M:%S")
    return str(Path("runs") / stamp)


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


def _run_all(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    output_dir = _resolve_output(args.output)
    run_pipeline(config, output_dir=output_dir, baseline_only=False)
    artifacts = build_report_data_package(
        output_dir,
        document_path=args.document,
        blueprint_path=args.blueprint,
        schema_path=args.schema,
        instance_path=args.config,
    )
    report_path = render_report(output_dir, pdf=args.pdf)
    print(f"Artifacts written to {output_dir}")
    print(f"Report data package written to {artifacts['report_data'].parent}")
    print(f"Report written to {report_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="adventure-capital")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Workflow MVP: instances ---
    inst_parser = subparsers.add_parser("instances", help="Manage model instances (frozen configs)")
    inst_sub = inst_parser.add_subparsers(dest="instances_command", required=True)
    inst_create = inst_sub.add_parser("create", help="Freeze a config as a new instance")
    inst_create.add_argument("--config", default="configs/base.yaml")
    inst_create.add_argument("--name", default=None)
    inst_sub.add_parser("list", help="List instances")
    inst_show = inst_sub.add_parser("show", help="Show instance metadata")
    inst_show.add_argument("instance_id")

    # --- Workflow MVP: executions ---
    exec_parser = subparsers.add_parser("executions", help="Run and inspect assessment executions")
    exec_sub = exec_parser.add_subparsers(dest="executions_command", required=True)
    exec_run = exec_sub.add_parser("run", help="Run the assessment flow for an instance")
    exec_run.add_argument("--instance", required=True)
    exec_run.add_argument("--name", default=None)
    exec_run.add_argument("--yes", action="store_true", help="Auto-confirm warning/minor DD verdicts")
    exec_run.add_argument("--no-stochastic", action="store_true", help="Stop after M1-M3 (skip M4)")
    exec_run.add_argument("--stochastic-time-limit", type=int, default=None,
                          help="CBC time limit (s) for M4; defaults to backend M4 default")
    exec_sub.add_parser("list", help="List executions")
    exec_status = exec_sub.add_parser("status", help="Show execution stages")
    exec_status.add_argument("run_id")
    exec_stoch = exec_sub.add_parser("stochastic", help="Re-run M4 for an execution")
    exec_stoch.add_argument("run_id")
    exec_stoch.add_argument("--stochastic-time-limit", type=int, default=None)
    exec_report = exec_sub.add_parser("report", help="Regenerate report.html for an execution")
    exec_report.add_argument("run_id")

    run_parser = subparsers.add_parser("run", help="[deprecated] Run financial planning pipeline")
    run_parser.add_argument("--config", default="configs/base.yaml")
    run_parser.add_argument("--output", default=None)

    all_parser = subparsers.add_parser("all", help="Run full pipeline and render standard report")
    all_parser.add_argument("--config", default="configs/base.yaml")
    all_parser.add_argument("--output", default=None)
    all_parser.add_argument("--document", default="reports/valuation-base.yaml")
    all_parser.add_argument("--blueprint", default="docs/report-blueprint.md")
    all_parser.add_argument("--schema", default="reports/schema/valuation-document.schema.yaml")
    all_parser.add_argument("--pdf", action="store_true", help="Also render report.pdf")

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

    if args.command == "instances":
        return _run_instances(args)
    if args.command == "executions":
        return _run_executions(args)
    if args.command == "run":
        print(_LEGACY_NOTE)
        config = load_config(args.config)
        output_dir = _resolve_output(args.output)
        run_pipeline(config, output_dir=output_dir, baseline_only=False)
        print(f"Artifacts written to {output_dir}")
        return 0
    if args.command == "all":
        print(_LEGACY_NOTE)
        return _run_all(args)
    if args.command == "report":
        print(_LEGACY_NOTE)
        return _run_report(args)
    if args.command == "calibrate":
        print(_LEGACY_NOTE)
        return _run_calibrate(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

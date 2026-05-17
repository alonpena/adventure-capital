"""Command line interface."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from adventure_capital.config import load_config
from adventure_capital.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(prog="adventure-capital")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run financial planning pipeline")
    run_parser.add_argument("--config", default="configs/base.yaml")
    run_parser.add_argument("--output", default=None)

    args = parser.parse_args()

    if args.command == "run":
        config = load_config(args.config)
        output_dir = args.output
        if output_dir is None:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_dir = str(Path("outputs") / stamp)
        run_pipeline(config, output_dir=output_dir)
        print(f"Artifacts written to {output_dir}")


if __name__ == "__main__":
    main()

"""Stochastic objective-function sweep + distribution audit.

Answers "which objective should the stochastic model use?" empirically, on the
SAME scenario set, instead of arguing about CVaR in the abstract:

  - lambda in {0.0, 0.5, 1.0} at alpha = 0.15   (pure CVaR -> mean-CVaR -> risk-neutral)
  - alpha  in {0.05, 0.30}   at lambda = 0.5    (tail depth sensitivity)

For each combo: solve the SAA (N configurable, default 40 like the ADR 0011
sweep), then evaluate the committed plan ex-post on an independent LHS set and
report E[VAN], P5/P50, CVaR5, prob(VAN<0), and total planned acquisition
(months 13+). If the plan and CVaR barely move across rows, the objective is
NOT the source of conservatism — the distributions are.

Also prints the distribution audit: mean of each triangular multiplier, i.e.
the *built-in* optimism/pessimism of the scenario generator.

Usage:
    uv run python scripts/objective_sweep.py [--config configs/caso-base-1m.yaml]
        [--saa 40] [--eval 200] [--time-limit 180] [--output docs/analysis]
"""

from __future__ import annotations

import argparse
import copy
import csv
from pathlib import Path

from adventure_capital.config import load_config
from adventure_capital.stochastic.defaults import M4_DEFAULTS
from adventure_capital.stochastic.evaluate import evaluate_strategy
from adventure_capital.stochastic.model import solve_stochastic_plan
from adventure_capital.stochastic.results import summarize_distribution
from adventure_capital.stochastic.scenarios import (
    generate_evaluation_scenarios,
    generate_scenarios,
)

COMBOS: list[tuple[float, float]] = [
    (0.15, 0.0),   # pure CVaR (the "conservative" hypothesis)
    (0.15, 0.5),   # current default (ADR 0011)
    (0.15, 1.0),   # risk-neutral E[VAN]
    (0.05, 0.5),   # deeper tail
    (0.30, 0.5),   # shallower tail
]


def _plan_total(strategy: dict) -> float:
    plan = strategy["strategy"]["A_plan"]
    total = 0.0
    for key, value in plan.items():
        _, t = key.rsplit("_", 1)
        if int(t) >= 13:
            total += value
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/caso-base-1m.yaml")
    parser.add_argument("--saa", type=int, default=40)
    parser.add_argument("--eval", type=int, default=200)
    parser.add_argument("--time-limit", type=int, default=180)
    parser.add_argument("--output", default="docs/analysis")
    args = parser.parse_args()

    seed = load_config(args.config)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- distribution audit -------------------------------------------------
    dists = M4_DEFAULTS["distributions"]
    audit_rows = []
    for name, spec in dists.items():
        mean = (spec["min"] + spec["mode"] + spec["max"]) / 3.0
        audit_rows.append((name, spec["min"], spec["mode"], spec["max"], mean))

    # ---- objective sweep ----------------------------------------------------
    rows: list[dict] = []
    for alpha, lam in COMBOS:
        cfg = copy.deepcopy(seed)
        block = dict(cfg.get("stochastic", {}) or {})
        block.update(
            {
                "cvar_alpha": alpha,
                "mean_cvar_lambda": lam,
                "saa_scenario_count": args.saa,
                "evaluation_scenario_count": args.eval,
            }
        )
        cfg["stochastic"] = block

        saa_scenarios = generate_scenarios(cfg)
        solved = solve_stochastic_plan(cfg, saa_scenarios, time_limit=args.time_limit)
        eval_scenarios = generate_evaluation_scenarios(cfg)
        evaluation = evaluate_strategy(cfg, solved["strategy"], eval_scenarios)
        summary = summarize_distribution(evaluation, cvar_alpha=alpha)

        rows.append(
            {
                "alpha": alpha,
                "lambda": lam,
                "status": solved["status"],
                "insample_expected_van": solved["expected_van"],
                "insample_cvar": solved["cvar_van"],
                "expost_expected_van": summary["expected_van"],
                "expost_p5": summary["van_p5"],
                "expost_p50": summary["van_p50"],
                "expost_cvar_alpha": summary["cvar_5"],
                "prob_van_negative": summary["prob_van_negative"],
                "plan_acq_13plus": _plan_total(solved),
            }
        )
        print(f"done alpha={alpha} lambda={lam}: status={solved['status']} "
              f"E[VAN]expost={summary['expected_van']:,.0f} plan={rows[-1]['plan_acq_13plus']:,.0f}")

    # ---- artifacts ----------------------------------------------------------
    csv_path = out_dir / "objective_sweep.csv"
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    md = [
        "# Sweep de función objetivo estocástica",
        "",
        f"Seed: `{args.config}` · SAA N={args.saa} (seed fija: mismo set de escenarios) · "
        f"ex-post N={args.eval} independiente · `scripts/objective_sweep.py`",
        "",
        "## Auditoría de distribuciones (triangulares actuales, defaults.py)",
        "",
        "| multiplicador | min | modo | max | **media** |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, lo, mode, hi, mean in audit_rows:
        md.append(f"| {name} | {lo} | {mode} | {hi} | **{mean:.3f}** |")
    md += [
        "",
        "Media ≠ 1.0 = sesgo incorporado del generador de escenarios (optimismo del plan",
        "del cliente vs realidad promedio). Esto — no el CVaR — desplaza E[VAN] respecto",
        "del VAN determinista.",
        "",
        "## Resultados por objetivo  (max λ·E[VAN] + (1−λ)·CVaR_α)",
        "",
        "| α | λ | status | E[VAN] ex-post | P5 | P50 | CVaR_α ex-post | P(VAN<0) | adquisición plan m13+ |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        md.append(
            f"| {r['alpha']} | {r['lambda']} | {r['status']} | "
            f"{r['expost_expected_van']:,.0f} | {r['expost_p5']:,.0f} | "
            f"{r['expost_p50']:,.0f} | {r['expost_cvar_alpha']:,.0f} | "
            f"{r['prob_van_negative']:.1%} | {r['plan_acq_13plus']:,.0f} |"
        )
    (out_dir / "objective_sweep.md").write_text("\n".join(md) + "\n")
    print(f"\nwrote {csv_path} and {out_dir / 'objective_sweep.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

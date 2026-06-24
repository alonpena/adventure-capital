"""Calibrate the convex-CAC saturation rate theta to each instance's realized Motor ramp,
and compare the two growth brakes side by side (ADR 0013, "Both, compare").

For every benchmark instance this:
  1. solves the deterministic plan under the 3x market-saturation ceiling (ADR 0010);
  2. bisects theta so the convex-CAC optimum reproduces the founder's realized Motor
     year-2/year-1 acquisition ratio (traceable to observed data, never to VAN);
  3. prints Y2/Y1, Y3/Y2 and VAN for both modes plus the calibrated theta*.

theta is monotone decreasing in growth, so bisection is exact. theta* is the reproducible,
data-traceable growth driver; the 3x ceiling is reported as an upper-bound reference.

Usage:  uv run python scripts/calibrate_theta.py [--yaml-dir DIR] [--time-limit S]
"""

from __future__ import annotations

import argparse
import copy

import yaml

from adventure_capital.instance import generate_instance
from adventure_capital.model import solve_growth_plan
from adventure_capital.results import extract_results
from adventure_capital.valuation import calculate_dcf

# Realized Motor Y1/Y2/Y3 acquisition (source-of-truth Excel) -> Y2/Y1 calibration target.
MOTOR_RAMP = {
    "godemos": (274, 548, 1096),
    "entrena-en-casa": (96, 157, 318),
    "kavacomex": (83, 82.161729, 164.443992),
    "beloop": (82, 128, 144),
}


def load(yaml_dir: str, name: str, time_limit: int) -> dict:
    with open(f"{yaml_dir}/{name}.yaml") as f:
        cfg = yaml.safe_load(f)
    cfg["solver"] = {"name": "cbc", "time_limit": time_limit, "verbose": False}
    return cfg


def solve(config: dict) -> dict | None:
    inst = generate_instance(config)
    sol = solve_growth_plan(inst)
    if sol["status"] != "Optimal":
        return None
    df = extract_results(inst, sol)
    y1 = df[df["t"].between(1, 12)]["Adq_clientes"].sum()
    y2 = df[df["t"].between(13, 24)]["Adq_clientes"].sum()
    y3 = df[df["t"].between(25, 36)]["Adq_clientes"].sum()
    return {
        "van": calculate_dcf(df, inst)["VAN"],
        "r21": y2 / y1 if y1 else 0.0,
        "r32": y3 / y2 if y2 else 0.0,
    }


def _convex(base: dict, theta: float) -> dict | None:
    cfg = copy.deepcopy(base)
    cfg["convex_cac"] = {"enabled": True, "theta": theta}
    cfg["acquisition_ceiling"] = {"enabled": False}  # convex is the sole brake
    return solve(cfg)


def calibrate(base: dict, target: float, lo=0.5, hi=300.0, iters=14):
    """Bisect theta so convex Y2/Y1 == target. theta up -> ratio down (monotone)."""
    best = None
    for _ in range(iters):
        mid = (lo + hi) / 2
        res = _convex(base, mid)
        if res is None:
            hi = mid
            continue
        best = (mid, res)
        if res["r21"] > target:
            lo = mid  # too much growth -> more saturation
        else:
            hi = mid
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaml-dir", default="/Users/apena/Downloads/instances_yaml_v1")
    ap.add_argument("--time-limit", type=int, default=60)
    args = ap.parse_args()

    hdr = f"{'instance':16} {'mode':14} {'Y2/Y1':>7} {'Y3/Y2':>7} {'VAN':>16} {'theta*':>8}"
    print(hdr)
    print("-" * len(hdr))
    for name, (y1, y2, _y3) in MOTOR_RAMP.items():
        target = y2 / y1
        base = load(args.yaml_dir, name, args.time_limit)
        a = solve(copy.deepcopy(base))
        cal = calibrate(base, target)
        theta, b = cal if cal else (None, None)
        print(f"{name:16} {'Motor target':14} {target:7.2f} {'':>7} {'':>16} {'':>8}")
        if a:
            print(f"{name:16} {'3x ceiling':14} {a['r21']:7.2f} {a['r32']:7.2f} {a['van']:16,.0f}")
        if b:
            flag = " (bound!)" if theta and theta > 299 else ""
            print(f"{name:16} {'convex theta*':14} {b['r21']:7.2f} {b['r32']:7.2f} "
                  f"{b['van']:16,.0f} {theta:8.2f}{flag}")
        print("-" * len(hdr))


if __name__ == "__main__":
    main()

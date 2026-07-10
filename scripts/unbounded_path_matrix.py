"""Controlled experiments: find the exact unbounded path (goal audit).

Run FROM the growth-law-adr14 worktree. No core changes — pure config variants
+ post-build var bounding for path confirmation.
"""
from __future__ import annotations

import copy
import pulp

from adventure_capital.config import load_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import build_model, solve_model

COMMIT = {"enabled": True, "source": "vc_minimum", "multiple_3y": 3.0, "checkpoints": "annual"}
HIRE = {"enabled": True, "max_new_sellers_per_month": 1, "max_new_leaders_per_month": 1}


def destination(cfg: dict, hire: bool = True) -> dict:
    c = copy.deepcopy(cfg)
    c["acquisition_ceiling"] = {"enabled": False}
    c.pop("convex_cac", None)
    c["growth_commitment"] = copy.deepcopy(COMMIT)
    if hire:
        c["hiring"] = copy.deepcopy(HIRE)
    return c


def solve(cfg: dict, bound_var: str | None = None, bigm: float = 1e6) -> dict:
    inst = generate_instance(copy.deepcopy(cfg))
    bundle = build_model(inst)
    if bound_var:
        problem = bundle["problem"]
        for key, var in bundle["variables"][bound_var].items():
            problem += var <= bigm
    solved = solve_model(bundle, time_limit=120)
    out = {"status": solved["status"], "objective": solved.get("objective")}
    if solved["status"] == "Optimal":
        for name in ("A_sf", "A_ad", "A_tp"):
            vars_ = bundle["variables"].get(name) or {}
            total = sum(pulp.value(v) or 0.0 for v in vars_.values())
            out[name] = round(total, 1)
        i_ad = bundle["variables"].get("I_ad") or {}
        out["I_ad_total"] = round(sum(pulp.value(v) or 0.0 for v in i_ad.values()), 0)
        v = bundle["variables"]["V"]
        out["V_36"] = pulp.value(v[max(v)]) if v else 0
    return out


def channels_only(cfg: dict, active: str) -> dict:
    c = copy.deepcopy(cfg)
    ch = c["channels"]
    for name in ("salesforce", "advertising", "third_party"):
        ch[name]["active"] = name == active
        if ch[name]["active"]:
            ch[name]["max_share"] = 1.0
            ch[name]["min_share"] = 0.0
    return c


def main() -> None:
    base = load_config("configs/base.yaml")
    godemos = load_config("benchmark_v0/godemos.yaml")
    mixed = load_config("configs/demo-mixed-channels.yaml")

    rows: list[tuple[str, dict]] = []

    # A. reported case + per-instance destination mode
    rows.append(("godemos dest (sf-only impl.)", solve(destination(godemos))))
    rows.append(("base dest (sf-only)", solve(destination(base))))
    rows.append(("mixed dest ALL channels", solve(destination(mixed))))

    # B. channel isolation on mixed
    for chan in ("salesforce", "advertising", "third_party"):
        rows.append((f"mixed dest {chan}-only", solve(destination(channels_only(mixed, chan)))))

    # C. third-party without commission
    tp0 = channels_only(mixed, "third_party")
    tp0["channels"]["third_party"]["commission"] = 0.0
    rows.append(("mixed dest tp-only com=0", solve(destination(tp0))))

    # D. cash floor active (base, minimum_cash 0)
    cash = destination(base)
    cash["liquidity_policy"] = {"type": "minimum_cash", "value": 0.0}
    rows.append(("base dest + cash>=0", solve(cash)))

    # E. path confirmation: if mixed-all unbounded, bound A_tp / I_ad / A_ad
    mixed_dest = destination(mixed)
    for bv in ("A_tp", "A_ad", "A_sf"):
        rows.append((f"mixed dest ALL, bound {bv}<=1e6", solve(mixed_dest, bound_var=bv)))

    print(f"{'experimento':38s} {'status':10s} {'objetivo':>14s}  detalles")
    for name, r in rows:
        obj = f"{r['objective']:,.0f}" if r.get("objective") is not None else "—"
        det = {k: v for k, v in r.items() if k not in ("status", "objective")}
        print(f"{name:38s} {r['status']:10s} {obj:>14s}  {det}")

    # F. destination-mode benchmarks (all 4, h in {1,2})
    print("\n=== BENCHMARKS MODO DESTINO (ceiling off + piso + friccion) ===")
    for inst_name in ("godemos", "entrena-en-casa", "beloop", "kavacomex"):
        cfg = load_config(f"benchmark_v0/{inst_name}.yaml")
        for h in (1, 2):
            c = destination(cfg)
            c["hiring"]["max_new_sellers_per_month"] = h
            c["hiring"]["max_new_leaders_per_month"] = h
            r = solve(c)
            obj = f"{r['objective']:,.0f}" if r.get("objective") is not None else "—"
            det = {k: v for k, v in r.items() if k not in ("status", "objective")}
            print(f"{inst_name:16s} h={h}  {r['status']:10s} {obj:>14s}  {det}")


if __name__ == "__main__":
    main()

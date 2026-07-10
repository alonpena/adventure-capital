"""Growth-band experiment: minimum VC benchmark + slack variants (goal task B).

Formulation injected post-build (no core changes):

    stock_t  = sum_s C[s,t]
    stock_t >= B_t                      (minimum growth commitment)
    stock_t <= B_t * (1 + slack_t)      (upper band, variant-dependent)

with B_t = C12_ref * (1+g)^((t-12)/12-steps), i.e. a geometric client-stock
benchmark anchored on the consensuated year-1 stock. Two sourced growth rates:

  - g_vc   = 2.0x/year — the Motor godemos realized ambition (traceable source,
             ADR 0013) and the VC "duplicar cartera cada 12 meses" heuristic
             (Maureira meeting 2026-07-01).
  - g_mom  = derived from the consensuated plan's own A_base MoM growth
             (geometric mean of month-over-month acquisition growth, months 1-12).

Variants:
  band-fixed     g_vc, slack 15% flat                 (assumption, conservative)
  band-grow      g_vc, slack 10% year2 / 30% year3    (assumption, widening)
  band-mom       g_mom, slack 15%                     (slack anchored to the plan's own MoM)
  band-min-only  g_vc, NO upper band                  (expected Unbounded -> proves upper bound or friction needed)
  band-min-hire  g_vc, NO upper band + V_t <= V_{t-1}+1, L_t <= L_{t-1}+1
                                                      (friction bounds instead of band ceiling)

Reference row: current log ceiling x8 (from threshold grid, for contrast only).

Usage: uv run python scripts/growth_band_experiment.py [--config configs/base.yaml]
"""

from __future__ import annotations

import argparse
import copy
import csv
import math
from pathlib import Path

import pulp

from adventure_capital.config import load_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import build_model, solve_model
from adventure_capital.results import extract_results
from adventure_capital.valuation import calculate_dcf


def _free_config(seed: dict) -> dict:
    cfg = copy.deepcopy(seed)
    cfg["acquisition_ceiling"] = {"enabled": False}
    cfg.pop("convex_cac", None)
    return cfg


def _mom_growth(a_base: list[float]) -> float:
    """Geometric-mean MoM growth of the consensuated acquisition plan."""
    first, last = float(a_base[0]), float(a_base[-1])
    months = len(a_base) - 1
    if first <= 0 or months <= 0:
        return 0.0
    return (last / first) ** (1.0 / months) - 1.0


def _reference_stock_m12(config: dict) -> float:
    """Solve the year-1-only dynamics implied stock at month 12.

    Year-1 acquisition is exogenous, so C12 is identical across variants; we
    read it from a quick ceiling-bounded solve."""
    cfg = copy.deepcopy(config)
    cfg["acquisition_ceiling"] = {"enabled": True, "target_stock_multiplier": 3.0, "slack": 0.15}
    inst = generate_instance(cfg)
    bundle = build_model(inst)
    solved = solve_model(bundle, time_limit=120)
    if solved["status"] != "Optimal":
        raise RuntimeError(f"reference solve not optimal: {solved['status']}")
    c_vars = bundle["variables"]["C"]
    services = range(inst["S"])
    return sum(float(pulp.value(c_vars[(s, 12)]) or 0.0) for s in services)


def run_variant(
    seed: dict,
    name: str,
    *,
    growth_annual: float,
    slack_fn,
    upper_band: bool,
    hiring_friction: bool,
    c12: float,
) -> dict:
    cfg = _free_config(seed)
    inst = generate_instance(cfg)
    bundle = build_model(inst)
    problem = bundle["problem"]
    c_vars = bundle["variables"]["C"]
    v_vars = bundle["variables"]["V"]
    l_vars = bundle["variables"]["L"]
    horizon = inst["H"]
    services = range(inst["S"])

    monthly_growth = (1.0 + growth_annual) ** (1.0 / 12.0) - 1.0
    for t in range(13, horizon + 1):
        benchmark = c12 * (1.0 + monthly_growth) ** (t - 12)
        stock_t = pulp.lpSum(c_vars[(s, t)] for s in services)
        problem += stock_t >= benchmark
        if upper_band:
            problem += stock_t <= benchmark * (1.0 + slack_fn(t))
        if hiring_friction:
            problem += v_vars[t] <= v_vars[t - 1] + 1
            problem += l_vars[t] <= l_vars[t - 1] + 1

    solved = solve_model(bundle, time_limit=240)
    row = {"variant": name, "status": solved["status"], "growth_annual": growth_annual}
    if solved["status"] != "Optimal":
        return row

    df = extract_results(inst, solved)
    dcf = calculate_dcf(df, inst)
    by_year = df.groupby("Año")["Ingresos"].sum()
    stock = df.groupby("t")["Clientes_activos"].sum() if "Clientes_activos" in df else None
    v = df.groupby("t")["Vendedores"].first()
    row.update(
        {
            "van": float(dcf["VAN"]),
            "rev_y3": float(by_year.iloc[2]) if len(by_year) >= 3 else None,
            "min_cash": float(df["Caja"].min()),
            "stock_m12": float(stock.loc[12]) if stock is not None else None,
            "stock_m24": float(stock.loc[24]) if stock is not None else None,
            "stock_m36": float(stock.loc[36]) if stock is not None else None,
            "V_m13": float(v.loc[13]),
            "V_m24": float(v.loc[24]),
            "V_m36": float(v.loc[36]),
        }
    )
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--output", default="docs/analysis")
    args = parser.parse_args()

    seed = load_config(args.config)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    a_base = seed["servicios"][0]["A_base"]
    g_mom_monthly = _mom_growth(a_base)
    g_mom_annual = (1.0 + g_mom_monthly) ** 12 - 1.0
    c12 = _reference_stock_m12(seed)
    print(f"C12 (stock consensuado) = {c12:.1f} · MoM plan = {g_mom_monthly:.1%}/mes "
          f"(~{g_mom_annual:.1f}x-1 anual)")

    slack_fixed = lambda t: 0.15
    slack_grow = lambda t: 0.10 if t <= 24 else 0.30

    variants = [
        ("band-fixed", dict(growth_annual=1.0, slack_fn=slack_fixed, upper_band=True, hiring_friction=False)),
        ("band-grow", dict(growth_annual=1.0, slack_fn=slack_grow, upper_band=True, hiring_friction=False)),
        ("band-mom", dict(growth_annual=g_mom_annual, slack_fn=slack_fixed, upper_band=True, hiring_friction=False)),
        ("band-min-only", dict(growth_annual=1.0, slack_fn=slack_fixed, upper_band=False, hiring_friction=False)),
        ("band-min-hire", dict(growth_annual=1.0, slack_fn=slack_fixed, upper_band=False, hiring_friction=True)),
    ]

    rows = []
    for name, kwargs in variants:
        try:
            row = run_variant(seed, name, c12=c12, **kwargs)
        except Exception as exc:
            row = {"variant": name, "status": f"ERROR {type(exc).__name__}: {exc}"}
        rows.append(row)
        print(f"{name}: {row.get('status')} van={row.get('van')}")

    fieldnames = sorted({k for r in rows for k in r})
    with open(out_dir / "growth_band_experiment.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md = [
        "# Experimento: banda de crecimiento mínimo + holgura",
        "",
        f"Seed `{args.config}` · C12 consensuado = {c12:.1f} clientes · "
        f"MoM del plan año 1 = {g_mom_monthly:.1%}/mes · `scripts/growth_band_experiment.py`",
        "",
        "Banda: `stock_t >= B_t` y (si aplica) `stock_t <= B_t·(1+slack_t)`, "
        "con `B_t = C12·(1+g_m)^(t-12)`.",
        "",
        "| variante | g anual | status | VAN | Ing Y3 | stock m24/m36 | V m13→24→36 | min caja |",
        "|---|---:|---|---:|---:|---|---|---:|",
    ]
    for r in rows:
        if r.get("van") is None:
            md.append(f"| {r['variant']} | {r.get('growth_annual','—')} | **{r['status']}** | | | | | |")
        else:
            md.append(
                f"| {r['variant']} | {r['growth_annual']:.2f} | {r['status']} | {r['van']:,.0f} | "
                f"{r['rev_y3']:,.0f} | {r['stock_m24']:.0f}/{r['stock_m36']:.0f} | "
                f"{r['V_m13']:.0f}→{r['V_m24']:.0f}→{r['V_m36']:.0f} | {r['min_cash']:,.0f} |"
            )
    (out_dir / "growth_band_experiment.md").write_text("\n".join(md) + "\n")
    print(f"wrote {out_dir}/growth_band_experiment.{{csv,md}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

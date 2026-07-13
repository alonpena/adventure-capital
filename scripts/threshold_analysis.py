"""Model-class threshold analysis (not instance calibration).

Answers three structural questions about the deterministic model, for ANY seed
config (default configs/base.yaml):

E1. What bounds growth when no external brake exists?
    Disable the log ceiling and convex CAC and report the solver status. If the
    LP relaxation is unbounded (or the plan explodes), the model *requires* an
    external brake — growth is not endogenous to the business model.

E2. Threshold frontier over (VC, target_stock_multiplier):
    For each grid point report VAN, year-3 revenue, the VAN / year-3-revenue
    ratio (business benchmark: >= 1.0), breakeven month, and the salesforce
    trajectory (V at months 12 / 13 / 36) to quantify the jump-then-flat
    hiring dynamic.

E3. Analytic feasibility threshold:
    VC* = 12 * (g_adm + RRHH[year1]) minus year-1 gross margin — the committed
    fixed cost the financing ticket must cover. Reported alongside the grid so
    the reader sees WHY low-VC cells fail without re-running anything.

E4. Hiring friction as an endogenous brake:
    Same no-brake model as E1 plus one business constraint per month >= 13:
    V[t] <= V[t-1] + h (and L[t] <= L[t-1] + 1). If this alone turns Unbounded
    into Optimal, the growth law can be a business-model parameter (monthly
    hiring/training capacity) instead of an exogenous market multiplier.

Usage:
    uv run python scripts/threshold_analysis.py [--config configs/base.yaml]
        [--vc 50000,100000] [--multipliers 3,5,8,12] [--output docs/analysis]
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path


from adventure_capital.config import load_config
from adventure_capital.pipeline import run_pipeline


def _load(config_path: str) -> dict:
    return load_config(config_path)


def _annual_revenue(output_dir: Path) -> list[float]:
    rows = list(csv.DictReader(open(output_dir / "dcf_annual_summary.csv")))
    return [float(r["Ingresos"]) for r in rows]


def _sellers_profile(output_dir: Path) -> tuple[float, float, float]:
    import pandas as pd

    df = pd.read_csv(output_dir / "optimized_results.csv")
    v = df["Vendedores"]
    return float(v.iloc[11]), float(v.iloc[12]), float(v.iloc[-1])


def _cash_metrics(output_dir: Path) -> dict:
    """Capital-requirement view: max drawdown (dinero), its month (tiempo),
    and cumulative-EBITDA breakeven (independent of VC)."""
    import pandas as pd

    df = pd.read_csv(output_dir / "optimized_results.csv")
    cash = df["Caja"].astype(float)
    cum_ebitda = df["EBITDA"].astype(float).cumsum()
    positive = df.index[cum_ebitda >= 0].tolist()
    return {
        "min_cash": float(cash.min()),
        "min_cash_month": int(df.loc[cash.idxmin(), "t"]),
        "breakeven_month": int(df.loc[positive[0], "t"]) if positive else None,
    }


def run_case(config: dict, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    run_pipeline(copy.deepcopy(config), output_dir=str(out), baseline_only=True)
    summary = json.load(open(out / "summary.json"))
    revenue = _annual_revenue(out)
    v12, v13, v36 = _sellers_profile(out)
    return {
        "van": summary["van"],
        "rev_y1": revenue[0],
        "rev_y2": revenue[1],
        "rev_y3": revenue[2],
        "van_over_rev_y3": summary["van"] / revenue[2] if revenue[2] else float("nan"),
        **_cash_metrics(out),
        "V_m12": v12,
        "V_m13": v13,
        "V_m36": v36,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--vc", default="50000,100000")
    parser.add_argument("--multipliers", default="3,5,8,12")
    parser.add_argument("--output", default="docs/analysis")
    parser.add_argument("--workdir", default="/tmp/threshold-analysis")
    args = parser.parse_args()

    seed = _load(args.config)
    vcs = [float(x) for x in args.vc.split(",")]
    mults = [float(x) for x in args.multipliers.split(",")]
    workdir = Path(args.workdir)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- E3: analytic feasibility threshold -------------------------------
    rrhh_y1 = seed["RRHH_mensual"][0]
    committed_fixed_y1 = 12 * (seed["g_adm"] + rrhh_y1)

    # ---- E1: no external brake --------------------------------------------
    # Solve the raw MILP directly (not through the pipeline) so we can read the
    # true solver status instead of downstream consistency-check noise.
    from adventure_capital.instance import generate_instance
    from adventure_capital.model import build_model, solve_model

    free = copy.deepcopy(seed)
    free["acquisition_ceiling"] = {"enabled": False}
    free.pop("convex_cac", None)
    e1_metrics: dict | None = None
    try:
        bundle = build_model(generate_instance(free))
        solved = solve_model(bundle, time_limit=120)
        e1_status = f"solver status = {solved['status']}"
        if solved["status"] == "Optimal":
            e1_metrics = {"van": float(solved.get("objective") or 0.0)}
    except Exception as exc:
        e1_status = f"NOT SOLVED: {type(exc).__name__}: {exc}"

    # ---- E4: hiring friction as endogenous brake ---------------------------
    import pulp

    e4_rows: list[dict] = []
    for h in (1, 2):
        try:
            bundle = build_model(generate_instance(copy.deepcopy(free)))
            prob = bundle["problem"]
            sellers_vars = bundle["variables"]["V"]
            leaders_vars = bundle["variables"]["L"]
            for t in sorted(sellers_vars):
                if t >= 13:
                    prob += sellers_vars[t] <= sellers_vars[t - 1] + h
                    prob += leaders_vars[t] <= leaders_vars[t - 1] + 1
            solved = solve_model(bundle, time_limit=180)
            v_vals = {t: pulp.value(sellers_vars[t]) or 0.0 for t in sorted(sellers_vars)}
            e4_rows.append({
                "h": h,
                "status": solved["status"],
                "objective": float(solved.get("objective") or 0.0),
                "V_m13": v_vals.get(13, 0.0),
                "V_m24": v_vals.get(24, 0.0),
                "V_m36": v_vals.get(36, 0.0),
            })
        except Exception as exc:
            e4_rows.append({"h": h, "status": f"ERROR {exc}", "objective": None})

    # ---- E2: grid -----------------------------------------------------------
    rows: list[dict] = []
    for vc in vcs:
        for m in mults:
            cfg = copy.deepcopy(seed)
            cfg["VC"] = vc
            cfg["acquisition_ceiling"] = {
                "enabled": True,
                "target_stock_multiplier": m,
                "slack": 0.15,
            }
            label = f"vc{int(vc/1000)}k-m{m:g}"
            try:
                metrics = run_case(cfg, workdir / label)
                rows.append({"case": label, "VC": vc, "M": m, **metrics})
            except Exception as exc:
                rows.append({"case": label, "VC": vc, "M": m, "van": None,
                             "error": f"{type(exc).__name__}: {exc}"})
            print(f"done {label}: {rows[-1].get('van')}")

    # ---- artifacts ----------------------------------------------------------
    csv_path = out_dir / "threshold_grid.csv"
    fieldnames = sorted({k for r in rows for k in r})
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md = [
        "# Análisis de umbrales del modelo determinista",
        "",
        f"Seed config: `{args.config}` · generado por `scripts/threshold_analysis.py`",
        "",
        "## E3 — Umbral analítico de factibilidad",
        "",
        f"Costo fijo comprometido año 1 = 12·(g_adm + RRHH_1) = **{committed_fixed_y1:,.0f}**.",
        "Todo VC bajo ese número depende del margen bruto del año 1 para no romper el piso de caja −VC.",
        "",
        "## E1 — ¿Qué acota el crecimiento sin freno externo?",
        "",
        f"Ceiling y convex-CAC desactivados → **{e1_status}**",
    ]
    if e1_metrics:
        md += ["", f"Objetivo del solver (no acotado por freno externo): {e1_metrics['van']:,.0f}"]
    md += [
        "",
        "## E4 — Fricción de contratación como freno endógeno",
        "",
        "Mismo modelo sin freno + `V_t <= V_{t-1} + h`, `L_t <= L_{t-1} + 1` (t ≥ 13):",
        "",
        "| h (vendedores/mes) | status | objetivo | V m13 / m24 / m36 |",
        "|---:|---|---:|---|",
    ]
    for r in e4_rows:
        if r.get("objective") is None:
            md.append(f"| {r['h']} | {r['status']} | | |")
        else:
            md.append(
                f"| {r['h']} | {r['status']} | {r['objective']:,.0f} | "
                f"{r['V_m13']:.0f} / {r['V_m24']:.0f} / {r['V_m36']:.0f} |"
            )
    md += [
        "",
        "## E2 — Frontera (VC × M)",
        "",
        "min caja = capital realmente requerido (dinero); su mes = tiempo; breakeven = EBITDA acumulado ≥ 0.",
        "",
        "| caso | VAN | Ing Y3 | VAN/IngY3 | min caja (mes) | breakeven | V m12→13→36 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        if r.get("van") is None:
            md.append(f"| {r['case']} | ERROR | | | | | {r.get('error','')} |")
            continue
        md.append(
            f"| {r['case']} | {r['van']:,.0f} | {r['rev_y3']:,.0f} | "
            f"{r['van_over_rev_y3']:.2f} | {r['min_cash']:,.0f} (m{r['min_cash_month']}) | "
            f"{r['breakeven_month'] or '—'} | "
            f"{r['V_m12']:.0f}→{r['V_m13']:.0f}→{r['V_m36']:.0f} |"
        )
    (out_dir / "threshold_analysis.md").write_text("\n".join(md) + "\n")
    print(f"\nwrote {csv_path} and {out_dir / 'threshold_analysis.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

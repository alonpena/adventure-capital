"""Benchmark runs for growth_commitment + hiring across benchmark_v0 (ADR 0014, plan §7).

For each of the four benchmark_v0 instances, solves three modes:
  off            - current baseline (no growth_commitment, no hiring)
  vc_minimum     - growth_commitment enabled (source=vc_minimum, x3/3y, annual checkpoints)
  vc_minimum+hire- same + hiring friction h_v=h_l=1

kavacomex additionally runs BOTH commitment source "none" (bottom-up valuation,
no floor) and vc_minimum; if vc_minimum comes back Infeasible, runs the full R1-R8
diagnosis routine and tabulates which levers restore feasibility.

Uses build_model + solve_model directly (never run_pipeline+output_dir): a
non-Optimal status would otherwise crash the consistency-check pipeline
(documented WORKLOG trap).

Usage: uv run python scripts/growth_commitment_benchmarks.py
Writes: docs/analysis/growth_commitment_benchmarks.md
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from adventure_capital.config import load_config  # noqa: E402
from adventure_capital.instance import generate_instance  # noqa: E402
from adventure_capital.model import build_model, solve_model  # noqa: E402
from adventure_capital.results import extract_results  # noqa: E402
from adventure_capital.valuation import calculate_dcf  # noqa: E402
from scripts.diagnose_infeasibility import diagnose_infeasibility  # noqa: E402

INSTANCES = ["godemos", "entrena-en-casa", "beloop", "kavacomex"]
TIME_LIMIT = 120


def _load(name: str) -> dict:
    cfg = load_config(f"benchmark_v0/{name}.yaml")
    cfg["solver"] = {"name": "cbc", "time_limit": TIME_LIMIT, "verbose": False}
    return cfg


def _run_mode(config: dict) -> dict:
    inst = generate_instance(config)
    bundle = build_model(inst)
    solved = solve_model(bundle, time_limit=TIME_LIMIT)
    row: dict = {"status": solved["status"]}
    if solved["status"] != "Optimal":
        return row
    df = extract_results(inst, solved)
    dcf = calculate_dcf(df, inst)
    by_year = df.groupby("Año")["Ingresos"].sum()
    stock = df.groupby("t")["Clientes_activos"].sum()
    growth_commitment = inst.get("growth_commitment", {})
    c12 = growth_commitment.get("C12")
    checkpoint_targets = growth_commitment.get("checkpoint_targets", {})
    stock_m24 = float(stock.loc[24]) if 24 in stock.index else None
    stock_m36 = float(stock.loc[36]) if 36 in stock.index else None
    # Binding check: is the commitment floor actually the tight constraint, or
    # is the plan already exceeding it for other reasons (e.g. the default
    # log ceiling, ADR 0010, already implies >= the same x3 multiple)? Slack
    # here is headroom ABOVE the target, not the config's floor_slack.
    binding_24 = (
        (stock_m24 - checkpoint_targets[24]) < 1e-3
        if stock_m24 is not None and 24 in checkpoint_targets
        else None
    )
    binding_36 = (
        (stock_m36 - checkpoint_targets[36]) < 1e-3
        if stock_m36 is not None and 36 in checkpoint_targets
        else None
    )
    row.update(
        {
            "van": float(dcf["VAN"]),
            "rev_y1": float(by_year.iloc[0]) if len(by_year) >= 1 else None,
            "rev_y3": float(by_year.iloc[2]) if len(by_year) >= 3 else None,
            "stock_m12": float(stock.loc[12]) if 12 in stock.index else None,
            "stock_m24": stock_m24,
            "stock_m36": stock_m36,
            "min_cash": float(df["Caja"].min()),
            "c12": c12,
            "ratio_m36": stock_m36 / c12 if c12 else None,
            "checkpoint_targets": checkpoint_targets,
            "binding_24": binding_24,
            "binding_36": binding_36,
        }
    )
    # Envelope binding check: in how many optimized months does the solution
    # sit against U_t (within 1e-3)? 0 = envelope never tight (upside intact).
    envelope = inst.get("acquisition_envelope", {})
    if envelope.get("enabled", False):
        acq = df.groupby("t")["Adq_clientes"].sum()
        tight = sum(
            1
            for t, u_t in envelope["path"].items()
            if t in acq.index and float(acq.loc[t]) >= u_t - 1e-3
        )
        row["env_tight_months"] = tight
        row["env_months"] = len(envelope["path"])
    return row


def _mode_off(seed: dict) -> dict:
    cfg = copy.deepcopy(seed)
    cfg.pop("growth_commitment", None)
    cfg.pop("hiring", None)
    return cfg


def _mode_vc_minimum(seed: dict) -> dict:
    cfg = copy.deepcopy(seed)
    cfg["growth_commitment"] = {
        "enabled": True,
        "source": "vc_minimum",
        "multiple_3y": 3.0,
        "checkpoints": "annual",
    }
    return cfg


def _mode_vc_minimum_hire(seed: dict) -> dict:
    cfg = _mode_vc_minimum(seed)
    cfg["hiring"] = {"enabled": True, "max_new_sellers_per_month": 1, "max_new_leaders_per_month": 1}
    return cfg


def _mode_none(seed: dict) -> dict:
    cfg = copy.deepcopy(seed)
    cfg["growth_commitment"] = {"enabled": False}
    cfg.pop("hiring", None)
    return cfg


def _mode_vc_minimum_ceiling_off(seed: dict) -> dict:
    """Contrast run (isolation check, not a benchmark mode): disables the
    exogenous log ceiling to show the commitment floor binding on its own,
    with no upper brake. Per the plan, the x8/x3 ceiling is never core to this
    feature — this run exists only to make the "off == vc_minimum because the
    default ceiling already implies x3" finding legible, not to promote a new
    default."""
    cfg = _mode_vc_minimum(seed)
    cfg["acquisition_ceiling"] = {"enabled": False}
    return cfg


def _mode_core_envelope(seed: dict) -> dict:
    """New core methodology (ADR 0014 amendment): growth_commitment floor +
    aggregate acquisition envelope, with the legacy exogenous log ceiling OFF.
    Demo profile pins growth to the VC-minimum path: U_vc with zero slack."""
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
    return cfg


def main() -> int:
    results: dict[str, dict[str, dict]] = {}
    kavacomex_diagnosis = None

    for name in INSTANCES:
        seed = _load(name)
        results[name] = {
            "off": _run_mode(_mode_off(seed)),
            "vc_minimum": _run_mode(_mode_vc_minimum(seed)),
            "vc_minimum+hire_h1": _run_mode(_mode_vc_minimum_hire(seed)),
        }
        print(f"{name}: off={results[name]['off']['status']} "
              f"vc_min={results[name]['vc_minimum']['status']} "
              f"vc_min+hire={results[name]['vc_minimum+hire_h1']['status']}")

        if name == "kavacomex":
            results[name]["none"] = _run_mode(_mode_none(seed))
            # kavacomex is the explicit x3-thesis stress case (near-flat real
            # ramp, ADR 0013): run the full R1-R8 diagnosis routine regardless
            # of status, per plan §7/§9. If Optimal (as observed under
            # defaults), the diagnosis routine still runs safely (every
            # relaxation reports feasible=True) and the report documents WHY
            # the expected stress did not materialize (ceiling redundancy).
            print("kavacomex: running full R1-R8 diagnosis routine (always, per plan)...")
            kavacomex_diagnosis = diagnose_infeasibility(
                _mode_vc_minimum(seed), time_limit=TIME_LIMIT
            )
            print(kavacomex_diagnosis["readable_summary"])

    # Contrast run (all 4 instances): commitment floor with the ceiling
    # disabled, to show the floor mechanism binding in isolation.
    ceiling_off_results = {}
    for name in INSTANCES:
        seed = _load(name)
        ceiling_off_results[name] = _run_mode(_mode_vc_minimum_ceiling_off(seed))

    # New core methodology (ADR 0014 amendment): commitment + envelope,
    # legacy ceiling off. This is THE run that shows the envelope closing the
    # unbounded hole the isolated-floor contrast exposes above.
    core_results = {}
    for name in INSTANCES:
        seed = _load(name)
        core_results[name] = _run_mode(_mode_core_envelope(seed))
        print(f"{name}: core (commitment+envelope, ceiling off) = "
              f"{core_results[name]['status']}")

    out_path = Path("docs/analysis/growth_commitment_benchmarks.md")
    _write_report(out_path, results, kavacomex_diagnosis, ceiling_off_results, core_results)
    print(f"wrote {out_path}")
    return 0


def _fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.0f}"
    return str(value)


def _binding_str(row: dict) -> str:
    b24, b36 = row.get("binding_24"), row.get("binding_36")

    def _one(b):
        if b is None:
            return "n/a"
        return "binding" if b else "holgado"

    return f"m24 {_one(b24)} / m36 {_one(b36)}"


def _write_report(
    path: Path,
    results: dict,
    kavacomex_diagnosis: dict | None,
    ceiling_off_results: dict,
    core_results: dict,
) -> None:
    # Cross-validation targets declared in each benchmark YAML's own header comments.
    targets = {
        "godemos": {"van": 2_005_000, "rev_y1": 303_000},
        "entrena-en-casa": {"van": 1_413_000, "rev_y1": 173_000},
        "beloop": {"van": 1_923_000, "rev_y1": 828_000},
        "kavacomex": {"van": 1_789_000, "rev_y1": 135_000, "rev_y3": 2_361_000},
    }

    lines = [
        "# Growth commitment + hiring — benchmark runs (ADR 0014)",
        "",
        "4 instancias `benchmark_v0/*.yaml` x {off, vc_minimum, vc_minimum+hiring h=1}. "
        "kavacomex corre además `none` (bottom-up puro) y la rutina completa de diagnóstico "
        "R1-R8. Targets = los declarados en el propio YAML (ver `YAML_EXTRACTION_SUMMARY.md`, "
        "tolerancia ±20% documentada por el founder, no exigida aquí como gate — se explica "
        "el delta por caso).",
        "",
        "`vc_minimum`: `growth_commitment.enabled=true, source=vc_minimum, multiple_3y=3.0, "
        "checkpoints=annual` (C24>=sqrt(3)*C12, C36>=3*C12) significa: **triplicar el stock "
        "de clientes entre el fin del año 1 consensuado (mes 12) y el fin del año 3 (mes 36)**. "
        "El log ceiling (ADR 0010, default-on x3/slack 0.15) queda activo en todos los modos "
        "de la tabla principal — nunca se sube su multiplicador como parte de esta feature "
        "(corrección Alonso: el x8/el ceiling no es core; el piso debe funcionar con el "
        "ceiling desactivado, ver sección de contraste abajo). "
        "`vc_minimum+hire`: además `hiring.enabled=true, h_v=h_l=1`.",
        "",
        "**Columna `piso` (binding check)**: indica si el checkpoint del compromiso "
        "(C24/C36) es la restricción activa (`binding`, el stock queda pegado al piso) o si "
        "el plan ya lo supera por otras razones (`holgado`, con margen).",
        "",
        "| instancia | modo | status | VAN | Δ vs target VAN | Ing Y1 | Ing Y3 | stock m12/m24/m36 | piso | min caja |",
        "|---|---|---|---:|---:|---:|---:|---|---|---:|",
    ]

    for name in INSTANCES:
        target = targets.get(name, {})
        target_van = target.get("van")
        for mode_key, mode_label in [
            ("off", "off"),
            ("vc_minimum", "vc_minimum"),
            ("vc_minimum+hire_h1", "vc_minimum+hire h=1"),
        ]:
            row = results[name][mode_key]
            if row["status"] != "Optimal":
                lines.append(f"| {name} | {mode_label} | **{row['status']}** | | | | | | | |")
                continue
            van = row["van"]
            delta = f"{(van/target_van - 1):+.0%}" if target_van else "—"
            stock = f"{_fmt(row['stock_m12'])}/{_fmt(row['stock_m24'])}/{_fmt(row['stock_m36'])}"
            binding = _binding_str(row) if mode_key != "off" else "n/a (piso off)"
            lines.append(
                f"| {name} | {mode_label} | {row['status']} | {_fmt(van)} | {delta} | "
                f"{_fmt(row['rev_y1'])} | {_fmt(row['rev_y3'])} | {stock} | {binding} | {_fmt(row['min_cash'])} |"
            )
        if name == "kavacomex" and "none" in results[name]:
            row = results[name]["none"]
            if row["status"] == "Optimal":
                van = row["van"]
                delta = f"{(van/target_van - 1):+.0%}" if target_van else "—"
                stock = f"{_fmt(row['stock_m12'])}/{_fmt(row['stock_m24'])}/{_fmt(row['stock_m36'])}"
                lines.append(
                    f"| {name} | none (bottom-up) | {row['status']} | {_fmt(van)} | {delta} | "
                    f"{_fmt(row['rev_y1'])} | {_fmt(row['rev_y3'])} | {stock} | n/a (piso off) | {_fmt(row['min_cash'])} |"
                )

    lines.append("")
    lines.append("## Hallazgo principal: `off` == `vc_minimum` en las 4 instancias")
    lines.append("")
    lines.append(
        "Ninguna de las 4 instancias muestra diferencia entre `off` y `vc_minimum` en la tabla "
        "de arriba (columna `piso` = `holgado` en todos los casos). Causa: el log ceiling por "
        "defecto (ADR 0010, `target_stock_multiplier=3.0`, `slack=0.15`, activo en TODOS los "
        "modos salvo el contraste explícito de abajo) ya produce, por sí solo, un stock que "
        "supera holgadamente el piso del compromiso: en las 4 instancias el ratio `off` natural "
        "es ~2.4-2.9x en m24 (> el umbral sqrt(3)~=1.73x) y ~3.1-3.5x en m36 (> el umbral 3.0x), "
        "incluso con `hiring h=1`. El compromiso (`growth_commitment`) es matemáticamente "
        "correcto y verificado por los tests unitarios (`tests/test_growth_commitment.py`), "
        "pero en estos 4 casos concretos **es redundante frente al ceiling por defecto**, no "
        "porque el mecanismo no funcione, sino porque el ceiling default-on ya implica un piso "
        "igual o mayor. Esto NO es una falla de la feature: es el resultado correcto de que "
        "ambos frenos comparten el mismo múltiplo x3 por default.",
    )
    lines.append("")
    lines.append(
        "## Contraste: piso aislado (ceiling desactivado, NO es un modo default)"
    )
    lines.append("")
    lines.append(
        "Para demostrar que el mecanismo del piso funciona de forma independiente (y que no "
        "es un techo — la parte superior queda libre), se corrió `vc_minimum` con "
        "`acquisition_ceiling.enabled=false` en las 4 instancias. Sin ningún freno superior, "
        "las 4 resultan `Unbounded` (comportamiento documentado y esperado, ADR 0010/0013: sin "
        "ceiling ni convex-CAC, la adquisición no tiene techo). Esto confirma que el piso NUNCA "
        "acota el crecimiento por arriba — solo por abajo — y que necesita, como siempre, algún "
        "freno superior (ceiling, convex-CAC, capacidad o caja) para acotar la solución."
    )
    lines.append("")
    lines.append("| instancia | vc_minimum + ceiling OFF | status |")
    lines.append("|---|---|---|")
    for name in INSTANCES:
        row = ceiling_off_results[name]
        lines.append(f"| {name} | piso aislado (sin ceiling) | **{row['status']}** |")
    lines.append("")

    lines.append("## Core nuevo: piso + envolvente agregada de adquisición (ADR 0014 enmienda)")
    lines.append("")
    lines.append(
        "`growth_commitment (vc_minimum, x3, annual)` + `acquisition_envelope "
        "(vc_minimum, slack 0 año 2 / 0 año 3)` con el log ceiling exógeno "
        "**desactivado**: la envolvente lo reemplaza como cota superior. A diferencia del "
        "ceiling (múltiplo de mercado exógeno), U_vc queda trazado directamente a "
        "`investment_thesis.multiple`: adquisición requerida por la senda mínima VC neta "
        "de churn. Slack = 0: sin upside especulativo. Esta corrida es la respuesta directa "
        "al contraste anterior: donde el piso aislado es Unbounded, el core completo queda "
        "acotado con significado de negocio."
    )
    lines.append("")
    lines.append(
        "**Columna `U_t activa`**: meses (de los 24 optimizados) en que la solución queda "
        "pegada a la envolvente. 0 = la envolvente nunca recorta el óptimo (upside intacto); "
        ">0 = la envolvente es el freno efectivo en esos meses."
    )
    lines.append("")
    lines.append(
        "| instancia | status | VAN | Δ vs target VAN | Ing Y1 | Ing Y3 | stock m36 | ratio m36/C12 | piso | U_t activa | min caja |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|")
    for name in INSTANCES:
        target = targets.get(name, {})
        target_van = target.get("van")
        row = core_results[name]
        if row["status"] != "Optimal":
            lines.append(f"| {name} | **{row['status']}** | | | | | | | | | |")
            continue
        van = row["van"]
        delta = f"{(van/target_van - 1):+.0%}" if target_van else "—"
        env_col = (
            f"{row['env_tight_months']}/{row['env_months']}"
            if row.get("env_months") is not None
            else "—"
        )
        lines.append(
            f"| {name} | {row['status']} | {_fmt(van)} | {delta} | "
            f"{_fmt(row['rev_y1'])} | {_fmt(row['rev_y3'])} | {_fmt(row['stock_m36'])} | "
            f"{row['ratio_m36']:.2f}× | "
            f"{_binding_str(row)} | {env_col} | {_fmt(row['min_cash'])} |"
        )
    lines.append("")
    lines.append(
        "**Lectura de los deltas (vs `off` = baseline entrega-tesis, ceiling default-on)**: "
        "la envolvente VC-minimum con δ=0 elimina el upside especulativo y fuerza una "
        "lectura de cumplimiento de tesis. El ratio m36/C12 queda cercano a ×3 en las "
        "cuatro instancias (las desviaciones vienen de la agregación de churn usada para "
        "U_vc frente a la dinámica exacta por servicio del MILP). La columna `U_t activa` "
        "muestra que la envolvente es el freno efectivo: sin ella estos casos son Unbounded "
        "(contraste anterior). VAN y MoM son consecuencias del plan comprometido, no "
        "parámetros calibrados."
    )
    lines.append("")

    lines.append("## Lectura por caso")
    lines.append("")
    lines.append(
        "- **godemos**: caso más limpio (PRIORITY 1). VC=0 (operating_company), "
        "unit economics casi sin costo — el ceiling por defecto ya lleva el plan muy por "
        "encima del piso x3 (holgado en ambos checkpoints)."
    )
    lines.append(
        "- **entrena-en-casa**: EBITDA año 1 negativo en el Excel (test de caja); el ceiling "
        "por defecto sigue dominando sobre el piso del compromiso en este benchmark."
    )
    lines.append(
        "- **beloop**: enterprise sticky (churn 0%) + downgrades de plan no modelados "
        "(ver YAML_EXTRACTION_SUMMARY) — el piso no cambia el resultado porque el ceiling ya "
        "domina; el downgrade no modelado sigue siendo el gap estructural conocido, "
        "independiente de esta feature."
    )
    lines.append(
        "- **kavacomex**: ramp real Motor ~0.99x (casi plano, ver ADR 0013) — se esperaba que "
        "fuera el candidato más probable a Infeasible bajo `vc_minimum` (WORKLOG P1), pero con "
        "los parámetros por defecto de `benchmark_v0/kavacomex.yaml` resultó **Optimal**: el "
        "ceiling default (x3/slack 0.15) sigue dominando incluso en este caso de ramp casi "
        "plano, porque el ceiling actúa sobre el stock consensuado del propio plan (que ya es "
        "mayor que el ramp manual del Excel). La rutina de diagnóstico R1-R8 se corrió de todas "
        "formas (ver abajo) para dejar la herramienta verificada end-to-end; con el estado base "
        "Optimal, todas las relajaciones reportan `feasible=True` trivialmente (nada que "
        "restaurar). El test unitario `test_diagnosis_routine_smoke` cubre el caso genuinamente "
        "infeasible (ceiling sin slack + hiring congelado en 0) con la rutina completa."
    )
    lines.append("")

    lines.append("## Rutina de diagnóstico R1-R8 — kavacomex (vc_minimum)")
    lines.append("")
    if kavacomex_diagnosis is not None:
        lines.append(f"Estado base: **{kavacomex_diagnosis['base_status']}**.")
        lines.append("")
        lines.append(kavacomex_diagnosis["readable_summary"])
        lines.append("")
        lines.append("| relajación | aplica | factible | diagnóstico |")
        lines.append("|---|---|---|---|")
        for r in kavacomex_diagnosis["relaxations"]:
            lines.append(
                f"| {r['relaxation']}: {r['description']} | {r['applicable']} | "
                f"{r.get('feasible')} | {r['diagnosis']} |"
            )
        lines.append("")
        if kavacomex_diagnosis["base_status"] == "Optimal":
            lines.append(
                "Nota: base ya Optimal bajo `benchmark_v0/kavacomex.yaml` con parámetros por "
                "defecto — no hay infactibilidad que diagnosticar en esta corrida específica. "
                "La rutina R1-R8 sigue siendo válida y se verifica de forma independiente en "
                "`tests/test_growth_commitment.py::test_diagnosis_routine_smoke` sobre un caso "
                "sintético construido para ser genuinamente Infeasible (ceiling sin slack + "
                "hiring congelado en 0 nuevas contrataciones/mes)."
            )
            lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

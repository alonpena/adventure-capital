"""Independent DAG, daily-capacity and exported-workbook checks (stdlib)."""

import json
import math
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict, deque

from plan import ROOT, cpm


def verify():
    data = json.loads((ROOT / "plan_data.json").read_text())
    tasks = {t["id"]: t for t in data["tasks"]}
    successors = defaultdict(list)
    degree = {}
    for ident, t in tasks.items():
        assert len({p["id"] for p in t["dependencies"]}) == len(t["dependencies"])
        degree[ident] = len(t["dependencies"])
        for p in t["dependencies"]:
            assert p["id"] in tasks, p
            successors[p["id"]].append(ident)
    ready = deque(k for k, d in degree.items() if not d)
    order = []
    es, ef = {}, {}
    while ready:
        key = ready.popleft()
        order.append(key)
        es[key] = max([ef[p["id"]] for p in tasks[key]["dependencies"]] or [0])
        ef[key] = es[key] + tasks[key]["duration"]
        for child in successors[key]:
            degree[child] -= 1
            if degree[child] == 0:
                ready.append(child)
    assert len(order) == len(tasks), "Cycle"
    finish = max(ef.values())
    ls, lf = {}, {}
    for key in reversed(order):
        lf[key] = min([ls[s] for s in successors[key]] or [finish])
        ls[key] = lf[key] - tasks[key]["duration"]
        t = tasks[key]
        assert [es[key], ef[key], ls[key], lf[key]] == [
            t[k] for k in ["es", "ef", "ls", "lf"]
        ]
        assert t["float"] == ls[key] - es[key] >= 0
    loads = {}
    for key, res in data["resources"].items():
        daily = [
            sum(
                t["effort"].get(key, 0) / t["duration"]
                for t in tasks.values()
                if t["es"] <= d < t["ef"]
            )
            for d in range(finish)
        ]
        assert max(daily) <= res["capacity"] / 5 + 1e-8
        total = sum(t["effort"].get(key, 0) for t in tasks.values())
        assert math.isclose(sum(daily), total)
        loads[key] = dict(
            hours=total,
            peak_day=max(daily),
            peak_week=max(sum(daily[d : d + 5]) for d in range(0, finish, 5)),
        )
    # Adversarial inputs must fail rather than invent dates.
    for deps in [[{"id": "MISSING", "type": "T"}], [{"id": "X", "type": "T"}]]:
        try:
            cpm([dict(id="X", duration=1, dependencies=deps)])
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid graph accepted")
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    workbook = ROOT / "03_PLAN_OPERACIONAL.xlsx"
    with zipfile.ZipFile(workbook) as z:
        names = [
            s.get("name")
            for s in ET.fromstring(z.read("xl/workbook.xml")).findall(
                "s:sheets/s:sheet", ns
            )
        ]
        assert len(names) == 7
        formulas = 0
        for i in range(1, 8):
            sheet = ET.fromstring(z.read(f"xl/worksheets/sheet{i}.xml"))
            errors = [
                c.get("r") for c in sheet.findall(".//s:c", ns) if c.get("t") == "e"
            ]
            assert not errors, (names[i - 1], errors)
            formulas += len(sheet.findall(".//s:f", ns))
        gantt = ET.fromstring(z.read("xl/worksheets/sheet3.xml"))
        assert len(gantt.findall(".//s:conditionalFormatting", ns)) >= 1
        table = ET.fromstring(z.read("xl/worksheets/sheet2.xml"))
        assert len(table.findall(".//s:dataValidation", ns)) >= 2
        summary = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        values = {
            c.get("r"): c.find("s:v", ns).text
            for c in summary.findall(".//s:c", ns)
            if c.find("s:v", ns) is not None
        }
        assert float(values["D8"]) == sum(t["hours"] for t in tasks.values())
        assert float(values["D9"]) == 2193
        assert float(values["D10"]) == 55510500
    output = dict(
        tasks=len(tasks),
        finish_days=finish,
        logical_days=data["validation"]["logical_days"],
        cycles=0,
        overloads=0,
        loads=loads,
        workbook_sheets=names,
        live_formulas=formulas,
        cached_errors=0,
        hours=2193,
        budget_clp=55510500,
        native_excel_recalculation="Not executed; artifact engine recalculation and OOXML checked",
    )
    (ROOT / "evidence" / "final_validation.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    )
    weeks = [
        "# Control semanal de la línea base",
        "",
        "Semanas laborales relativas, sin feriados todavía. El Excel es la vista vigente después de cambios. Cada tarea tiene criterio de aceptación en EDT; al iniciar, descomponer sus acciones en bloques diarios de 0,5–2 días. No todo trabajo activo vence esa semana.",
        "",
        "| Semana | Trabajo activo de Alonso | Trabajo activo empresa | Decisiones / comercial Alejandro | Entregables que vencen |",
        "|---|---|---|---|---|",
    ]
    for week in range(1, 36):
        active = [
            t
            for t in tasks.values()
            if t["es"] < (week * 5) and t["ef"] > (week - 1) * 5
        ]
        ap = [t["id"] for t in active if t["effort"].get("AP", 0)]
        firm = [
            t["id"]
            for t in active
            if any(t["effort"].get(k, 0) for k in ["BE", "FE", "UX", "QA", "OP"])
        ]
        am = [t["id"] for t in active if t["effort"].get("AM", 0)]
        due = [
            f"{t['id']}: {t['deliverable']}"
            for t in tasks.values()
            if (week - 1) * 5 < t["ef"] <= week * 5
        ]
        weeks.append(
            f"| S{week} | {', '.join(ap) or 'Reserva / coordinación'} | {', '.join(firm) or 'Reserva / soporte según contrato'} | {', '.join(am) or 'Seguimiento'} | {'; '.join(due) or 'Sin hito; revisar avance y riesgos'} |"
        )
    weeks += [
        "",
        "## Horas por módulo (tareas, sin coordinación recurrente)",
        "",
        "| Módulo | Horas-persona | Días-persona a 8 h |",
        "|---|---:|---:|",
    ]
    mods = defaultdict(float)
    for t in tasks.values():
        mods[t["module"]] += t["hours"]
    for k, v in mods.items():
        weeks.append(f"| {k} | {v:.0f} | {v / 8:.2f} |")
    weeks += [
        "",
        "Coordinación recurrente: 70 h Alonso, 35 h Alejandro y 58 h líder backend (S4–S32). Incluida en recursos y presupuesto; no duplicar en tareas.",
    ]
    (ROOT / "evidence" / "weekly_plan.md").write_text("\n".join(weeks) + "\n")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    verify()

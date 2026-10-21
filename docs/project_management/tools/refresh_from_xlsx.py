"""Import existing-task edits from XLSX, validate the graph, and relevel.

Standard-library OOXML reader; never uses cached formula values for task inputs.
Run python3 tools/refresh_from_xlsx.py [path.xlsx], then node tools/build_workbook.mjs.
The existing XLSX is not overwritten by this importer. Back it up before export.
"""

import datetime
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from plan import ROOT, RESOURCES, cpm, level

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_sheet(z, index, strings):
    tree = ET.fromstring(z.read(f"xl/worksheets/sheet{index}.xml"))
    cells = {}
    for c in tree.findall(".//s:sheetData/s:row/s:c", NS):
        if c.find("s:f", NS) is not None:
            continue
        val = c.find("s:v", NS)
        text = val.text if val is not None else None
        typ = c.get("t")
        if typ == "s" and text is not None:
            text = strings[int(text)]
        elif typ == "inlineStr":
            text = "".join(x.text or "" for x in c.findall(".//s:t", NS))
        elif text is not None and typ == "d":
            date = datetime.datetime.fromisoformat(text.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
            text = (date - datetime.datetime(1899, 12, 30)).total_seconds() / 86400
        elif text is not None and typ not in ("str", "e"):
            text = float(text)
        cells[c.get("r")] = text
    return cells


def main():
    file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "03_PLAN_OPERACIONAL.xlsx"
    data = json.loads((ROOT / "plan_data.json").read_text())
    with zipfile.ZipFile(file) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = [
                "".join(t.text or "" for t in si.findall(".//s:t", NS))
                for si in ET.fromstring(z.read("xl/sharedStrings.xml"))
            ]
        sheets = {i: read_sheet(z, i, strings) for i in range(1, 8)}
    byid = {t["id"]: t for t in data["tasks"]}
    resource_keys = list(data["resources"])
    seen = set()
    for r in range(6, 6 + len(byid)):
        cell = sheets[2]
        ident = cell.get(f"A{r}")
        if ident not in byid or ident in seen:
            raise ValueError(
                "Unknown/duplicate task; add new tasks in plan_data.json explicitly"
            )
        seen.add(ident)
        t = byid[ident]
        deps = [p.strip() for p in str(cell.get(f"J{r}") or "").split(",") if p.strip()]
        kinds = [
            p.strip() for p in str(cell.get(f"K{r}") or "").split(",") if p.strip()
        ]
        if len(deps) != len(kinds) or any(k not in ["T", "V", "C", "R"] for k in kinds):
            raise ValueError(f"{ident}: predecessor types must match IDs")
        t["dependencies"] = [
            dict(id=p, type=k) for p, k in zip(deps, kinds) if k != "R"
        ]
        for key, column in [
            ("duration", "M"),
            ("optimistic", "AA"),
            ("conservative", "AB"),
        ]:
            n = cell[f"{column}{r}"]
            if n is None or n != int(n) or n < 1:
                raise ValueError(f"Invalid {ident} {key}")
            t[key] = int(n)
        t["status"] = cell.get(f"V{r}", "No iniciada")
        t["progress"] = cell.get(f"W{r}", 0)
        if not 0 <= t["progress"] <= 1:
            raise ValueError("Progress must be 0–1")
        t["effort"] = {
            k: float(cell.get(f"A{chr(ord('D') + i)}{r}", 0) or 0)
            for i, k in enumerate(resource_keys)
        }
        if any(v < 0 for v in t["effort"].values()):
            raise ValueError("Negative effort")
        t["hours"] = sum(t["effort"].values())
    for i, k in enumerate(resource_keys):
        data["resources"][k]["capacity"] = float(sheets[4][f"C{i + 6}"])
        data["resources"][k]["rate"] = float(sheets[4][f"H{i + 6}"])
    RESOURCES.clear()
    RESOURCES.update(data["resources"])
    logical, logical_days = cpm(data["tasks"])
    level(data["tasks"])
    network, finish = cpm(data["tasks"])
    for t in data["tasks"]:
        t.update(network[t["id"]])
    serial = sheets[1]["D3"]
    data["start_date"] = (
        (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=serial))
        .date()
        .isoformat()
    )
    data["months"] = int(sheets[1]["D4"])
    data["validation"].update(logical_days=logical_days, leveled_days=finish)
    data["workbook_overrides"] = {
        "RESUMEN": {
            k: v for k, v in sheets[1].items() if k in [f"J{i}" for i in range(6, 26)]
        },
        "PRESUPUESTO": {
            k: v
            for k, v in sheets[5].items()
            if k in [f"{c}{r}" for r in range(6, 18) for c in ["C", "D", "E", "K"]]
        },
        "RIESGOS": {
            k: v
            for k, v in sheets[6].items()
            if k in [f"{c}{r}" for r in range(6, 18) for c in ["C", "D"]]
        },
        "HITOS Y CONTROL": {
            k: v for k, v in sheets[7].items() if k in [f"F{i}" for i in range(6, 16)]
        },
    }
    (ROOT / "plan_data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"Validated {len(seen)} tasks; no cycles; relevelled finish day {finish}. Export with build_workbook.mjs."
    )


if __name__ == "__main__":
    main()

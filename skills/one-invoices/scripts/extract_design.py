#!/usr/bin/env python3
"""Extract an AEAT record design spreadsheet (diseño de registro, .xlsx) into JSON.

Usage:
    python3 scripts/extract_design.py <design.xlsx> <source-url> <out.json>

Reads every sheet, finds the header row (Nº | Posic. | Lon | Tipo | ...) and keeps the numbered
field rows. Standard library only (an .xlsx is a zip of XML files).
"""
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")) for si in root.findall("m:si", NS)]


def sheet_paths(z: zipfile.ZipFile) -> list[tuple[str, str]]:
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels}
    out = []
    for s in wb.find("m:sheets", NS):
        t = target[s.get(REL_NS)]
        out.append((s.get("name"), t.lstrip("/") if t.startswith("/xl/") else "xl/" + t))
    return out


def rows(z: zipfile.ZipFile, path: str, strings: list[str]) -> list[list[str]]:
    root = ET.fromstring(z.read(path))
    out = []
    for row in root.iter(f"{{{NS['m']}}}row"):
        cells: dict[int, str] = {}
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            if c.get("t") == "s" and v is not None:
                val = strings[int(v.text)]
            elif c.get("t") == "inlineStr":
                val = "".join(t.text or "" for t in c.iter(f"{{{NS['m']}}}t"))
            else:
                val = v.text if v is not None else ""
            cells[col_index(c.get("r"))] = " ".join((val or "").split())
        if cells:
            out.append([cells.get(i, "") for i in range(max(cells) + 1)])
    return out


def parse_sheet(table: list[list[str]]) -> list[dict]:
    head = next((i for i, r in enumerate(table) if r and r[0].startswith("Nº") and len(r) > 2 and r[1].startswith("Posic")), None)
    if head is None:
        return []
    fields = []
    for r in table[head + 1:]:
        r = r + [""] * (7 - len(r))
        if not r[0].isdigit():
            if fields and r[0].lower().startswith("total"):
                break
            continue
        pos = int(r[1]) if r[1].isdigit() else None
        length = int(r[2]) if r[2].isdigit() else None
        fields.append({"n": int(r[0]), "pos": pos, "len": length, "type": r[3].strip(),
                       "desc": r[4], "validation": r[5], "content": r[6]})
    return fields


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    src, url, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    m = re.match(r"DR(\d{3})e(\d{2})v(\d+)", src.stem, re.I)
    if not m:
        print(f"error: cannot read model/year/version from file name {src.name}", file=sys.stderr)
        return 1
    with zipfile.ZipFile(src) as z:
        strings = shared_strings(z)
        pages = {name: parse_sheet(rows(z, path, strings)) for name, path in sheet_paths(z)}
    design = {"model": m.group(1), "year": 2000 + int(m.group(2)), "version": m.group(3),
              "source_file": src.name, "source_url": url,
              "pages": {k: v for k, v in pages.items() if v}}
    out.write_text(json.dumps(design, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{out}: {len(design['pages'])} pages, {sum(len(v) for v in design['pages'].values())} fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())

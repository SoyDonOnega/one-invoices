#!/usr/bin/env python3
"""Build the AEAT model 390 import file (annual VAT summary) and a summary by box from the invoice register.

Usage:
    python3 scripts/aeat390.py <config.json> <year> [--force]

Writes <output_dir>/390/<year>.txt and <year>.md. Never files anything. Uses the same rows and mapping as the
four 303 of the year, by VAT rate, and the same carry-forward chain (negative quarters carried forward).
Pages written: 1, 2, 2 bis, 3, 4, 6, 7 (no simplified regime, no differentiated sectors). Standard library only.
"""
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aeat303  # noqa: E402
import register  # noqa: E402
from aeat303 import GenError, box_fields, render  # noqa: E402

PAGES = ["Pág. 1", "Pág. 2", "Pág. 2 bis", "Pág. 3", "Pág. 4", "Pág. 6", "Pág. 7"]
RATES = (Decimal(4), Decimal(10), Decimal(21))
# (base box, VAT box) by rate, and (total base, total VAT) per section.
ACCRUED = {Decimal(4): ("01", "02"), Decimal(10): ("03", "04"), Decimal(21): ("05", "06")}
EU_ACCRUED = {Decimal(4): ("545", "546"), Decimal(10): ("547", "548"), Decimal(21): ("551", "552")}
DOMESTIC = {Decimal(4): ("190", "191"), Decimal(10): ("603", "604"), Decimal(21): ("605", "606")}
INVESTMENT = {Decimal(4): ("196", "197"), Decimal(10): ("611", "612"), Decimal(21): ("613", "614")}
EU_DEDUCT = {Decimal(4): ("587", "588"), Decimal(10): ("635", "636"), Decimal(21): ("637", "638")}
# Counterparts of the 303 [59] and [120] in section 10 (volume of operations).
NOT_SUBJECT = {"eu-services": "103", "non-eu-services": "110"}
CONFIG = ("nif", "surname", "first_name", "activity", "activity_code", "iae", "register_dir", "output_dir")


def compute(issued: list[dict], received: list[dict], year: int) -> tuple[dict[str, Decimal], dict[str, list[str]]]:
    boxes: dict[str, Decimal] = {}
    src: dict[str, list[str]] = {}

    def put(table, row, who):
        if row["vat_rate"] not in table:
            raise GenError(f"{who} {row['number']}: VAT rate {row['vat_rate']} % is not 4, 10 or 21")
        for b, v in zip(table[row["vat_rate"]], (row["base"], row["vat"])):
            boxes[b] = boxes.get(b, Decimal(0)) + v
            src.setdefault(b, []).append(f"{who} {row['number']} ({row['date']})")

    def total(*boxlist):
        return sum((boxes.get(b, Decimal(0)) for b in boxlist), Decimal(0))

    year_rows = lambda rows: [r for r in rows if r["date"].startswith(f"{year}-")]  # noqa: E731
    for r in year_rows(issued):
        if r["kind"] in NOT_SUBJECT:
            b = NOT_SUBJECT[r["kind"]]
            boxes[b] = boxes.get(b, Decimal(0)) + r["base"]
            src.setdefault(b, []).append(f"issued {r['number']} ({r['date']})")
        else:
            put(ACCRUED, r, "issued")
    for r in year_rows(received):
        if r["kind"] == "domestic":
            put(DOMESTIC, r, "received")
        elif r["kind"] == "investment":
            put(INVESTMENT, r, "received")
        elif r["kind"] == "eu-services":
            put(EU_ACCRUED, r, "received")
            put(EU_DEDUCT, r, "received")
        elif r["kind"] == "not-deductible" and r["vat"]:
            boxes["232"] = boxes.get("232", Decimal(0)) + r["base"]
            src.setdefault("232", []).append(f"received {r['number']} ({r['date']})")
    pairs = lambda t: [b for pair in t.values() for b in pair]  # noqa: E731
    boxes["33"] = total(*pairs(ACCRUED)[0::2], *pairs(EU_ACCRUED)[0::2])
    boxes["34"] = total(*pairs(ACCRUED)[1::2], *pairs(EU_ACCRUED)[1::2])
    boxes["47"] = boxes["34"]
    for (base, vat), t in ((("48", "49"), DOMESTIC), (("50", "51"), INVESTMENT), (("597", "598"), EU_DEDUCT)):
        boxes[base], boxes[vat] = total(*pairs(t)[0::2]), total(*pairs(t)[1::2])
    boxes["64"] = total("49", "51", "598")
    boxes["65"] = boxes["47"] - boxes["64"]
    boxes["84"] = boxes["65"]

    # Results of the year's four 303, from the same chain the 303 uses.
    chain, log = aeat303.history(issued, received, year + 1, 1)
    quarters = [(q, b, used) for y, q, b, used in log if y == year]
    boxes["85"] = sum((a for _, _, used in quarters for oy, _, a in used if oy < year), Decimal(0))
    boxes["86"] = boxes["84"] - boxes["85"]
    boxes["95"] = sum((b["71"] for _, b, _ in quarters if b["71"] > 0), Decimal(0))
    boxes["97"] = sum((a for y, q, a in chain if (y, q) == (year, 4)), Decimal(0))
    boxes["662"] = sum((a for y, q, a in chain if y == year and q < 4), Decimal(0))
    boxes["99"] = total(*pairs(ACCRUED)[0::2])
    boxes["108"] = total("99", "103", "110")  # 390 instructions: 108 = 99 + 103 + 110 + boxes not used here
    return boxes, src


def build(design: dict, cfg: dict, year: int, boxes: dict[str, Decimal]) -> str:
    p = design["pages"]
    p1 = {7: cfg["nif"], 8: cfg["surname"], 9: cfg["first_name"], 10: year,
          12: 0, 13: 0, 15: 0, 16: 0, 17: 0, 19: 2, 20: 2, 21: 2, 22: 2, 23: 0, 24: 0,
          26: cfg["activity"], 27: cfg["activity_code"], 28: cfg["iae"], 44: 0}
    body = render(p["Pág. 1"], p1)
    for name in PAGES[1:]:
        body += render(p[name], {f["n"]: boxes[b] for b, f in box_fields(p[name]).items() if b in boxes})
    head = render(p["Pág. 0"][:13], {4: year})
    return head + body + f"</T3900{year}0A0000>"


def summary(design: dict, year: int, boxes: dict[str, Decimal], src: dict[str, list[str]]) -> str:
    labels = {}
    for name in PAGES[1:]:
        for b, f in box_fields(design["pages"][name]).items():
            labels[b] = aeat303.BOX.sub("", f["desc"]).split(" - ", 1)[-1].strip(" -")
    lines = [f"# Model 390 — {year}", "",
             f"Record design: `{design['source_file']}` (version {design['version']}).",
             "Generated by one-invoices. Not filed: import the `.txt` in the AEAT site, review it and file it there.", "",
             "| Box | Concept | Amount (EUR) | Register rows |", "|---|---|---|---|"]
    for b in sorted(boxes, key=int):
        if boxes[b]:
            lines.append(f"| [{b}] | {labels.get(b, '')} | {boxes[b]:.2f} | {', '.join(src.get(b, []))} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--force"]
    if len(args) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        cfg = aeat303.load_config(args[0])
        year = int(args[1])
        missing = [k for k in CONFIG if not cfg.get(k)]
        if missing:
            raise GenError(f"config is missing: {', '.join(missing)}")
        design = aeat303.load_design(year, "390")
        reg = Path(cfg["register_dir"]).expanduser()
        boxes, src = compute(register.read(reg, "issued"), register.read(reg, "received"), year)
        text = build(design, cfg, year, boxes)
        out = Path(cfg["output_dir"]).expanduser() / "390"
        txt, md = out / f"{year}.txt", out / f"{year}.md"
        if txt.exists() and "--force" not in argv:
            raise GenError(f"{txt} already exists — run again with --force to overwrite")
        out.mkdir(parents=True, exist_ok=True)
        txt.write_text(text, encoding="latin-1", newline="")
        md.write_text(summary(design, year, boxes, src), encoding="utf-8")
        print(f"{txt}\n{md}\nresult [86]: {boxes['86']:.2f} EUR")
    except (GenError, register.RegisterError, FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

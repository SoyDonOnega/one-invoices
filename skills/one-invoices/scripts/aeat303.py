#!/usr/bin/env python3
"""Build the AEAT model 303 import file (fixed-length text) and a summary by box from the invoice register.

Usage:
    python3 scripts/aeat303.py <config.json> <year> <quarter 1-4> [--type I|U|C|D|N] [--iban ES..] [--force]

Writes <output_dir>/303/<year>-T<q>.txt and <year>-T<q>.md. Never files anything.
--type: I pay, U direct debit (needs --iban), C carry forward, D refund (needs --iban), N zero/no activity.
Default: I if the result is positive, C if negative, N if zero. Standard library only.
"""
import json
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import register  # noqa: E402

REFS = Path(__file__).resolve().parent.parent / "references"
TESTED = {2026: "101"}  # design versions the generator is tested against
RATE_BOXES = {Decimal(4): ("01", "03"), Decimal(10): ("04", "06"), Decimal(21): ("07", "09")}
CONST = re.compile(r'^\s*(?:Constante\s*)?"([^"]*)"[\s.]*(?:Nota\b.*)?$', re.I)
BOX = re.compile(r"\[(\d+)\]\s*$")


class GenError(Exception):
    pass


def load_design(year: int) -> dict:
    path = REFS / f"303-{year}.json"
    if not path.exists():
        raise GenError(f"no record design for {year}: download DR303e{year % 100:02d}v*.xlsx from the AEAT site "
                       f"(Ayuda > Diseños de registro > Modelos 300 al 399) and run scripts/extract_design.py")
    d = json.loads(path.read_text(encoding="utf-8"))
    if TESTED.get(year) != d["version"]:
        raise GenError(f"design {d['source_file']} (version {d['version']}) is not the version tested for {year}")
    return d


def box_fields(page: list[dict]) -> dict[str, dict]:
    return {m.group(1): f for f in page if (m := BOX.search(f["desc"]))}


def clean_text(s: str) -> str:
    s = s.upper()
    s = s.translate(str.maketrans("ÁÉÍÓÚÜÀÈÌÒÙ", "AEIOUUAEIOU"))
    return re.sub(r"[^A-Z0-9ÑÇ ]", " ", s)  # ISO-8859-1 keeps Ñ and Ç


def encode(f: dict, value) -> str:
    n, t = f["len"], f["type"].strip()
    if value is None:
        c = CONST.match(f["content"])
        if c and len(c.group(1)) == n:
            return c.group(1)
        return "0" * n if t in ("Num", "N") else " " * n
    if isinstance(value, Decimal):
        cents = int((value * 100).to_integral_value())
        if cents < 0:
            if t != "N":
                raise GenError(f"field {f['n']} ({f['desc'][-40:]}) cannot be negative")
            return "N" + str(-cents).zfill(n - 1)
        out = str(cents).zfill(n)
    else:
        out = clean_text(str(value)).ljust(n) if t in ("An", "A") else str(value).zfill(n)
    if len(out) != n:
        raise GenError(f"field {f['n']} ({f['desc'][-40:]}) does not fit in {n}: {out!r}")
    return out


def render(page: list[dict], values: dict[int, object]) -> str:
    out = "".join(encode(f, values.get(f["n"])) for f in page)
    expected = page[-1]["pos"] + page[-1]["len"] - 1
    if len(out) != expected:
        raise GenError(f"page length {len(out)} != {expected}")
    return out


def in_quarter(d: str, year: int, q: int) -> bool:
    x = date.fromisoformat(d)
    return x.year == year and (x.month - 1) // 3 + 1 == q


def compute(issued: list[dict], received: list[dict], year: int, q: int) -> tuple[dict[str, Decimal], dict[str, list[str]]]:
    """Box number -> amount, and box number -> register rows behind it."""
    boxes: dict[str, Decimal] = {}
    src: dict[str, list[str]] = {}

    def put(base_box, vat_box, row, who):
        boxes[base_box] = boxes.get(base_box, Decimal(0)) + row["base"]
        boxes[vat_box] = boxes.get(vat_box, Decimal(0)) + row["vat"]
        for b in (base_box, vat_box):
            src.setdefault(b, []).append(f"{who} {row['number']} ({row['date']})")

    for r in (r for r in issued if in_quarter(r["date"], year, q)):
        if r["vat_rate"] not in RATE_BOXES:
            raise GenError(f"issued {r['number']}: VAT rate {r['vat_rate']} % is not 4, 10 or 21")
        put(*RATE_BOXES[r["vat_rate"]], r, "issued")
    for r in (r for r in received if in_quarter(r["date"], year, q)):
        if r["kind"] == "domestic":
            put("28", "29", r, "received")
        elif r["kind"] == "investment":
            put("30", "31", r, "received")
        elif r["kind"] == "eu-services":
            put("10", "11", r, "received")
            put("36", "37", r, "received")
    accrued = sum((boxes.get(b, Decimal(0)) for b in ("03", "06", "09", "11")), Decimal(0))
    deductible = sum((boxes.get(b, Decimal(0)) for b in ("29", "31", "37")), Decimal(0))
    boxes.update({"27": accrued, "45": deductible, "46": accrued - deductible})
    boxes.update({"64": boxes["46"], "65": Decimal(100), "66": boxes["46"], "69": boxes["46"], "71": boxes["46"]})
    return boxes, src


def build(design: dict, cfg: dict, year: int, q: int, boxes: dict[str, Decimal], kind: str, iban: str) -> str:
    p = design["pages"]
    period = f"{q}T"
    last = q == 4
    p1 = {6: kind, 7: cfg["nif"], 8: cfg["name"], 9: year, 10: period,
          11: 2, 12: 2, 13: 3, 14: 2, 15: 2, 16: 2, 17: 2 if last else " ", 18: 2 if last else " ", 19: 2,
          20: " ", 21: " ", 22: 2, 23: 2 if last else 0, 24: 0, 25: 0}
    p1.update({f["n"]: boxes[b] for b, f in box_fields(p["DP30301"]).items() if b in boxes})
    p3 = {f["n"]: boxes[b] for b, f in box_fields(p["DP30303"]).items() if b in boxes}
    if kind == "N" and not any(boxes.get(b) for b in ("27", "45")):
        p3[30] = "X"
    did = {6: iban, 11: 1} if kind in ("U", "D") else {}  # 11: SEPA mark, 1 = Spanish account
    # Wrapper (DP30300): fields 1-13 open it, the pages follow, field 15 closes it.
    head = render(p["DP30300"][:13], {4: year, 5: period})
    body = render(p["DP30301"], p1) + render(p["DP30303"], p3) + render(p["DP303DID"], did)
    return head + body + f"</T3030{year}{period}0000>"


def summary(design: dict, year: int, q: int, boxes: dict[str, Decimal], src: dict[str, list[str]], kind: str) -> str:
    labels = {}
    for name in ("DP30301", "DP30303"):
        for b, f in box_fields(design["pages"][name]).items():
            labels[b] = re.sub(r"^(Liquidación \(3\) - |Regimen General - |Resultado - )+", "", BOX.sub("", f["desc"])).strip(" -")
    lines = [f"# Model 303 — {year} Q{q}", "",
             f"Record design: `{design['source_file']}` (version {design['version']}). Declaration type: `{kind}`.",
             "Generated by one-invoices. Not filed: import the `.txt` in the AEAT site, review it and file it there.", "",
             "| Box | Concept | Amount (EUR) | Register rows |", "|---|---|---|---|"]
    for b in sorted(boxes, key=int):
        if boxes[b] and b != "65":
            lines.append(f"| [{b}] | {labels.get(b, '')} | {boxes[b]:.2f} | {', '.join(src.get(b, []))} |")
    if not any(boxes[b] for b in ("27", "45")):
        lines += ["", "No register rows in this quarter: zero return."]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    args, opts, it = [], {}, iter(argv)
    for a in it:
        if a == "--force":
            opts[a] = "1"
        elif a in ("--type", "--iban"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if len(args) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        cfg = json.loads(Path(args[0]).expanduser().read_text(encoding="utf-8"))
        year, q = int(args[1]), int(args[2])
        if q not in (1, 2, 3, 4):
            raise GenError("quarter must be 1-4")
        missing = [k for k in ("nif", "name", "register_note", "output_dir") if not cfg.get(k)]
        if missing:
            raise GenError(f"config is missing: {', '.join(missing)}")
        design = load_design(year)
        note = Path(cfg["register_note"]).expanduser()
        boxes, src = compute(register.read(note, "issued"), register.read(note, "received"), year, q)
        res = boxes["71"]
        kind = opts.get("--type") or ("I" if res > 0 else "C" if res < 0 else "N")
        iban = (opts.get("--iban") or "").replace(" ", "").upper()
        if kind not in ("I", "U", "C", "D", "N"):
            raise GenError(f"unknown --type {kind}")
        if kind in "UD" and not iban.startswith("ES"):
            raise GenError(f"--type {kind} needs a Spanish --iban")
        text = build(design, cfg, year, q, boxes, kind, iban)
        out = Path(cfg["output_dir"]).expanduser() / "303"
        txt, md = out / f"{year}-T{q}.txt", out / f"{year}-T{q}.md"
        if txt.exists() and "--force" not in opts:
            raise GenError(f"{txt} already exists — run again with --force to overwrite")
        out.mkdir(parents=True, exist_ok=True)
        txt.write_text(text, encoding="latin-1", newline="")
        md.write_text(summary(design, year, q, boxes, src, kind), encoding="utf-8")
        print(f"{txt}\n{md}\nresult [71]: {res:.2f} EUR, type {kind}")
    except (GenError, register.RegisterError, FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

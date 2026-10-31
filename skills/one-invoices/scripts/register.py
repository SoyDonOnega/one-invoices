#!/usr/bin/env python3
"""Invoice register kept as two Markdown tables in a note: issued and received invoices.

Usage:
    python3 scripts/register.py init <note.md>
    python3 scripts/register.py list <note.md> [issued|received]
    python3 scripts/register.py add <note.md> issued|received '<row as JSON>'

Rows are append-only. Amounts are written with a dot and two decimals (1200.00); dates as YYYY-MM-DD.
Standard library only.
"""
import json
import re
import sys
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HEADINGS = {"issued": "## Issued invoices", "received": "## Received invoices"}
COLUMNS = {
    "issued": ["Nº", "Date", "Client", "Client tax ID", "Base", "VAT %", "VAT", "IRPF withheld", "Total", "PDF"],
    "received": ["Nº", "Date", "Supplier", "Supplier tax ID", "Country", "Kind", "Base", "VAT %", "VAT", "Total", "PDF"],
}
KEYS = {
    "issued": ["number", "date", "client", "client_tax_id", "base", "vat_rate", "vat", "irpf", "total", "pdf"],
    "received": ["number", "date", "supplier", "supplier_tax_id", "country", "kind", "base", "vat_rate", "vat", "total", "pdf"],
}
AMOUNTS = {"base", "vat", "irpf", "total"}
KINDS = {"domestic", "eu-services", "investment", "not-deductible"}
# EU VAT number prefixes (model 349 annex, without GB; Greece is EL).
EU_PREFIXES = {"AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU", "IE", "IT", "LT", "LU",
               "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"}
CENT = Decimal("0.01")


class RegisterError(Exception):
    pass


def money(v) -> Decimal:
    try:
        return Decimal(str(v).replace(" ", "")).quantize(CENT, rounding=ROUND_HALF_UP)
    except Exception:
        raise RegisterError(f"not an amount: {v!r}")


def header_lines(kind: str) -> list[str]:
    cols = COLUMNS[kind]
    return ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def find_table(lines: list[str], kind: str) -> tuple[int, int] | None:
    """Return (header index, end index exclusive) of the table under the kind's heading, or None."""
    try:
        h = next(i for i, l in enumerate(lines) if l.strip() == HEADINGS[kind])
    except StopIteration:
        return None
    start = next((i for i in range(h + 1, len(lines)) if lines[i].lstrip().startswith("|")), None)
    if start is None or any(lines[i].startswith("## ") for i in range(h + 1, start)):
        raise RegisterError(f"'{HEADINGS[kind]}' has no table")
    if cells(lines[start]) != COLUMNS[kind]:
        got = cells(lines[start])
        diff = next((f"column {i + 1}: expected '{e}', found '{g}'" for i, (e, g) in enumerate(zip(COLUMNS[kind], got)) if e != g),
                    f"expected {len(COLUMNS[kind])} columns, found {len(got)}")
        raise RegisterError(f"'{HEADINGS[kind]}' header changed by hand — {diff}")
    end = start + 2
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    return start, end


def init(note: Path) -> list[str]:
    """Add any missing table (with its heading) at the end of the note. Returns the kinds added."""
    lines = note.read_text(encoding="utf-8").splitlines()
    added = []
    for kind in ("issued", "received"):
        if find_table(lines, kind) is None:
            lines += ["", HEADINGS[kind], ""] + header_lines(kind)
            added.append(kind)
    if added:
        note.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return added


def read(note: Path, kind: str) -> list[dict]:
    lines = note.read_text(encoding="utf-8").splitlines()
    t = find_table(lines, kind)
    if t is None:
        raise RegisterError(f"no '{HEADINGS[kind]}' table in {note} — run init")
    rows = []
    for line in lines[t[0] + 2:t[1]]:
        c = cells(line)
        if not any(c):
            continue
        row = dict(zip(KEYS[kind], c))
        for k in AMOUNTS & row.keys():
            row[k] = money(row[k])
        row["vat_rate"] = Decimal(row["vat_rate"])
        rows.append(row)
    return rows


def validate(kind: str, row: dict) -> dict:
    missing = [k for k in KEYS[kind] if k != "pdf" and str(row.get(k, "")).strip() == ""]
    if missing:
        raise RegisterError(f"missing fields: {', '.join(missing)}")
    r = {k: str(row.get(k, "")).strip() for k in KEYS[kind]}
    try:
        date.fromisoformat(r["date"])
    except ValueError:
        raise RegisterError(f"date must be YYYY-MM-DD: {r['date']!r}")
    for k in AMOUNTS & set(KEYS[kind]):
        r[k] = money(r[k])
    r["vat_rate"] = Decimal(r["vat_rate"])
    base, vat, total = r["base"], r["vat"], r["total"]
    if kind == "issued":
        expected = base + vat - r["irpf"]
        if abs(expected - total) > CENT:
            raise RegisterError(f"base {base} + VAT {vat} − IRPF {r['irpf']} = {expected}, but total is {total}")
    else:
        if r["kind"] not in KINDS:
            raise RegisterError(f"kind must be one of {', '.join(sorted(KINDS))}: {r['kind']!r}")
        if r["kind"] == "eu-services":
            # Reverse charge: the supplier charges no VAT; the VAT column holds the Spanish VAT the buyer self-assesses.
            r["vat"] = (base * r["vat_rate"] / 100).quantize(CENT, rounding=ROUND_HALF_UP)
            if abs(total - base) > CENT:
                raise RegisterError(f"EU service invoice: total {total} should equal base {base} (no VAT charged)")
        elif abs(base + vat - total) > CENT:
            raise RegisterError(f"base {base} + VAT {vat} = {base + vat}, but total is {total}")
    party = "client_tax_id" if kind == "issued" else "supplier_tax_id"
    r[party] = r[party].upper().replace(" ", "")
    if kind == "received" and r["kind"] == "eu-services" and (r[party][:2] not in EU_PREFIXES - {"ES"} or len(r[party]) < 4):
        raise RegisterError(f"EU service invoice {r['number']}: supplier tax ID {r[party]!r} must start with an EU country code")
    return r


def fmt(v) -> str:
    return f"{v:.2f}" if isinstance(v, Decimal) else str(v)


def add(note: Path, kind: str, row: dict) -> dict:
    r = validate(kind, row)
    party = "client_tax_id" if kind == "issued" else "supplier_tax_id"
    for old in read(note, kind):
        if old["number"] == r["number"] and old[party].upper() == r[party]:
            raise RegisterError(f"already in the register: {old['number']} ({old[party]}) of {old['date']}")
    lines = note.read_text(encoding="utf-8").splitlines()
    _, end = find_table(lines, kind)
    rate = r["vat_rate"].normalize()
    values = [str(rate) if k == "vat_rate" else fmt(r[k]) for k in KEYS[kind]]
    lines.insert(end, "| " + " | ".join(v.replace("|", "/") for v in values) + " |")
    note.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return r


def main(argv: list[str]) -> int:
    try:
        if len(argv) >= 2 and argv[0] == "init":
            added = init(Path(argv[1]))
            print(f"added: {', '.join(added)}" if added else "both tables already present")
        elif len(argv) >= 2 and argv[0] == "list":
            for kind in argv[2:] or ["issued", "received"]:
                for r in read(Path(argv[1]), kind):
                    print(kind, json.dumps({k: str(v.normalize()) if k == "vat_rate" else fmt(v) for k, v in r.items()},
                                           ensure_ascii=False))
        elif len(argv) == 4 and argv[0] == "add" and argv[2] in KEYS:
            r = add(Path(argv[1]), argv[2], json.loads(argv[3]))
            print(f"added {argv[2]} {r['number']} of {r['date']}: total {r['total']}")
        else:
            print(__doc__.strip(), file=sys.stderr)
            return 2
    except (RegisterError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

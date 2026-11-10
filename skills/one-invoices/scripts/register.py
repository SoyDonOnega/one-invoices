#!/usr/bin/env python3
"""Invoice register kept as one Markdown note per invoice, with the fields as note properties (frontmatter).

Usage:
    python3 scripts/register.py init <register folder>
    python3 scripts/register.py list <register folder> [issued|received]
    python3 scripts/register.py add <register folder> issued|received '<row as JSON>' [--pdf <file> --to <folder>]
    python3 scripts/register.py check <register folder> issued|received '<row as JSON>'
    python3 scripts/register.py render issued|received '<row as JSON>' [--pdf-dir <PDF folder>]

add writes a new note YYYY-MM_<party>_<number>.md and never changes an existing one. With --pdf, the file is
moved into --to as YYYY-MM_<party>_<number>.pdf and the note links to it; the move happens only after the row
passes every check, and is undone if the note cannot be written.
check validates the row against a copy of the register (totals, duplicates) without writing. render validates the
row and prints {"note": name, "pdf": name, "text": note content} with the PDF link set to <PDF folder>/<pdf name>,
without writing anything: for callers that write through another channel (e.g. a Drive connector).
Amounts with a dot and two decimals (1200.00); dates as YYYY-MM-DD. Standard library only.
"""
import json
import re
import shutil
import sys
import unicodedata
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from urllib.parse import quote

KEYS = {
    "issued": ["number", "date", "client", "client_tax_id", "kind", "base", "vat_rate", "vat", "irpf", "total", "pdf"],
    "received": ["number", "date", "supplier", "supplier_tax_id", "country", "kind", "base", "vat_rate", "vat", "total", "pdf"],
}
AMOUNTS = {"base", "vat", "irpf", "total"}
KINDS = {"domestic", "eu-services", "investment", "not-deductible"}
# Issued: domestic (Spanish VAT charged), eu-services (B2B service to an EU client: 0 %, 303 [59], 390 [103], 349 S),
# non-eu-services (service to a client outside the EU, not subject by place of supply: 0 %, 303 [120], 390 [110]).
ISSUED_KINDS = {"domestic", "eu-services", "non-eu-services"}
DOMESTIC_RATES = {Decimal(4), Decimal(10), Decimal(21)}
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


def init(folder: Path) -> bool:
    """Create the register folder if missing. Returns True when it was created."""
    if folder.is_dir():
        return False
    folder.mkdir(parents=True)
    return True


def frontmatter(text: str, name: str) -> dict[str, str]:
    """Flat 'key: value' frontmatter. Quoted values are JSON strings."""
    m = re.match(r"---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not m:
        raise RegisterError(f"{name}: no properties block")
    out = {}
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        k, sep, v = line.partition(":")
        if not sep:
            raise RegisterError(f"{name}: cannot read property line {line!r}")
        v = v.strip()
        if v.startswith('"'):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                raise RegisterError(f"{name}: cannot read value of {k.strip()!r}")
        out[k.strip()] = v
    return out


def read(folder: Path, kind: str) -> list[dict]:
    if not folder.is_dir():
        raise RegisterError(f"no register folder {folder} — run init")
    rows = []
    for f in sorted(folder.glob("*.md")):
        props = frontmatter(f.read_text(encoding="utf-8"), f.name)
        if props.get("register") != kind:
            continue
        if kind == "issued":
            props.setdefault("kind", "domestic")  # notes written before issued kinds existed
        missing = [k for k in KEYS[kind] if k != "pdf" and k not in props]
        if missing:
            raise RegisterError(f"{f.name}: missing properties {', '.join(missing)}")
        row = {k: props.get(k, "") for k in KEYS[kind]}
        for k in AMOUNTS & row.keys():
            row[k] = money(row[k])
        row["vat_rate"] = Decimal(row["vat_rate"])
        row["note"] = f.name
        rows.append(row)
    return sorted(rows, key=lambda r: (r["date"], r["number"]))


def validate(kind: str, row: dict) -> dict:
    if kind == "issued" and not str(row.get("kind", "")).strip():
        row = {**row, "kind": "domestic"}
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
        if r["kind"] not in ISSUED_KINDS:
            raise RegisterError(f"kind must be one of {', '.join(sorted(ISSUED_KINDS))}: {r['kind']!r}")
        if r["kind"] == "domestic" and r["vat_rate"] not in DOMESTIC_RATES:
            raise RegisterError(f"domestic issued invoice: VAT rate {r['vat_rate']} % is not 4, 10 or 21 "
                                f"(no Spanish VAT: kind eu-services or non-eu-services)")
        if r["kind"] != "domestic" and (r["vat_rate"] or vat):
            raise RegisterError(f"{r['kind']} issued invoice: VAT rate and VAT must be 0")
    else:
        if r["kind"] not in KINDS:
            raise RegisterError(f"kind must be one of {', '.join(sorted(KINDS))}: {r['kind']!r}")
        if r["kind"] == "eu-services":
            # Reverse charge: the supplier charges no VAT; the VAT field holds the Spanish VAT the buyer self-assesses.
            r["vat"] = (base * r["vat_rate"] / 100).quantize(CENT, rounding=ROUND_HALF_UP)
            if abs(total - base) > CENT:
                raise RegisterError(f"EU service invoice: total {total} should equal base {base} (no VAT charged)")
        elif abs(base + vat - total) > CENT:
            raise RegisterError(f"base {base} + VAT {vat} = {base + vat}, but total is {total}")
    party = "client_tax_id" if kind == "issued" else "supplier_tax_id"
    r[party] = r[party].upper().replace(" ", "")
    if r["kind"] == "eu-services" and (r[party][:2] not in EU_PREFIXES - {"ES"} or len(r[party]) < 4):
        who = "client" if kind == "issued" else "supplier"
        raise RegisterError(f"EU service invoice {r['number']}: {who} tax ID {r[party]!r} must start with an EU country code other than ES")
    if r["kind"] == "non-eu-services" and r[party][:2] in EU_PREFIXES:
        raise RegisterError(f"non-EU service invoice {r['number']}: client tax ID {r[party]!r} starts with an EU country code "
                            f"(EU client: kind eu-services)")
    return r


def fmt(v) -> str:
    return f"{v:.2f}" if isinstance(v, Decimal) else str(v)


def check_new(folder: Path, kind: str, r: dict) -> None:
    party = "client_tax_id" if kind == "issued" else "supplier_tax_id"
    for old in read(folder, kind):
        if old["number"] == r["number"] and old[party].upper() == r[party]:
            raise RegisterError(f"already in the register: {old['number']} ({old[party]}) of {old['date']}")
    if (folder / note_name(kind, r)).exists():
        raise RegisterError(f"{note_name(kind, r)} already exists in the register")


def file_stem(kind: str, r: dict) -> str:
    """YYYY-MM_<party>_<number>, ASCII letters, digits and hyphens only."""
    def slug(s: str) -> str:
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
        return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-") or "x"
    party = r["client"] if kind == "issued" else r["supplier"]
    return f"{r['date'][:7]}_{slug(party.split()[0] if party else '')}_{slug(r['number'])}"


def pdf_name(kind: str, r: dict) -> str:
    return file_stem(kind, r) + ".pdf"


def note_name(kind: str, r: dict) -> str:
    return file_stem(kind, r) + ".md"


def pdf_link(path: Path) -> str:
    return f"[{path.name}](file://{quote(str(path))})"


def note_text(kind: str, r: dict, pdf_path: str = "") -> str:
    """The invoice note: properties in a fixed order, then a link to the PDF."""
    lines = ["---", f"register: {kind}"]
    for k in KEYS[kind]:
        if k == "pdf":
            continue
        v = r[k]
        if k == "vat_rate":
            lines.append(f"{k}: {v.normalize()}")
        elif isinstance(v, Decimal):
            lines.append(f"{k}: {v:.2f}")
        elif k == "date":
            lines.append(f"{k}: {v}")
        else:
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    if pdf_path:
        lines.append(f"pdf: {json.dumps('file://' + quote(pdf_path))}")
    party = r["client"] if kind == "issued" else r["supplier"]
    lines += ["---", "", f"{'Issued' if kind == 'issued' else 'Received'} invoice {r['number']} — {party}, {r['date']}."]
    if pdf_path:
        lines += ["", f"PDF: {pdf_link(Path(pdf_path))}"]
    return "\n".join(lines) + "\n"


def add(folder: Path, kind: str, row: dict, pdf_path: str = "") -> dict:
    r = validate(kind, row)
    check_new(folder, kind, r)
    (folder / note_name(kind, r)).write_text(note_text(kind, r, pdf_path), encoding="utf-8")
    return r


def add_with_pdf(folder: Path, kind: str, row: dict, src: Path, pdf_folder: Path) -> dict:
    """Validate the row, move the PDF into pdf_folder with a uniform name, then write the note linking to it."""
    r = validate(kind, row)
    check_new(folder, kind, r)
    if not src.is_file() or src.suffix.lower() != ".pdf":
        raise RegisterError(f"not a PDF file: {src}")
    dest = pdf_folder.expanduser() / pdf_name(kind, r)
    if src.resolve() != dest.resolve():
        if dest.exists():
            raise RegisterError(f"{dest} already exists")
        pdf_folder.expanduser().mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
    try:
        return add(folder, kind, row, str(dest))
    except Exception:
        if src.resolve() != dest.resolve():
            shutil.move(str(dest), str(src))
        raise


def main(argv: list[str]) -> int:
    try:
        if len(argv) >= 2 and argv[0] == "init":
            print("register folder created" if init(Path(argv[1]).expanduser()) else "register folder already present")
        elif len(argv) >= 2 and argv[0] == "list":
            for kind in argv[2:] or ["issued", "received"]:
                for r in read(Path(argv[1]).expanduser(), kind):
                    print(kind, json.dumps({k: str(v.normalize()) if k == "vat_rate" else fmt(v) for k, v in r.items()},
                                           ensure_ascii=False))
        elif len(argv) in (4, 8) and argv[0] == "add" and argv[2] in KEYS:
            opts = dict(zip(argv[4::2], argv[5::2]))
            if len(argv) == 8 and set(opts) != {"--pdf", "--to"}:
                print(__doc__.strip(), file=sys.stderr)
                return 2
            folder, row = Path(argv[1]).expanduser(), json.loads(argv[3])
            if opts:
                r = add_with_pdf(folder, argv[2], row, Path(opts["--pdf"]).expanduser(), Path(opts["--to"]))
            else:
                r = add(folder, argv[2], row)
            print(f"added {argv[2]} {r['number']} of {r['date']}: total {r['total']} → {note_name(argv[2], r)}")
        elif len(argv) == 4 and argv[0] == "check" and argv[2] in KEYS:
            r = validate(argv[2], json.loads(argv[3]))
            check_new(Path(argv[1]).expanduser(), argv[2], r)
            print(f"ok: {note_name(argv[2], r)}")
        elif len(argv) in (3, 5) and argv[0] == "render" and argv[1] in KEYS:
            opts = dict(zip(argv[3::2], argv[4::2]))
            if len(argv) == 5 and set(opts) != {"--pdf-dir"}:
                print(__doc__.strip(), file=sys.stderr)
                return 2
            r = validate(argv[1], json.loads(argv[2]))
            pdf_path = str(Path(opts["--pdf-dir"]) / pdf_name(argv[1], r)) if opts else ""
            print(json.dumps({"note": note_name(argv[1], r), "pdf": pdf_name(argv[1], r),
                              "text": note_text(argv[1], r, pdf_path)}, ensure_ascii=False))
        else:
            print(__doc__.strip(), file=sys.stderr)
            return 2
    except (RegisterError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

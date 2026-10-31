---
name: one-invoices
description: >-
  Registers a Spanish freelancer's issued and received invoices from their PDFs and generates
  the AEAT import file for model 303 with a summary by box. Never files anything.
  Use when the user runs /one-invoices add <pdf> or /one-invoices 303 <year> <quarter>.
license: MIT
compatibility: Requires Python 3.12 and pdftotext (poppler).
argument-hint: "add <pdf> | 303 <year> <T1-T4>"
disable-model-invocation: true
---

# One Invoices

Keeps the user's invoice register and turns it into the file the AEAT online form for model 303 imports. It does not issue invoices, file returns or give tax advice: the user confirms every row and files every return. Models 349 and 390 are not built yet.
Paths in this file are relative to the skill root (the folder that contains this SKILL.md).

## When invoked

1. **Configuration.** Read `skill-data/one-invoices/config.json` (the folder next to the skills folder). If it is missing, copy `data/config.json` there. If any field is empty, ask the user for it, save it and continue. Fields: `nif`, `name` (as in the census registration), `issued_pdfs`, `received_pdfs`, `register_note`, `output_dir`.
2. **Register ready.** Run `python3 scripts/register.py init <register_note>`. It adds the issued and received tables if they are missing and refuses if a header was changed by hand; show that error and stop.
3. **`add <pdf>`**
   1. The PDF must be inside `issued_pdfs` (issued) or `received_pdfs` (received). Otherwise ask the user to move it there and stop.
   2. Run `pdftotext -layout <pdf> -`. No text: say so and ask the user for the fields; never guess.
   3. Propose the row as a table with every field (issued: number, date, client, client tax ID, base, VAT %, VAT, IRPF withheld, total; received: number, date, supplier, supplier tax ID, country, kind, base, VAT %, VAT, total). Mark fields you could not read. Received `kind`: `domestic`, `eu-services` (EU supplier, no VAT charged), `investment` (asset used for more than a year), `not-deductible`. Ask the user to confirm or correct; never decide the kind alone when unsure.
   4. On confirmation run `python3 scripts/register.py add <register_note> <issued|received> '<row JSON>'` with `pdf` set to a Markdown link to the file. On an error, show it, fix the row with the user and retry.
4. **`303 <year> <quarter>`**
   1. Run `python3 scripts/register.py list <register_note>` and show the rows of that quarter.
   2. Ask how the result is settled only if it is not the default (pay if positive, carry forward if negative, zero return if zero): direct debit (`--type U --iban <IBAN>`) or refund (`--type D --iban <IBAN>`).
   3. Run `python3 scripts/aeat303.py skill-data/one-invoices/config.json <year> <quarter> [--type ..] [--iban ..]`. If the file exists, ask before adding `--force`.
   4. Show the summary `.md` (boxes, amounts, rows behind each box) and tell the user: import the `.txt` in the AEAT site (model 303, import file), check every box against the summary, then file it there.

## Rules

- Never file, sign or submit anything to the AEAT, and never ask for the user's certificate or credentials.
- Never add a register row without the user's confirmation, and never edit or delete existing rows: corrections are made by the user in the note.
- Amounts come from the invoice as printed; never recompute them except the self-assessed VAT of EU services, which the script does.
- Never write invoices, the register or generated files inside the skill folder or a repo.
- Answer in the user's language.

## Resources

- `scripts/register.py` — `init`, `list` and `add` (validates totals, refuses duplicates, append-only) on the two Markdown tables.
- `scripts/aeat303.py` — builds `<output_dir>/303/<year>-T<q>.txt` (AEAT import file) and `.md` (summary by box) from the register.
- `scripts/extract_design.py` — turns an AEAT record design spreadsheet into `references/303-<year>.json`.
- `references/303-2026.json` — record design `DR303e26v101` (fields, positions, lengths, source URL).
- `data/config.json` — empty configuration template.

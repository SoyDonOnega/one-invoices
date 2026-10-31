---
name: one-invoices
description: >-
  Registers a Spanish freelancer's issued and received invoices from their PDFs and generates
  the AEAT import files for models 303, 349 and 390 with a summary. Never files anything.
  Use when the user runs /one-invoices add [<pdf> …], 303 <year> <quarter>, 349 <year> <quarter> or 390 <year>.
license: MIT
compatibility: Requires Python 3.12 and pdftotext (poppler).
argument-hint: "add [<pdf> …] | 303 <year> <T1-T4> | 349 <year> <T1-T4> | 390 <year>"
disable-model-invocation: true
---

# One Invoices

Keeps the user's invoice register and turns it into the files the AEAT online forms for models 303, 349 and 390 import. It does not issue invoices, file returns or give tax advice: the user confirms every row and files every return.
Paths in this file are relative to the skill root (the folder that contains this SKILL.md).

## When invoked

1. **Configuration.** Read `skill-data/one-invoices/config.json` (the folder next to the skills folder). If it is missing, copy `data/config.json` there. If a field the command needs is empty, ask the user for it, save it and continue. Always: `nif`, `name` (surnames then first name, as in the census registration), `issued_pdfs`, `received_pdfs`, `register_note`, `output_dir`; optional `inbox` (default `~/Downloads`). For 349 also `phone`, `contact_name`. For 390 also `surname`, `first_name`, `activity`, `activity_code`, `iae` (as in the census registration).
2. **Register ready.** Run `python3 scripts/register.py init <register_note>`. It adds the issued and received tables if they are missing and refuses if a header was changed by hand; show that error and stop.
3. **`add [<pdf> …]`** — one or more invoices, issued or received.
   1. **Find the PDFs.** Take every PDF the user gave: an argument, an `@` mention or a file dropped into the chat (the app passes its path). With none, list the PDFs in `inbox` (default `~/Downloads`) changed in the last 14 days and ask which to add. A PDF shown without a path on disk cannot be moved: ask the user to drop the file itself or save it to `inbox`.
   2. **Read each one.** Run `pdftotext -layout <pdf> -`. No text: say so and ask the user for the fields; never guess.
   3. **Issued or received.** Issued when the issuer's tax ID is the user's `nif` (the client's self-bills are issued in the user's name); received otherwise.
   4. **Propose.** Show one table with a row per PDF and every field (issued: number, date, client, client tax ID, base, VAT %, VAT, IRPF withheld, total; received: number, date, supplier, supplier tax ID, country, kind, base, VAT %, VAT, total), plus issued/received and the file name it will get (`YYYY-MM_<party>_<number>.pdf`). Mark fields you could not read. Received `kind`: `domestic`, `eu-services` (EU supplier, no VAT charged), `investment` (asset used for more than a year), `not-deductible`. Never decide the kind alone when unsure: ask. The user confirms all rows, some, or corrects any field.
   5. **Write.** For each confirmed row run `python3 scripts/register.py add <register_note> <issued|received> '<row JSON>' --pdf <file> --to <issued_pdfs|received_pdfs>`. It checks the row, moves the PDF into its folder under the new name (never overwriting), then writes the row with a link to it; on any error nothing is moved or written. Show the error, fix the row with the user and retry. Report what was added and where each PDF went.
4. **`303 <year> <quarter>`**
   1. Run `python3 scripts/register.py list <register_note>` and show the rows of that quarter.
   2. Ask how the result is settled only if it is not the default (pay if positive, carry forward if negative, zero return if zero): direct debit (`--type U --iban <IBAN>`) or refund (`--type D --iban <IBAN>`).
   3. Amounts pending from earlier quarters ([110]) are computed from the register, assuming every negative quarter was carried forward. If the user chose a refund in an earlier quarter, or the register starts after the first quarter of activity, ask for the pending amount the AEAT site shows and pass `--carry <amount>`.
   4. Run `python3 scripts/aeat303.py skill-data/one-invoices/config.json <year> <quarter> [--type ..] [--iban ..] [--carry ..]`. If the file exists, ask before adding `--force`.
   5. Show the summary `.md` (boxes, amounts, rows behind each box, pending chain) and tell the user: import the `.txt` in the AEAT site (model 303, import file), check every box against the summary, then file it there.
5. **`349 <year> <quarter>`**
   1. Show the EU rows of the quarter (`register.py list`): received `eu-services` (key I) and issued to EU clients without VAT (key S).
   2. Run `python3 scripts/aeat349.py skill-data/one-invoices/config.json <year> <quarter> [--id <13 digits>]`. With no EU rows it writes nothing: tell the user there is nothing to declare. If the file exists, ask before adding `--force`.
   3. Show the summary by operator and tell the user to import the `.txt` in the AEAT site, check it and file it there.
6. **`390 <year>`**
   1. Run `python3 scripts/aeat390.py skill-data/one-invoices/config.json <year>`. If the file exists, ask before adding `--force`.
   2. Show the summary and tell the user to compare it with the four 303 filed for the year, import the `.txt` in the AEAT site, check it and file it there.

## Rules

- Never file, sign or submit anything to the AEAT, and never ask for the user's certificate or credentials.
- Never add a register row without the user's confirmation, and never edit or delete existing rows: corrections are made by the user in the note.
- Amounts come from the invoice as printed; never recompute them except the self-assessed VAT of EU services, which the script does.
- Never write invoices, the register or generated files inside the skill folder or a repo.
- Answer in the user's language.

## Resources

- `scripts/register.py` — `init`, `list` and `add` (validates totals, refuses duplicates, append-only; with `--pdf --to` moves the PDF into its folder under a uniform name and links it) on the two Markdown tables.
- `scripts/aeat303.py` — builds `<output_dir>/303/<year>-T<q>.txt` (AEAT import file) and `.md` (summary by box) from the register.
- `scripts/aeat349.py` — builds `<output_dir>/349/<year>-T<q>.txt` and `.md` (summary by EU operator).
- `scripts/aeat390.py` — builds `<output_dir>/390/<year>.txt` and `.md` (summary by box).
- `scripts/extract_design.py` — turns an AEAT record design spreadsheet into `references/<model>-<year>.json`.
- `references/303-2026.json`, `390-2026.json` — record designs `DR303e26v101` and `dr390e2026` v1.00, extracted from the AEAT spreadsheets.
- `references/349-2026.json` — record design of `DR_Anexo_349.pdf`, copied by hand (with the PDF page of each field).
- `data/config.json` — empty configuration template.

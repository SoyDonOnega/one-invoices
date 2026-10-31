---
name: one-invoices
description: >-
  Registers a Spanish freelancer's issued and received invoices from their PDFs and generates
  the AEAT import files for models 303, 349 and 390 with a summary. Never files anything.
  Use when the user asks to add invoice PDFs to the register or to build a model 303, 349 or 390 file
  (/one-invoices add [PDF …] | 303 YEAR QUARTER | 349 YEAR QUARTER | 390 YEAR).
license: MIT
compatibility: Local files, or code execution plus a Google Drive connector. Python 3.12; pdftotext (poppler) when available.
argument-hint: "add [<pdf> …] | 303 <year> <T1-T4> | 349 <year> <T1-T4> | 390 <year>"
disable-model-invocation: true
---

# One Invoices

Keeps the user's invoice register and turns it into the files the AEAT online forms for models 303, 349 and 390 import. It does not issue invoices, file returns or give tax advice: the user confirms every row and files every return.
Paths in this file are relative to the skill root (the folder that contains this SKILL.md). `CONFIG` below is the configuration file path.

The register is a folder with one Markdown note per invoice; its fields are the note's properties. Notes are only ever added, never changed by the skill, so it works where files can be created but not edited.

## Where it runs

- **Local mode** (the agent can read and write the user's files): follow "When invoked" as written. `CONFIG` is `skill-data/one-invoices/config.json` (the folder next to the skills folder); a file with only `{"config": <path>}` points to the real one, kept in the notes.
- **Drive mode** (no local files; code execution and a Google Drive connector that can create, read and move files but not edit them): before "When invoked", build a working copy, then follow the Drive-mode steps below:
  1. Find the file titled `one-invoices.json` in Drive, download it and save it as `work/config.json` (`CONFIG`). Its `drive` block holds the folder IDs: `register`, `issued`, `received`, `output` and, optionally, `inbox` (the shared inbox below).
  2. List every file with `parentId` = `drive.register` (follow `next_page_token`), download each `.md` into `work/Register/`, and in `work/config.json` set `register_dir` to `work/Register` and `output_dir` to `work/out`. Keep `issued_pdfs` and `received_pdfs` as they are: they are the paths on the user's Mac that note links point to.
  3. If the Drive connector or code execution is missing, say which one and stop.

## When invoked

1. **Configuration.** Read `CONFIG`. If it is missing in local mode, copy `data/config.json` there. If a field the command needs is empty, ask the user for it; in local mode save it, in Drive mode ask the user to add it to `one-invoices.json`. Always: `nif`, `name` (surnames then first name, as in the census registration), `issued_pdfs`, `received_pdfs`, `register_dir`, `output_dir`; optional `inbox` (default `~/Downloads`) and `shared_inbox` (a folder where invoice PDFs arrive from elsewhere, e.g. forwarded by another assistant; its Drive ID is `drive.inbox`). For 349 also `phone`, `contact_name`. For 390 also `surname`, `first_name`, `activity`, `activity_code`, `iae` (as in the census registration).
2. **Register ready.** In local mode run `python3 scripts/register.py init <register_dir>` (creates the folder if missing). A note it cannot read stops every command: show the error and stop.
3. **`add [<pdf> …]`** — one or more invoices, issued or received.
   1. **Find the PDFs.** Take every PDF the user gave: an argument, an `@` mention or a file dropped into the chat. With none, list the PDFs waiting in `shared_inbox` (Drive mode: the files in `drive.inbox`) and, in local mode, those in `inbox` (default `~/Downloads`) changed in the last 14 days, and ask which to add.
      - Local mode: the app passes each dropped file's path. A PDF shown without a path on disk cannot be moved: ask the user to drop the file itself or save it to `inbox`.
      - Drive mode: only PDFs already in Drive can be filed (the connector moves and renames files; it cannot upload a PDF of real size, so never try). A PDF attached to the chat can be read and proposed, but before writing ask the user to put it in the shared inbox (or the issued/received folder) and then take it from there.
   2. **Read each one.** Local mode: `pdftotext -layout <pdf> -`. Drive mode: read the Drive file's text through the connector (or the attachment directly); never pass the PDF's bytes through the conversation. No text: say so and ask the user for the fields; never guess.
   3. **Issued or received.** Issued when the issuer's tax ID is the user's `nif` (the client's self-bills are issued in the user's name); received otherwise.
   4. **Propose.** Show one table with a row per PDF and every field (issued: number, date, client, client tax ID, base, VAT %, VAT, IRPF withheld, total; received: number, date, supplier, supplier tax ID, country, kind, base, VAT %, VAT, total), plus issued/received and the file name it will get: take it from `python3 scripts/register.py render <issued|received> '<row JSON>'` (field `pdf`), never compose it by hand. Mark fields you could not read. Received `kind`: `domestic`, `eu-services` (EU supplier, no VAT charged), `investment` (a capital good for VAT purposes, which is narrower than "used for more than a year": never propose it on your own, ask the user), `not-deductible`. Never decide the kind alone when unsure: ask. The user confirms all rows, some, or corrects any field.
   5. **Write (local mode).** For each confirmed row run `python3 scripts/register.py add <register_dir> <issued|received> '<row JSON>' --pdf <file> --to <issued_pdfs|received_pdfs>`. It checks the row, moves the PDF into its folder under the new name (never overwriting), then writes the invoice note with a link to it; on any error nothing is moved or written. Show the error, fix the row with the user and retry. Report what was added and where each PDF went.
   6. **Write (Drive mode).** For each confirmed row:
      1. `python3 scripts/register.py check work/Register <issued|received> '<row JSON>'` (totals, duplicates). On an error, fix the row with the user and retry.
      2. `python3 scripts/register.py render <issued|received> '<row JSON>' --pdf-dir <issued_pdfs|received_pdfs>` prints the note name, the PDF name and the note text.
      3. Search Drive for the note name in `drive.register` and the PDF name in `drive.issued` / `drive.received`. If either exists, stop for that row and say so: Drive mode cannot overwrite.
      4. **File the PDF.** If it is in Drive outside the issued/received folder (e.g. in `drive.inbox`), move and rename it with the connector's file update (`fileId`, `title` = the PDF name, `parentId` = `drive.issued` or `drive.received`). If it is only a chat attachment, ask the user to put it in the shared inbox first (step 1). The app asks the user to approve each Drive write; if the user declines, stop for that row and say nothing changed.
      5. Create the note in `drive.register` (`textContent`, `contentMimeType` `text/markdown`, `disableConversionToGoogleType` true). If this fails or is declined after the PDF was moved, move the PDF back to where it was, with its old name, and say so.
      6. Report what was added. The notes reach the Mac when Google Drive syncs.
4. **`303 <year> <quarter>`**
   1. Run `python3 scripts/register.py list <register_dir>` and show the rows of that quarter.
   2. Ask how the result is settled only if it is not the default (pay if positive, carry forward if negative, zero return if zero): direct debit (`--type U --iban <IBAN>`) or refund (`--type D --iban <IBAN>`).
   3. Amounts pending from earlier quarters ([110]) are computed from the register, assuming every negative quarter was carried forward. If the user chose a refund in an earlier quarter, or the register starts after the first quarter of activity, ask for the pending amount the AEAT site shows and pass `--carry <amount>`.
   4. Run `python3 scripts/aeat303.py CONFIG <year> <quarter> [--type ..] [--iban ..] [--carry ..]`. If the file exists, ask before adding `--force`.
   5. Show the summary `.md` (boxes, amounts, rows behind each box, pending chain) and tell the user: import the `.txt` in the AEAT site (model 303, import file), check every box against the summary, then file it there.
5. **`349 <year> <quarter>`**
   1. Show the EU rows of the quarter (`register.py list`): received `eu-services` (key I) and issued to EU clients without VAT (key S).
   2. Run `python3 scripts/aeat349.py CONFIG <year> <quarter> [--id <13 digits>]`. With no EU rows it writes nothing: tell the user there is nothing to declare. If the file exists, ask before adding `--force`.
   3. Show the summary by operator and tell the user to import the `.txt` in the AEAT site, check it and file it there.
6. **`390 <year>`**
   1. Run `python3 scripts/aeat390.py CONFIG <year>`. If the file exists, ask before adding `--force`.
   2. Show the summary and tell the user to compare it with the four 303 filed for the year, import the `.txt` in the AEAT site, check it and file it there.
7. **Saving the files (Drive mode).** The generators write into `work/out/<model>/`. In Drive, find the folder titled `303`, `349` or `390` with `parentId` = `drive.output` (create it as a folder if missing). If a file of the same name is already there, do not upload: say so (Drive mode cannot overwrite; the user deletes the old one or runs it in local mode). Otherwise create the `.txt` with `base64Content` of its bytes (a few KB; ISO-8859-1, `contentMimeType` `text/plain`, `disableConversionToGoogleType` true) and the `.md` with `textContent` (`text/markdown`, same flag). Also offer the `.txt` as a file in the chat, so the user can import it from the device.

## Rules

- Never file, sign or submit anything to the AEAT, and never ask for the user's certificate or credentials.
- Never add an invoice without the user's confirmation, and never edit or delete an invoice note: corrections are made by the user in Obsidian.
- Amounts come from the invoice as printed; never recompute them except the self-assessed VAT of EU services, which the script does.
- Never write invoices, the register or generated files inside the skill folder or a repo.
- Never pass a PDF's bytes through the conversation (base64 in a tool call): file PDFs by moving them.
- Answer in the user's language.

## Harness notes

- Claude Code runs in local mode.
- The Claude app (web, desktop chat, phone) runs in Drive mode: upload this folder as a custom skill, turn on code execution and connect Google Drive.

## Resources

- `scripts/register.py` — `init`, `list`, `add` (validates totals, refuses duplicates, new notes only; with `--pdf --to` moves the PDF into its folder under a uniform name and links it), `check` and `render` (for Drive mode, which writes through the connector).
- `scripts/aeat303.py` — builds `<output_dir>/303/<year>-T<q>.txt` (AEAT import file) and `.md` (summary by box) from the register.
- `scripts/aeat349.py` — builds `<output_dir>/349/<year>-T<q>.txt` and `.md` (summary by EU operator).
- `scripts/aeat390.py` — builds `<output_dir>/390/<year>.txt` and `.md` (summary by box).
- `scripts/extract_design.py` — turns an AEAT record design spreadsheet into `references/<model>-<year>.json`.
- `references/303-2026.json`, `390-2026.json` — record designs `DR303e26v101` and `dr390e2026` v1.00, extracted from the AEAT spreadsheets.
- `references/349-2026.json` — record design of `DR_Anexo_349.pdf`, copied by hand (with the PDF page of each field).
- `data/config.json` — empty configuration template (`drive` holds the Drive folder IDs used in Drive mode).

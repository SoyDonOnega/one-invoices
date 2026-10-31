# Proposal

## Why

The user files model 303 every quarter and the annual 390, and today copies figures by hand from invoice PDFs. The first real deadline is the 303 for Q4 2026 (until 30 January 2027), filed by the user's tax adviser while this tool is tested; the tool's file must match what the adviser files.

## What Changes

- A register of issued and received invoices kept as Markdown tables in the user's notes, filled from the invoice PDFs after the user confirms each row.
- A generator of the model 303 import file (fixed-length `.txt`, official record design for 2026, version 1.01) and a Markdown summary by box, both written to the user's `303/` folder.
- A machine-readable copy of the official record design, extracted from the AEAT spreadsheet with its source URL and version, so the generator never hard-codes positions from memory.
- Models 349 and 390 are out of scope (phase 2).

## Capabilities

### New Capabilities

- `invoice-register`: the register of issued and received invoices, its fields and how rows are added.
- `invoice-intake`: turning an invoice PDF into a proposed register row the user confirms.
- `aeat-303-file`: the quarterly model 303 import file and its summary, built from the register.

### Modified Capabilities

None.

## Impact

- New Python scripts and tests in this repo; no dependencies beyond the standard library and `pdftotext`.
- Writes only to paths in the user's configuration (`skill-data/one-invoices/config.json`).
- No interaction with the AEAT: the user imports the file in the AEAT site.

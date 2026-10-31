# Design

## Context

See proposal.md. The AEAT publishes each model's import format as a spreadsheet ("diseño de registro"): for 303 in 2026, `DR303e26v101.xlsx` (https://sede.agenciatributaria.gob.es/static_files/Sede/Disenyo_registro/DR_300_399/archivos_26/DR303e26v101.xlsx), with a wrapper record (`DP30300`) and pages `DP30301`–`DP30305` plus `DP303DID`. Each field has position, length, type (An / Num) and content rules; amounts are 17 digits (15 integers, 2 decimals). The user's invoices are self-billed by the client, so the tool never issues invoices.

## Goals / Non-Goals

**Goals:**
- One generator that is driven by data (the design copy), so a new year means a new design file, not new code.
- Tests that pin the output to a real AEAT export.

**Non-Goals:**
- Models 349 and 390, deadlines calendar, comparison with the adviser's filing (later changes).
- Any page of 303 the user does not need (special regimes, pro rata, foral).

## Decisions

- **Design copy as JSON, extracted by a script.** `scripts/extract_design.py` reads the AEAT `.xlsx` with the standard library (zip + XML) and writes `references/303-2026.json` (fields, positions, lengths, types, constants, source URL, version). Alternative: hand-typed positions — rejected, error-prone and not auditable.
- **Generator fills only named fields; everything else is the design's default** (blanks for An, zeros for Num, constants as given). Alternative: a template file — rejected, hides positions.
- **Register as Markdown tables in the user's note.** Readable in the notes app, diffable, no database. Alternative: CSV — rejected, not readable in the notes app.
- **PDF reading by the agent, writing by scripts.** Supplier invoices have no common layout, so the agent proposes the fields from `pdftotext` output; `scripts/register.py add` validates and appends. Alternative: regex parsers per supplier — rejected for now, brittle.
- **Golden test from an AEAT export.** The user fills the online 303 form with made-up figures and exports the file without filing; the test regenerates it from the same figures.

## Risks / Trade-offs

- [Wrapper fields for software developers (program version, developer NIF) may be required] → the golden export shows what the AEAT itself writes; copy that.
- [Box numbering in the design differs from the printed form] → the summary maps design fields to the printed box numbers, and the Sede import shows any mismatch before filing.
- [Rounding] → amounts are kept as integer cents end to end; rounding happens once per row, as printed on the invoice.
- [Design changes mid-year] → each design file carries its version; the generator refuses a version it was not tested with.

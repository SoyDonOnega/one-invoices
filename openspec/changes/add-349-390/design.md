# Design

## Context

See proposal.md. Sources, both checked byte for byte against the copies the user downloaded on 2026-10-31:

- 390: `dr390e2026.xlsx`, version 1.00 — https://sede.agenciatributaria.gob.es/static_files/Sede/Disenyo_registro/DR_300_399/archivos_26/dr390e2026.xlsx. Wrapper `Pág. 0` (period `0A`, closing `</T3900EEEE0A0000>`) and pages 1, 2, 2 bis, 3, 4, 5, 6, 7, 8 (lengths 1188, 1806, 531, 1840, 854, 1519, 862, 781, 1092).
- 349: `DR_Anexo_349.pdf` — https://sede.agenciatributaria.gob.es/static_files/Sede/Disenyo_registro/DR_300_399/archivos_20/DR_Anexo_349.pdf. Published in the 2020 folder and linked from the current design index; no later version found. Record type 1 (declarant) and type 2 (operator or rectification), 500 positions each; amounts as 13 or 15 digits with the last two as decimals; all amounts positive.
- General rules: AEAT guide "Diseños de registro — breve manual de uso" (v.2, 12/12/2022).

## Goals / Non-Goals

**Goals:**
- Same approach as 303: generators driven by a JSON copy of the design, refusing untested versions, pinned by golden files exported from the AEAT site.
- 303 carry-forward computed, so a negative quarter is not forgotten in the next one.

**Non-Goals:**
- 349 rectification records (type 2, rectifications): refused with a message; the user files those by hand.
- 390 pages for regimes the user is not in (simplified regime page 5, special regimes, pro rata page 8, recargo de equivalencia page 2 bis).
- Model 100.

## Decisions

- **349 design hand-copied to JSON.** The PDF has no machine-readable table. `references/349-2026.json` lists each field (positions, length, type, constant) with the page of the PDF it comes from; the test checks positions are contiguous and each record is 500 long. Alternative: parse the PDF text — rejected, the layout is prose.
- **349 from the register.** Received rows of kind `eu-services` give key `I`; issued rows to an EU client with no VAT give key `S` (none today, kept for completeness). Rows are summed per operator (country + tax ID) and key in the quarter, one type 2 record each. Supplier tax ID must start with the EU country code; the register check refuses one that does not.
- **No 349 when there is nothing to declare.** A quarter with no EU operations produces no file and says so.
- **390 from the four quarters.** The same mapping as 303, summed over the year, into page 1 (identification and activity), pages 2–4 (accrued and deductible VAT by rate), page 6 (annual result) and page 7 (turnover), plus the 303 results of each quarter where the design asks for them. Which pages the AEAT form requires for a filer like the user is confirmed by the golden export.
- **Carry-forward in 303.** [110] is the sum of negative [71] results of earlier quarters still pending, from the first quarter with register rows; [78] is the part applied this quarter (at most the positive result before it); [87] = [110] − [78]. The summary shows the chain quarter by quarter so the user can check it against the pending amount the AEAT site shows. Alternative: the user types the amount — rejected as the default, kept as `--carry <amount>` to override.
- **Extractor reads columns by header name.** Some sheets add a "Comp" column; version is read from the file name or, for `dr390e2026`, from the sheet heading ("vers.1.00" → `100`). Done in the phase 1 follow-up.

## Risks / Trade-offs

- [Line breaks between 349 records are not stated in the annex] → the golden export shows them; until then the generator writes CRLF, as in other AEAT informative files.
- [349 declaration number (13 digits starting with 349) may need to be a number the AEAT issues] → the generator takes it from `--id`; the golden export shows whether the form accepts any number.
- [390 page set] → golden export; the generator leaves out a page only when the design says it may be left out empty.
- [Wrapper developer fields] → same as 303: blank until a golden export shows otherwise.
- [Carry-forward across years] → the chain runs over all years in the register; a year without register rows breaks the chain and the tool asks for `--carry`.

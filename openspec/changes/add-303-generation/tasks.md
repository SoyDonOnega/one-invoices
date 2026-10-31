# Tasks

## 1. Record design

- [x] 1.1 Write `scripts/extract_design.py` (xlsx → JSON, standard library) and generate `references/303-2026.json` from `DR303e26v101.xlsx`
- [x] 1.2 Test: every field's position equals the previous position plus length; totals match the design

## 2. Register

- [x] 2.1 Write `scripts/register.py` (read, validate and append rows in the two Markdown tables)
- [x] 2.2 Tests: header check, totals check, duplicate refusal, append-only
- [x] 2.3 Add the received-invoices table to the user's note and fill the config in `skill-data/one-invoices/`

## 3. Intake

- [x] 3.1 SKILL.md `add` flow: folder check, `pdftotext`, proposed row, confirmation, `register.py add`
- [ ] 3.2 Try it on the October 2026 Shakers self-bill and one Anthropic invoice

## 4. Model 303

- [x] 4.1 Map register rows to design fields (output VAT by rate, reverse charge, deductible VAT, result)
- [x] 4.2 Write `scripts/aeat303.py` (file + summary) and the SKILL.md `303` flow
- [ ] 4.3 User exports a 303 with made-up figures from the AEAT site (no filing); add it as the golden test and make it pass
- [ ] 4.4 Generate 303 Q4 2026; user imports it in the AEAT site without filing and checks it

## 5. Skill

- [x] 5.1 `check_skill.py --embedded` with 0 errors
- [x] 5.2 Install the skill (copied into the skills folder; kept out of OneStack, 2026-10-31)

## Workflow follow-up

- Compare the generated Q4 2026 file with the 303 the adviser files (by 30 January 2027).
- Archive the change and start `add-349-390`.

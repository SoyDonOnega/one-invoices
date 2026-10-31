# Tasks

## 1. Designs

- [ ] 1.1 Generate `references/390-2026.json` from `dr390e2026.xlsx` with `extract_design.py`; test page lengths
- [ ] 1.2 Hand-copy `references/349-2026.json` from `DR_Anexo_349.pdf` (field, positions, type, PDF page); test contiguous positions and 500-long records

## 2. Model 303 carry-forward

- [ ] 2.1 Compute [110], [78], [87] from earlier quarters; `--carry` override; summary shows the chain
- [ ] 2.2 Tests for the scenarios in the spec delta

## 3. Model 349

- [ ] 3.1 Register check: EU tax IDs start with an EU country code
- [ ] 3.2 Write `scripts/aeat349.py` (file + summary, `--id`) and the SKILL.md `349` flow
- [ ] 3.3 User exports a 349 with made-up figures from the AEAT site (no filing); golden test

## 4. Model 390

- [ ] 4.1 Config fields (surname, first name, activity, activity code, IAE heading) and the SKILL.md question flow
- [ ] 4.2 Write `scripts/aeat390.py` (file + summary) and the SKILL.md `390` flow
- [ ] 4.3 Test: 390 totals equal the sums of the four 303
- [ ] 4.4 User exports a 390 with made-up figures from the AEAT site (no filing); golden test

## 5. Skill

- [ ] 5.1 README, SKILL.md and `check_skill.py --embedded` with 0 errors
- [ ] 5.2 Compare the generated 2026 files with what the adviser files (by 30 January 2027)

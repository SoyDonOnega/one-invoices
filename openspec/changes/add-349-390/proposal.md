# Proposal

## Why

Phase 1 builds the quarterly 303. The user also files the 349 in quarters with EU service purchases (e.g. Anthropic) and the annual 390. The first deadlines are the 349 for Q4 2026 (if there are EU purchases) and the 390 for 2026, both by 30 January 2027, filed by the adviser while the tool is tested. The 303 also needs the amounts to carry forward from earlier quarters as soon as one quarter ends with a negative result.

## What Changes

- A generator of the model 349 import file (fixed-length records of 500 positions: one declarant record and one record per EU operator and operation key), with a summary by operator.
- A generator of the model 390 import file (same wrapper and pages as 303; design `dr390e2026`, version 1.00) built from the four quarters of the register, with a summary by box.
- The 303 computes the carry-forward boxes ([110], [78], [87]) from the earlier quarters' results.
- A hand-written machine-readable copy of the 349 design (the AEAT publishes it only as a PDF), checked by the same position tests as the spreadsheet designs.
- New configuration fields: contact phone and name (349), surname and first name apart, main activity, activity code and IAE heading (390).

## Capabilities

### New Capabilities

- `aeat-349-file`: the quarterly model 349 import file and its summary, built from the register.
- `aeat-390-file`: the annual model 390 import file and its summary, built from the register.

### Modified Capabilities

- `aeat-303-file`: adds the carry-forward from earlier quarters (added requirement; this change is archived after `add-303-generation`).

## Impact

- New scripts `aeat349.py` and `aeat390.py`, references `349-2026.json` and `390-2026.json`, tests and golden files.
- `config.json` template gains the new fields; existing private configs keep working and the skill asks for the missing fields only when the 349 or 390 is run.
- No interaction with the AEAT: the user imports each file in the AEAT site.

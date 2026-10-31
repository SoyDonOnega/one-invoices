# Proposal

## Why

The user wants to add invoices and generate returns from the Claude app (web or phone), not only from Claude Code. There the agent has no local files, only code execution and the Google Drive connector, which can create, read and move files but cannot edit an existing file. A register kept as tables inside one note cannot be appended to from there.

## What Changes

- **BREAKING** The register becomes a folder with one note per invoice (fields as note properties) instead of two tables in `Facturación.md`. An Obsidian Base shows the two tables; `Facturación.md` embeds it. The old tables were empty, so nothing is migrated.
- Configuration key `register_note` becomes `register_dir`. The configuration moves next to the register note (`one-invoices.json`) so both environments read the same file; `skill-data/one-invoices/config.json` only points to it.
- A Drive mode in the skill: it builds a working copy of the register from Drive, runs the same scripts, and writes new PDFs, notes and generated files through the connector. It never overwrites.
- `register.py` gains `check` and `render` (validate and produce the note without writing).

## Capabilities

### New Capabilities

- `drive-mode`: running the skill where only code execution and a Google Drive connector are available.

### Modified Capabilities

- `invoice-register`: one note per invoice instead of two tables (edited in the open change `add-303-generation`, not yet archived).

## Impact

- `register.py` rewritten for notes; generators read `register_dir`. Tests updated.
- The user uploads the skill folder to the Claude app as a custom skill and keeps the Google Drive connector on.

# one-invoices

Agent skill `/one-invoices`: register a Spanish freelancer's invoices and expenses and generate the AEAT import files for models 303, 349 and 390.

## What it does

- Reads invoice PDFs (issued or received) dropped into the chat or found in Downloads, proposes the register rows, and after the user confirms adds them and files each PDF in its folder under a uniform name.
- Keeps the register as one Markdown note per invoice (fields as note properties), shown as two tables by an Obsidian Base.
- Runs where it has local files (Claude Code) or only code execution and a Google Drive connector (the Claude app, web or phone): there it reads the register from Drive and only creates files.
- Generates the fixed-length `.txt` file that the AEAT online form imports, following the official record design of each model and year, plus a Markdown summary by box.
- Never files anything: the user imports the file in the AEAT site, reviews it and files it.

Status: register, PDF intake and models 303, 349 and 390 are implemented (`openspec/changes/add-303-generation/`, `add-349-390/`). Each still needs the byte-for-byte check against a file exported from the AEAT site.

## Usage

```
/one-invoices add [<pdf> …]      read PDFs (dropped in the chat, or new ones in Downloads), add them
                                 to the register and file each PDF in its folder
/one-invoices 303 <year> <T1-T4> generate 303/<year>-T<n>.txt and .md
/one-invoices 349 <year> <T1-T4> generate 349/<year>-T<n>.txt and .md (only with EU operations)
/one-invoices 390 <year>         generate 390/<year>.txt and .md
```

## Install

- Claude Code: copy `skills/one-invoices/` as `<skills dir>/one-invoices/` (e.g. `~/.claude/skills/one-invoices/`). It is not part of OneStack.
- Claude app: `python3 tools/package_app.py` builds `~/Downloads/one-invoices.zip` (without the Claude Code-only keys, so the model can invoke it); upload it as a custom skill, turn on code execution and connect Google Drive.

## Requirements

- Python 3.12 (standard library only).
- `pdftotext` (poppler) to read PDFs.

## Layout

- `skills/one-invoices/SKILL.md` — the skill.
- `skills/one-invoices/scripts/` — deterministic tools (register, file generators).
- `skills/one-invoices/references/` — AEAT record designs as JSON, with source URL and version.
- `skills/one-invoices/data/config.json` — empty configuration template.
- `tools/package_app.py` — builds the .zip for the Claude app.
- `tests/` — tests (`python3 -m unittest discover -s tests`), including a byte-for-byte comparison with a file exported from the AEAT site once `tests/golden/` has one.
- `openspec/` — specs and changes (OpenSpec, schema spec-driven).

## Private data

Invoices, the register and generated files never enter this repo. Settings live in `one-invoices.json` next to the register note (paths, Drive folder IDs); `skill-data/one-invoices/config.json` next to the skills folder may hold only `{"config": <path>}` pointing to it.

## License

MIT

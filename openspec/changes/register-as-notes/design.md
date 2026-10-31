# Design

## Context

Google Drive connector, checked 2026-10-31: `create_file` (text or base64 content, parent folder, optional no conversion), `download_file_content`, `search_files`, `update_file` (metadata and parent only: it cannot replace content). So the skill can add files but not edit them from the Claude app.

## Decisions

- **One note per invoice, properties as fields.** Adding an invoice is creating a file, which both environments can do. Obsidian Bases renders the table and sums. Alternative: Google Sheets register — rejected, it leaves the notes; inbox folder imported later from Claude Code — rejected, two steps and no returns from the phone.
- **Properties format.** Flat `key: value`; text values as JSON strings, dates as `YYYY-MM-DD`, amounts with two decimals, so Obsidian types them and the parser stays in the standard library.
- **Same scripts in both modes.** Drive mode downloads the register notes into a working folder, runs `check` / `render` / the generators there, and uploads results. Only the transport differs.
- **One configuration.** `one-invoices.json` next to the register note, with a `drive` block of folder IDs (register, issued PDFs, received PDFs, output). Local mode follows a pointer file in `skill-data`.
- **Never overwrite.** Drive allows two files with the same name; Drive mode searches first and stops if the name exists.
- **Harness-neutral wording.** The skill speaks of local mode and Drive mode; the harness mapping is in "Harness notes" (Skill Standard).

## Risks / Trade-offs

- [Drive sync delay] → a note created from the phone reaches the Mac when Drive syncs; Obsidian then shows it.
- [Custom skills in the Claude app may not honour slash-only invocation] → the description names the commands; to verify with a test invoice.
- [A PDF uploaded but its note fails] → the skill says which PDF was created so the user can remove or retry.

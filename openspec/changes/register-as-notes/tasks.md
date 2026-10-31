# Tasks

- [x] 1 Rewrite `register.py` for one note per invoice; `check` and `render`; tests
- [x] 2 Generators read `register_dir`; config pointer (`load_config`)
- [x] 3 Register folder, `Register.base` and `Facturación.md` embed in the notes; config moved to `one-invoices.json` with Drive folder IDs
- [x] 4 SKILL.md: local mode and Drive mode; Harness notes
- [x] 5 Upload the skill to the Claude app (2026-10-31: accepted after removing tag-like text from the description; read-only test in a chat used the skill and the Drive connector, read the config and the register folder)
- [x] 6 First real invoice added from the Claude app (2026-10-31, SH-T-44085-26-001): note created through Drive after approval, synced to the Mac, read by `register.py list` and the 303. The PDF could not go through the connector (about 122,000 base64 characters in one call): the user saves it, the tool checks it
- [x] 7 Shared inbox (`shared_inbox`, `drive.inbox`): PDFs forwarded on WhatsApp land in Drive; Drive mode files them by moving, never by uploading bytes
- [x] 8 First invoice end to end through the shared inbox in the Claude app (2026-10-31: Apple UA36248033 saved by the assistant, moved to Received and noted from the Claude app)

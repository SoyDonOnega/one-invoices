# Workflow

How invoices go from the inbox of a phone to the files the AEAT online forms import. The skill does the register and the files; the routines and the assistant are the user's own setup (templates in `routines/`). Nothing is ever filed: the user imports each file in the AEAT site and files it there.

## Pieces

| Piece | Where it runs | Does |
|---|---|---|
| Messaging assistant (e.g. on WhatsApp) | The user's phone | Receives each invoice PDF and saves it, unchanged, in a shared inbox folder in Google Drive. Relays messages between the routines and the user |
| Shared inbox | Google Drive | `shared_inbox` (local path) / `drive.inbox` (Drive ID): invoice PDFs waiting to be registered |
| Register | Notes (Obsidian), in Drive | One note per invoice; an Obsidian Base shows them as two tables |
| PDF folders | Google Drive | `issued_pdfs` and `received_pdfs`: every registered PDF, renamed `YYYY-MM_<party>_<number>.pdf` |
| Mailbox | Notes, in Drive | Two append-only files the routines and the assistant use to talk |
| Monthly routine | Claude Code, scheduled on the user's computer | Registers the PDFs in the shared inbox (automatic mode); before a filing month, asks the user whether anything is missing |
| Daily routine | Claude Code, scheduled | When the assistant relays the user's "generate", builds the quarter's files (automatic mode) and reports back |
| Claude app (web, phone) | Drive mode | Optional, interactive: register a PDF or build a return from the phone |

## One quarter, end to end

1. **During the quarter.** Each invoice that arrives is forwarded to the assistant. It saves the PDF in the shared inbox and leaves a notice in the mailbox. The user does nothing else.
2. **Last evening of each month.** The monthly routine registers every PDF in the shared inbox without asking (automatic mode, rules below), moves each PDF to the issued or received folder and creates its note. A PDF that fails a check stays in the inbox and is named in the next message.
3. **Last evening before January, April, July and October.** The monthly routine lists the quarter's invoices and asks, through the mailbox, whether anything is missing. The assistant relays the question in its morning message on day 1.
4. **The user answers.** Missing invoices go to the assistant as usual. When all is there, the user answers "generate" (in the user's language). The assistant writes a notice in the mailbox quoting the answer.
5. **Next daily run.** The daily routine registers anything new, then generates the 303, the 349 when there were EU operations and, in January, the 390. It reports each result through the mailbox; the assistant relays it.
6. **Filing.** The user imports the `.txt` in the AEAT site, checks every box against the `.md` summary and files it. During the trial period the user's adviser files and the generated file is compared with theirs.

Corrections: the user edits the invoice note in Obsidian before answering "generate". The files are derived from the register and are regenerated on request.

## Automatic mode rules

Set by the user in advance; they replace the confirmation per invoice. Every check of the interactive mode still runs (totals, duplicates, EU tax ID prefix).

- Issued when the issuer's tax ID is the user's `nif` (self-bills included); received otherwise.
- Received `eu-services` when the supplier's tax ID has an EU prefix other than ES and no VAT is charged; `domestic` in every other case. `investment` and `not-deductible` are never used: the user's standing choice is that every expense is deductible.
- `country` is the tax ID's prefix, `ES` when it has none.
- A duplicate of an invoice already registered with the same PDF is staged for deletion, never deleted.

## Interactive use

- **Claude Code** (local mode): `/one-invoices add` with PDFs dropped in the chat, or with no arguments to pick up the shared inbox and recent Downloads; the user confirms each row.
- **Claude app** (Drive mode): "register the invoices in the inbox"; the app asks to approve each Drive write. A PDF attached to the chat can be read but not uploaded (the connector takes file content inside the call), so it goes through the shared inbox first.

## What needs the user

- Forwarding each invoice to the assistant.
- Answering the quarter question.
- Filing in the AEAT site (certificate and signature are the user's).
- Approving each tool once, on the routines' first run, so later runs do not stop for permission.

## Timing

Routines run while the computer is awake and the Claude app is open; a run that was due while the app was closed runs on next launch. Filing windows: 1–20 April, July and October; 1–30 January for Q4 and the 390.

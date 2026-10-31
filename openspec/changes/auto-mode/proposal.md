# Proposal

## Why

José wants invoices handled without sessions: he forwards each PDF to his WhatsApp assistant, which saves it in a shared inbox in Drive, and scheduled routines do the rest. He does not want to confirm each invoice; at the end of each quarter he only answers whether anything is missing, and then gets the import files.

## What Changes

- An automatic mode in the skill (local mode only): registers every PDF in the shared inbox without a confirmation per invoice, with fixed rules (issued when the issuer is the user; received `eu-services` when the supplier has a non-Spanish EU prefix and charges no VAT, `domestic` otherwise), and generates the quarter's files without questions.
- Scheduled routines outside this repo (in the user's setup): a monthly run that registers and, before a filing month, asks the user whether anything is missing; a daily run that generates the files once the user answers.

## Capabilities

### New Capabilities

- `auto-mode`: unattended registration and generation, on the user's standing choice.

### Modified Capabilities

None.

## Impact

- SKILL.md only; scripts unchanged. Nothing is ever filed.

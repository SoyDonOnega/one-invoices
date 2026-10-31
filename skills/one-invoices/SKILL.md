---
name: one-invoices
description: >-
  Registers a Spanish freelancer's issued and received invoices from their PDFs and generates
  the AEAT import files for models 303, 349 and 390 with a summary by box. Never files anything.
  Use when the user runs /one-invoices add <pdf> or /one-invoices 303 <year> <quarter>.
license: MIT
compatibility: Requires Python 3.12 and pdftotext (poppler).
argument-hint: "add <pdf> | 303 <year> <T1-T4>"
disable-model-invocation: true
---

# One Invoices

Keeps the user's invoice register and turns it into the files the AEAT online forms import. It does not issue invoices, file returns or give tax advice: the user reviews every row and files every return.
Paths in this file are relative to the skill root (the folder that contains this SKILL.md).

## When invoked

1. Read the configuration in `skill-data/one-invoices/config.json` (next to the skills folder). If it is missing or a field is empty, copy `data/config.json` there, ask the user for the missing values and stop.
2. Not implemented yet. Phase 1 (`add` and `303`) is specified in the repo's `openspec/changes/add-303-generation/`. Tell the user and stop.

## Rules

- Never file or submit anything to the AEAT. The output is a file the user imports and reviews.
- Never add a row to the register without the user's confirmation.
- Never write invoices, the register or generated files inside the skill folder or the repo.
- Answer in the user's language.

## Resources

- `data/config.json` — empty configuration template (NIF, name, PDF folders, register note, output folder).

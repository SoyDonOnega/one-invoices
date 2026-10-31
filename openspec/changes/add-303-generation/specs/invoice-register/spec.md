# Spec Delta

## Purpose

Keep one register of the user's issued and received invoices, readable in the notes app and complete enough to build every return from it.

## ADDED Requirements

### Requirement: Register location and format
The register SHALL be the folder named in the configuration (`register_dir`), with one Markdown note per invoice named `YYYY-MM_<party>_<number>.md`. The invoice fields SHALL be the note's properties, with `register` set to `issued` or `received`. A view in the notes app (Obsidian Bases) shows them as two tables. (Changed by `register-as-notes`: it was two tables in one note.)

#### Scenario: Note broken by hand
- **WHEN** a note in the register folder has no properties block or misses a field
- **THEN** every command stops and names the note

#### Scenario: Other notes in the folder
- **WHEN** a note in the folder has a `register` value other than issued or received
- **THEN** it is ignored

### Requirement: Issued invoice fields
Each issued invoice row SHALL hold: number, issue date, client name, client tax ID, taxable base, VAT rate, VAT amount, income tax withheld, total, and the PDF link.

#### Scenario: Totals do not add up
- **WHEN** base + VAT − withholding differs from the total by more than 0.01 EUR
- **THEN** the row is rejected with the three figures shown

### Requirement: Received invoice fields
Each received invoice row SHALL hold: number, issue date, supplier name, supplier tax ID, supplier country, kind (domestic, EU services with reverse charge, investment good, not deductible), taxable base, VAT rate, VAT amount, total, and the PDF link.

#### Scenario: EU service with reverse charge
- **WHEN** a received invoice has kind "EU services with reverse charge"
- **THEN** its VAT amount is the base times the Spanish rate computed by the tool, and the invoice's own VAT (zero) is kept as printed

### Requirement: No silent edits
The tool SHALL only create new invoice notes; it SHALL never change or delete an existing one.

#### Scenario: Duplicate invoice
- **WHEN** a row with the same number and tax ID already exists
- **THEN** the tool refuses to add it and points to the existing row

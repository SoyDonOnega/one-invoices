# Spec Delta

## Purpose

Keep one register of the user's issued and received invoices, readable in the notes app and complete enough to build every return from it.

## ADDED Requirements

### Requirement: Register location and format
The register SHALL live in the Markdown note named in the configuration (`register_note`), as two tables: issued invoices and received invoices. Each table SHALL have a fixed header that the tool writes once and checks before every write.

#### Scenario: Missing table
- **WHEN** the configured note has no received-invoices table
- **THEN** the tool adds the table with its fixed header and leaves the rest of the note unchanged

#### Scenario: Header changed by hand
- **WHEN** a table header does not match the fixed header
- **THEN** the tool refuses to write and names the column that differs

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
The tool SHALL only append rows; it SHALL never change or delete an existing row.

#### Scenario: Duplicate invoice
- **WHEN** a row with the same number and tax ID already exists
- **THEN** the tool refuses to add it and points to the existing row

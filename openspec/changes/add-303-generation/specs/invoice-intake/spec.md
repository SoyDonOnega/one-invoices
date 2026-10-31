# Spec Delta

## Purpose

Turn an invoice PDF into a proposed register row that the user reviews before anything is written.

## ADDED Requirements

### Requirement: Read the PDF
The tool SHALL extract the PDF text and propose every register field, marking each field it could not read.

#### Scenario: Scanned PDF without text
- **WHEN** the PDF has no extractable text
- **THEN** the tool says so and asks the user for the fields instead of guessing

### Requirement: PDFs from anywhere, one or many
The tool SHALL accept one or more PDFs from any folder (argument, mention or file dropped in the chat) and, with none given, SHALL offer the PDFs changed in the last 14 days in the inbox folder (default `~/Downloads`).

#### Scenario: Several PDFs dropped in the chat
- **WHEN** the user drops three PDFs into the chat with `add`
- **THEN** the tool proposes three rows in one table and the user confirms all, some or none

### Requirement: Issued or received
The tool SHALL propose issued when the issuer's tax ID is the user's NIF (self-billing included) and received otherwise; the user confirms.

#### Scenario: Self-bill
- **WHEN** the PDF is a self-bill issued by the client in the user's name
- **THEN** the tool proposes it as issued

### Requirement: Filing the PDF
After confirmation the tool SHALL move the PDF into `issued_pdfs` or `received_pdfs` as `YYYY-MM_<party>_<number>.pdf` and link the row to it. It SHALL NOT overwrite a file, and SHALL move nothing when the row is refused.

#### Scenario: Row refused
- **WHEN** the row fails a check (totals, duplicate)
- **THEN** the PDF stays where it was and nothing is written

### Requirement: Confirmation before writing
The tool SHALL show the proposed row and write it only after the user confirms, applying any correction the user gives.

#### Scenario: User corrects a field
- **WHEN** the user changes the VAT rate in the proposal
- **THEN** the row is re-validated with the new rate before it is written

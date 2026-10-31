# Spec Delta

## Purpose

Turn an invoice PDF into a proposed register row that the user reviews before anything is written.

## ADDED Requirements

### Requirement: Read the PDF
The tool SHALL extract the PDF text and propose every register field, marking each field it could not read.

#### Scenario: Scanned PDF without text
- **WHEN** the PDF has no extractable text
- **THEN** the tool says so and asks the user for the fields instead of guessing

### Requirement: Issued or received
The tool SHALL decide whether the invoice is issued or received from the folder it sits in (`issued_pdfs` or `received_pdfs`) and SHALL refuse a PDF outside both folders.

#### Scenario: PDF elsewhere
- **WHEN** the user passes a PDF from another folder
- **THEN** the tool asks the user to move it to the issued or received folder first

### Requirement: Confirmation before writing
The tool SHALL show the proposed row and write it only after the user confirms, applying any correction the user gives.

#### Scenario: User corrects a field
- **WHEN** the user changes the VAT rate in the proposal
- **THEN** the row is re-validated with the new rate before it is written

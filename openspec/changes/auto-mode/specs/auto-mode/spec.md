# Spec Delta

## Purpose

Register invoices and generate the return files without a confirmation per invoice, when the user has chosen it in advance.

## ADDED Requirements

### Requirement: Fixed classification
In automatic mode the tool SHALL classify with fixed rules and SHALL NOT use `investment` or `not-deductible`: issued when the issuer's tax ID is the user's; received `eu-services` when the supplier's tax ID has an EU prefix other than ES and no VAT is charged; received `domestic` otherwise.

#### Scenario: Spanish supplier
- **WHEN** a received invoice from a supplier with a Spanish tax ID is in the shared inbox
- **THEN** it is registered as `domestic` without asking

### Requirement: Checks still apply
In automatic mode every check of the interactive mode SHALL still run; a refused or unreadable PDF SHALL stay in the shared inbox and be listed in the report.

#### Scenario: Totals do not add up
- **WHEN** an invoice's base, VAT and total do not add up
- **THEN** nothing is written and the PDF stays in the inbox, named in the report

### Requirement: Generation on request
In automatic mode the tool SHALL generate the period's files only when asked for that period, and SHALL never file anything.

#### Scenario: Quarter closed
- **WHEN** the routine asks for the files of a closed quarter
- **THEN** the tool registers what is pending, writes the 303 (and the 349 with EU operations, and the 390 for Q4) and reports each result

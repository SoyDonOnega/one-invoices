# Spec Delta

## Purpose

Produce, from the register, the model 303 file that the AEAT online form imports for one quarter, and a summary the user can check box by box.

## ADDED Requirements

### Requirement: Official record design
The file SHALL follow the AEAT record design for model 303 of the return's year (2026: `DR303e26v101`), taken from a machine-readable copy that records the source URL and version. A year without a design copy SHALL be refused.

#### Scenario: Year without design
- **WHEN** the user asks for the 303 of a year with no design copy
- **THEN** the tool refuses and names the design file to download from the AEAT site

### Requirement: Figures from the register
Box amounts SHALL be computed only from register rows whose issue date falls in the quarter: output VAT from issued invoices by rate, reverse-charge VAT from EU services (both payable and deductible), deductible VAT from domestic received invoices and investment goods. Rows of kind "not deductible" SHALL not count.

#### Scenario: Quarter with no rows
- **WHEN** the quarter has no register rows
- **THEN** the tool still generates a zero return and says so in the summary

### Requirement: Byte-for-byte match with the AEAT export
For the same figures, the generated file SHALL be identical to the file the AEAT online form exports.

#### Scenario: Golden file
- **WHEN** the test suite runs with the figures of a file exported from the AEAT site
- **THEN** the generated file equals the exported file byte for byte

### Requirement: Output files
The tool SHALL write `<output_dir>/303/<year>-T<n>.txt` and `<year>-T<n>.md`. The summary SHALL list each non-zero box with its amount and the register rows behind it.

#### Scenario: File already exists
- **WHEN** the output file for the quarter already exists
- **THEN** the tool asks before overwriting it

### Requirement: Never file
The tool SHALL NOT submit, sign or file anything with the AEAT.

#### Scenario: User asks to file
- **WHEN** the user asks the tool to file the return
- **THEN** the tool explains that the user imports the file in the AEAT site, reviews it and files it there

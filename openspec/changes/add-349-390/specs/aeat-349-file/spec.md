# Spec Delta

## Purpose

Produce, from the register, the model 349 file for one quarter and a summary by EU operator.

## ADDED Requirements

### Requirement: Official record design
The file SHALL follow the AEAT record design for model 349 (`DR_Anexo_349.pdf`), taken from a machine-readable copy that records the source URL and the PDF page of each field.

#### Scenario: Record length
- **WHEN** the file is generated
- **THEN** every record is 500 positions long, with one type 1 record first and type 2 records after it

### Requirement: Operators from the register
Type 2 records SHALL be built only from register rows of the quarter with EU operations: received `eu-services` rows with key `I`, issued rows to EU clients without VAT with key `S`. Rows SHALL be summed per operator tax ID and key.

#### Scenario: Two invoices from one supplier
- **WHEN** the quarter has two `eu-services` invoices from the same supplier
- **THEN** the file has one type 2 record for that supplier with the sum of both bases

#### Scenario: Tax ID without country code
- **WHEN** an EU row's tax ID does not start with an EU country code
- **THEN** the tool refuses and names the row

### Requirement: Nothing to declare
A quarter with no EU operations SHALL produce no file.

#### Scenario: Quarter without EU operations
- **WHEN** the user asks for the 349 of a quarter with no EU rows
- **THEN** the tool writes nothing and says there is nothing to declare

### Requirement: Byte-for-byte match with the AEAT export
For the same figures, the generated file SHALL be identical to the file the AEAT online form exports.

#### Scenario: Golden file
- **WHEN** the test suite runs with the figures of a 349 file exported from the AEAT site
- **THEN** the generated file equals the exported file byte for byte

### Requirement: Output and filing
The tool SHALL write `<output_dir>/349/<year>-T<n>.txt` and `.md`, ask before overwriting, and SHALL NOT submit anything to the AEAT.

#### Scenario: File already exists
- **WHEN** the output file for the quarter already exists
- **THEN** the tool asks before overwriting it

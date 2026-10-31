# Spec Delta

## Purpose

Produce, from the register, the annual model 390 file and a summary by box.

## ADDED Requirements

### Requirement: Official record design
The file SHALL follow the AEAT record design for model 390 of the year (2026: `dr390e2026`, version 1.00), taken from a machine-readable copy that records the source URL and version. A year or version without a tested copy SHALL be refused.

#### Scenario: Untested version
- **WHEN** the design copy for the year has a version the generator was not tested with
- **THEN** the tool refuses and names the version

### Requirement: Figures from the four quarters
Box amounts SHALL be the sums over the year of the same register rows the 303 uses, with the same mapping by rate and kind.

#### Scenario: Year matches the quarters
- **WHEN** the 390 and the four 303 of a year are generated from the same register
- **THEN** the 390 accrued and deductible totals equal the sums of the 303 boxes [27] and [45]

### Requirement: Identification from the configuration
Page 1 SHALL take surname, first name, main activity, activity code and IAE heading from the configuration; the tool SHALL ask for any that is missing.

#### Scenario: Missing activity
- **WHEN** the configuration has no IAE heading
- **THEN** the tool asks for it, saves it and continues

### Requirement: Byte-for-byte match with the AEAT export
For the same figures, the generated file SHALL be identical to the file the AEAT online form exports.

#### Scenario: Golden file
- **WHEN** the test suite runs with the figures of a 390 file exported from the AEAT site
- **THEN** the generated file equals the exported file byte for byte

### Requirement: Output and filing
The tool SHALL write `<output_dir>/390/<year>.txt` and `.md`, ask before overwriting, and SHALL NOT submit anything to the AEAT.

#### Scenario: File already exists
- **WHEN** the output file for the year already exists
- **THEN** the tool asks before overwriting it

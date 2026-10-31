# Spec Delta

## Purpose

Let the user add invoices and generate return files from an environment with code execution and a Google Drive connector but no local files.

## ADDED Requirements

### Requirement: Working copy
In Drive mode the tool SHALL read the configuration and every register note from Drive into a working folder and run the same scripts as in local mode.

#### Scenario: Connector missing
- **WHEN** the Google Drive connector or code execution is not available
- **THEN** the tool says which one is missing and stops

### Requirement: Create, never overwrite
In Drive mode the tool SHALL only create files (PDF, invoice note, generated files) in the configured folders, and SHALL stop for any file whose name already exists there.

#### Scenario: Note already in Drive
- **WHEN** the note for a confirmed invoice already exists in the register folder
- **THEN** the tool writes nothing for that invoice and says so

### Requirement: Generated files
In Drive mode the generated `.txt` SHALL be uploaded byte for byte (ISO-8859-1) into the model's folder and also offered as a file in the conversation.

#### Scenario: Return generated from the phone
- **WHEN** the user asks for the 303 of a quarter in Drive mode
- **THEN** the `.txt` and `.md` are created in the `303` folder next to the register note and the `.txt` is offered for download

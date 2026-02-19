## ADDED Requirements

### Requirement: .lexibrary/ directory skeleton
`lexi init` SHALL create a `.lexibrary/` directory at the project root containing `config.yaml`, `START_HERE.md`, `HANDOFF.md`, a `concepts/` directory, and a `guardrails/` directory.

#### Scenario: lexi init creates full skeleton
- **WHEN** running `lexi init` in an empty project directory
- **THEN** `.lexibrary/config.yaml`, `.lexibrary/START_HERE.md`, `.lexibrary/HANDOFF.md`, `.lexibrary/concepts/`, and `.lexibrary/guardrails/` all exist

#### Scenario: Empty directories get .gitkeep
- **WHEN** running `lexi init` in a new project
- **THEN** `.lexibrary/concepts/.gitkeep` and `.lexibrary/guardrails/.gitkeep` are created so the directories are tracked by git

#### Scenario: Init is idempotent
- **WHEN** running `lexi init` in a directory that already has `.lexibrary/`
- **THEN** the command succeeds without error and does not overwrite existing files (prints a notice instead)

### Requirement: Mirror tree path construction
The system SHALL compute the mirror path for any source file by replacing the project root prefix with `.lexibrary/` and appending `.md` to files or using the bare directory path for `.aindex` placement.

#### Scenario: Source file maps to design file path
- **WHEN** computing the mirror path for `src/auth/login.py` with project root at `/project`
- **THEN** the design file path is `.lexibrary/src/auth/login.py.md`

#### Scenario: Directory maps to .aindex path
- **WHEN** computing the mirror directory for `src/auth/` with project root at `/project`
- **THEN** the `.aindex` path is `.lexibrary/src/auth/.aindex`

#### Scenario: Nested paths are preserved
- **WHEN** computing the mirror path for `backend/api/v2/users/controller.py`
- **THEN** the design file path is `.lexibrary/backend/api/v2/users/controller.py.md` (full depth preserved)

### Requirement: START_HERE.md placeholder
`lexi init` SHALL write a `START_HERE.md` placeholder that tells agents the library has not been generated yet and instructs them to run `lexi update`.

#### Scenario: Placeholder contains generation instruction
- **WHEN** reading `.lexibrary/START_HERE.md` after `lexi init`
- **THEN** it contains text instructing the reader to run `lexi update` to generate the full library

### Requirement: HANDOFF.md placeholder
`lexi init` SHALL write a `HANDOFF.md` placeholder with the required format fields populated with "No active session" values.

#### Scenario: Placeholder follows required format
- **WHEN** reading `.lexibrary/HANDOFF.md` after `lexi init`
- **THEN** it contains the `# Handoff` heading and all required fields: **Task**, **Status**, **Next step**, **Key files**, **Watch out** with placeholder values

## MODIFIED Requirements

### Requirement: .gitignore is configured
The system SHALL exclude Python artifacts, virtual environments, generated BAML code, and `.lexibrary/` generated artifacts while keeping `.lexibrary/config.yaml` tracked. The `.gitignore` SHALL include a `**/.iwh` pattern for IWH ephemeral files.

#### Scenario: .gitignore contains .lexibrary/ generated file patterns
- **WHEN** reading `.gitignore`
- **THEN** it includes patterns for `.lexibrary/START_HERE.md`, `.lexibrary/**/*.md`, `.lexibrary/**/.aindex`, `**/.iwh`, `baml_client/`, and standard Python patterns (`__pycache__/`, `*.pyc`, `.venv/`, `venv/`)

#### Scenario: .gitignore does NOT contain HANDOFF.md pattern
- **WHEN** reading `.gitignore` after Phase 8c changes
- **THEN** it SHALL NOT contain `.lexibrary/HANDOFF.md` pattern

#### Scenario: .lexibrary/config.yaml is NOT gitignored
- **WHEN** running `git status` in a project with `.lexibrary/config.yaml`
- **THEN** `config.yaml` is tracked (not in .gitignore), because project config is version-controlled

### Requirement: Stack directory in scaffolding
`lexictl init` SHALL create a `.lexibrary/stack/` directory and a `.lexibrary/concepts/` directory in the project skeleton. It SHALL NOT create a `HANDOFF.md` file.

#### Scenario: Init creates stack directory
- **WHEN** running `lexictl init` in an empty directory
- **THEN** `.lexibrary/stack/` SHALL be created

#### Scenario: Init does not create HANDOFF.md
- **WHEN** running `lexictl init` in an empty directory
- **THEN** `.lexibrary/HANDOFF.md` SHALL NOT be created

#### Scenario: Init creates IWH gitignore entry
- **WHEN** running `lexictl init` in an empty directory
- **THEN** `.gitignore` SHALL contain the `**/.iwh` pattern

## MODIFIED Requirements

### Requirement: Init command creates config file
The `lexictl init` command SHALL run the interactive setup wizard to create a `.lexibrary/` directory with a dynamically generated `config.yaml`. It MUST accept a `--defaults` flag that accepts all auto-detected values without prompting (for CI/scripting use).

#### Scenario: Init runs wizard
- **WHEN** running `lexictl init` in a fresh directory
- **THEN** the wizard SHALL run and create `.lexibrary/` with a config derived from wizard answers

#### Scenario: Init with --defaults skips prompts
- **WHEN** running `lexictl init --defaults` in a fresh directory
- **THEN** the wizard SHALL use all detected/default values without prompting and create `.lexibrary/`

#### Scenario: Init fails if already initialized
- **WHEN** running `lexictl init` in a directory that already contains `.lexibrary/`
- **THEN** the command SHALL print an error message pointing to `lexictl setup --update` and exit with code 1

#### Scenario: Init shows creation summary
- **WHEN** `lexictl init` completes successfully
- **THEN** the output SHALL include a count of items created and suggest running `lexictl update`

## ADDED Requirements

### Requirement: Re-init guard
`lexictl init` SHALL check for an existing `.lexibrary/` directory before running the wizard. If found, it SHALL print an error message directing the user to `lexictl setup --update` and exit with code 1.

#### Scenario: Re-init blocked
- **WHEN** running `lexictl init` and `.lexibrary/` already exists
- **THEN** the command SHALL print `"Project already initialised"` and reference `lexictl setup --update`

### Requirement: Non-TTY detection
`lexictl init` SHALL detect when `stdin` is not a TTY. In non-interactive environments without `--defaults`, it SHALL print a message advising the user to use `--defaults` and exit with code 1.

#### Scenario: Non-TTY without --defaults
- **WHEN** `lexictl init` is invoked in a non-TTY environment without `--defaults`
- **THEN** the command SHALL print a message about non-interactive mode and exit with code 1

#### Scenario: Non-TTY with --defaults succeeds
- **WHEN** `lexictl init --defaults` is invoked in a non-TTY environment
- **THEN** the command SHALL proceed normally using defaults

### Requirement: Wizard cancellation exits cleanly
If the user cancels at the wizard summary step, `lexictl init` SHALL exit with code 1 without creating any files.

#### Scenario: User cancels wizard
- **WHEN** the user answers "No" at the wizard summary step
- **THEN** no `.lexibrary/` directory SHALL be created and exit code SHALL be 1

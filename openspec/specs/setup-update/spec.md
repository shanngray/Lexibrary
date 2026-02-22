# setup-update Specification

## Purpose
TBD - created by archiving change init-wizard. Update Purpose after archive.
## Requirements
### Requirement: setup command with --update flag
`lexictl setup` SHALL accept a `--update` boolean flag. When called without `--update`, it SHALL display usage instructions pointing to `lexictl setup --update` and `lexictl init`, then exit with code 0.

#### Scenario: Setup without --update shows usage
- **WHEN** running `lexictl setup` without the `--update` flag
- **THEN** the output SHALL include guidance to use `lexictl setup --update` or `lexictl init`, and exit code SHALL be 0

### Requirement: setup --update requires initialized project
`lexictl setup --update` SHALL require an initialized `.lexibrary/` directory (found via `require_project_root()`). If not found, it SHALL error with a non-zero exit code.

#### Scenario: Setup --update outside project fails
- **WHEN** running `lexictl setup --update` in a directory with no `.lexibrary/`
- **THEN** the command SHALL print an error and exit with a non-zero code

### Requirement: setup --update reads agent_environment from config
`lexictl setup --update` SHALL load the project config and read `agent_environment`. If the list is empty, it SHALL display a message directing the user to run `lexictl init` and exit with code 1.

#### Scenario: No agent environments configured
- **WHEN** running `lexictl setup --update` and `config.agent_environment` is empty
- **THEN** the output SHALL say no agent environments are configured and suggest `lexictl init`, and exit code SHALL be 1

### Requirement: setup --update stub for Phase 8c
In Phase 8b, `lexictl setup --update` SHALL iterate over configured agent environments and print a placeholder message for each indicating that rule generation is not yet implemented.

#### Scenario: Stub output for configured environments
- **WHEN** running `lexictl setup --update` with `agent_environment: ["claude", "cursor"]` in config
- **THEN** the output SHALL list both environments with a message that rule generation is deferred to Phase 8c


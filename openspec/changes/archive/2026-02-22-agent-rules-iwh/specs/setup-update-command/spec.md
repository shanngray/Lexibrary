## ADDED Requirements

### Requirement: Setup command generates rules
The `lexictl setup` command SHALL generate agent environment rules by reading `agent_environment` from persisted project config and calling `generate_rules()` for each configured environment.

#### Scenario: Setup with config-persisted environments
- **WHEN** running `lexictl setup` where config has `agent_environment: ["claude", "cursor"]`
- **THEN** rules SHALL be generated for both Claude Code and Cursor, and a summary of created files SHALL be printed

#### Scenario: Setup with explicit environment argument
- **WHEN** running `lexictl setup claude`
- **THEN** rules SHALL be generated for Claude Code only, regardless of config

#### Scenario: Setup with --update flag
- **WHEN** running `lexictl setup --update`
- **THEN** rules SHALL be regenerated from current templates, updating any existing files

#### Scenario: No environment configured
- **WHEN** running `lexictl setup` where config has no `agent_environment` set
- **THEN** the command SHALL print a warning and exit with code 1

#### Scenario: Unsupported environment
- **WHEN** running `lexictl setup vscode`
- **THEN** the command SHALL print an error listing supported environments and exit with code 1

### Requirement: Setup ensures IWH gitignore
The `lexictl setup` command SHALL call `ensure_iwh_gitignored()` after generating rules, ensuring the `**/.iwh` pattern is in `.gitignore`.

#### Scenario: Gitignore updated on setup
- **WHEN** running `lexictl setup` successfully
- **THEN** `.gitignore` SHALL contain the `**/.iwh` pattern

### Requirement: Setup reports results
The `lexictl setup` command SHALL print a summary showing each environment and the number of files written, with file paths relative to project root.

#### Scenario: Result summary format
- **WHEN** running `lexictl setup` successfully for `["claude"]`
- **THEN** output SHALL include `claude: N files written` followed by relative paths of created files, and a final line like `Installed rules for claude (N files)`

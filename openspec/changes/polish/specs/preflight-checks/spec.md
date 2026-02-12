## ADDED Requirements

### Requirement: Pre-flight validation function
The system SHALL provide a `preflight_check(config, root)` function that returns a list of error message strings. An empty list indicates all checks passed.

#### Scenario: All checks pass
- **WHEN** `preflight_check()` is called with a valid config and writable root directory
- **THEN** it SHALL return an empty list

#### Scenario: Missing API key detected
- **WHEN** the config specifies a non-Ollama provider and no API key is found in config or environment
- **THEN** the returned list SHALL contain a message naming the expected environment variable and suggesting where to set the key

#### Scenario: Ollama provider skips API key check
- **WHEN** the config specifies the `"ollama"` provider
- **THEN** the API key check SHALL be skipped

#### Scenario: Root directory does not exist
- **WHEN** the root path does not point to an existing directory
- **THEN** the returned list SHALL contain a message with the path

#### Scenario: Root directory is not writable
- **WHEN** the root directory exists but is not writable
- **THEN** the returned list SHALL contain a message identifying the directory as not writable

#### Scenario: BAML client not generated
- **WHEN** importing `baml_client` raises `ImportError`
- **THEN** the returned list SHALL contain a message instructing the user to run `uv run baml-cli generate`

### Requirement: Pre-flight checks run before crawl
The `lexi crawl` command SHALL run `preflight_check()` before starting any crawl work. If any errors are returned, the command SHALL display all errors and exit with a non-zero code without performing any crawl operations.

#### Scenario: Crawl aborted on pre-flight failure
- **WHEN** `lexi crawl` is invoked and `preflight_check()` returns errors
- **THEN** the CLI SHALL print each error using Rich formatting and exit with code 1 before any LLM calls or file writes occur

#### Scenario: Crawl proceeds on pre-flight success
- **WHEN** `lexi crawl` is invoked and `preflight_check()` returns an empty list
- **THEN** the crawl SHALL proceed normally

### Requirement: Pre-flight checks run before daemon
The `lexi daemon` command SHALL run `preflight_check()` before starting the daemon. If any errors are returned, the command SHALL display all errors and exit with a non-zero code.

#### Scenario: Daemon aborted on pre-flight failure
- **WHEN** `lexi daemon` is invoked and `preflight_check()` returns errors
- **THEN** the CLI SHALL print each error and exit with code 1 before starting the watcher or scheduler

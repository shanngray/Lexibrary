## MODIFIED Requirements

### Requirement: Crawl command
The system SHALL provide a `crawl` command that takes a path argument (default "."), a `--verbose` flag for debug logging, `--full` for forced re-crawl, and `--dry-run` for preview mode. The crawl command SHALL wrap its core logic in a try/except block that catches `LexibrarianError` subclasses and prints user-friendly error messages via Rich console without tracebacks, then exits with code 1.

#### Scenario: Crawl command accepts path argument
- **WHEN** running `lexi crawl /some/path`
- **THEN** the command executes without error and prints a placeholder message

#### Scenario: Crawl command defaults to current directory
- **WHEN** running `lexi crawl` with no path argument
- **THEN** the command executes with path="."

#### Scenario: Crawl command has help text
- **WHEN** running `lexi crawl --help`
- **THEN** the help text says "Run the Lexibrarian crawler."

#### Scenario: Crawl displays user-friendly error for LexibrarianError
- **WHEN** the crawl operation raises a `LexibrarianError` subclass
- **THEN** the CLI SHALL print the error message with `[red]Error:[/red]` prefix and exit with code 1 without showing a traceback

#### Scenario: Crawl shows traceback for unexpected errors
- **WHEN** the crawl operation raises an exception that is not a `LexibrarianError` subclass
- **THEN** the full traceback SHALL be shown for debugging

### Requirement: Daemon command
The system SHALL provide a `daemon` command that takes a path argument (default ".") and a `--foreground` flag. The daemon command SHALL wrap its core logic in a try/except block that catches `LexibrarianError` subclasses and prints user-friendly error messages.

#### Scenario: Daemon command accepts path argument
- **WHEN** running `lexi daemon /some/path`
- **THEN** the command executes without error and prints a placeholder message

#### Scenario: Daemon command defaults to current directory
- **WHEN** running `lexi daemon` with no path argument
- **THEN** the command executes with path="."

#### Scenario: Daemon command has help text
- **WHEN** running `lexi daemon --help`
- **THEN** the help text says "Start the background daemon."

#### Scenario: Daemon displays user-friendly error for LexibrarianError
- **WHEN** the daemon operation raises a `LexibrarianError` subclass
- **THEN** the CLI SHALL print the error message with `[red]Error:[/red]` prefix and exit with code 1 without showing a traceback

## ADDED Requirements

### Requirement: Verbose flag configures logging
The `--verbose` flag on `lexi crawl` SHALL configure logging to DEBUG level via `setup_logging(verbose=True)`. Without the flag, the default level SHALL be INFO.

#### Scenario: Verbose flag enables debug output
- **WHEN** running `lexi crawl --verbose`
- **THEN** `setup_logging()` SHALL be called with `verbose=True` and DEBUG-level log messages SHALL appear on the console

#### Scenario: Default logging is INFO level
- **WHEN** running `lexi crawl` without `--verbose`
- **THEN** `setup_logging()` SHALL be called with `verbose=False` and only INFO-level and above messages SHALL appear

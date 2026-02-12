## ADDED Requirements

### Requirement: Custom exception hierarchy
The system SHALL define a base `LexibrarianError` exception class in `utils/errors.py` with three direct subclasses: `ConfigError` for configuration-related errors, `CrawlError` for crawl/filesystem-related errors, and `LLMError` for LLM service-related errors.

#### Scenario: Base exception exists
- **WHEN** importing `from lexibrarian.utils.errors import LexibrarianError`
- **THEN** `LexibrarianError` SHALL be a subclass of `Exception`

#### Scenario: Subclasses are importable
- **WHEN** importing `from lexibrarian.utils.errors import ConfigError, CrawlError, LLMError`
- **THEN** each SHALL be a direct subclass of `LexibrarianError`

#### Scenario: Exceptions carry descriptive messages
- **WHEN** raising `ConfigError("Missing API key for provider 'anthropic'")`
- **THEN** `str(e)` SHALL return `"Missing API key for provider 'anthropic'"`

### Requirement: Network error handling in LLM service
The `LLMService` SHALL catch network-related exceptions from LLM API calls and either return fallback summaries or raise `LLMError` depending on recoverability.

#### Scenario: API timeout returns fallback summary
- **WHEN** an LLM call raises a timeout exception
- **THEN** the service SHALL log a warning and return a `FileSummaryResult` with summary `"Summary unavailable (timeout)"`

#### Scenario: Rate limit triggers backoff and retry
- **WHEN** an LLM call receives a 429 rate limit response
- **THEN** the service SHALL log a warning, back off, retry once, and return a fallback summary if the retry also fails

#### Scenario: Auth error raises LLMError
- **WHEN** an LLM call receives a 401 or 403 response
- **THEN** the service SHALL raise `LLMError` with a message containing "Check your API key" and SHALL NOT retry

#### Scenario: Network unreachable returns fallback summary
- **WHEN** an LLM call fails due to network connectivity
- **THEN** the service SHALL log a warning and return a `FileSummaryResult` with summary `"Summary unavailable (network error)"`

#### Scenario: Malformed LLM response returns fallback summary
- **WHEN** BAML fails to parse the LLM response
- **THEN** the service SHALL log a warning and return a `FileSummaryResult` with summary `"Summary unavailable (parse error)"`

### Requirement: File system error handling in crawler
The crawler SHALL catch file system exceptions and skip affected files or directories gracefully, logging warnings for each skipped item.

#### Scenario: Permission denied on file
- **WHEN** a file cannot be read due to permission denial
- **THEN** the crawler SHALL skip the file, log a warning, and list it in `.aindex` with description `"Permission denied"`

#### Scenario: Permission denied on directory
- **WHEN** a directory cannot be accessed due to permission denial
- **THEN** the crawler SHALL skip the entire directory and log a warning

#### Scenario: File deleted during crawl
- **WHEN** a file is deleted between discovery and read
- **THEN** the crawler SHALL catch `FileNotFoundError`, skip the file, and log a warning

#### Scenario: Disk full on write
- **WHEN** writing a `.aindex` file fails due to disk full (`OSError`)
- **THEN** the crawler SHALL log an error and continue processing other directories

#### Scenario: Broken symlink encountered
- **WHEN** `stat()` fails on a symlink target
- **THEN** the crawler SHALL skip the file and log a debug message

### Requirement: Config error handling
The config loader SHALL catch parsing errors and raise `ConfigError` with user-friendly messages.

#### Scenario: Invalid TOML syntax
- **WHEN** `lexibrary.toml` contains invalid TOML syntax
- **THEN** the loader SHALL raise `ConfigError` with a message containing the parse error details

#### Scenario: Invalid config field values
- **WHEN** `lexibrary.toml` contains values that fail Pydantic validation
- **THEN** the loader SHALL raise `ConfigError` with a message identifying the invalid field

#### Scenario: Unknown LLM provider
- **WHEN** the config specifies an unrecognized LLM provider
- **THEN** the factory SHALL raise `ConfigError` with a message listing valid providers

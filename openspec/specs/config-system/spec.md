# config-system Specification

## Purpose
TBD - created by archiving change phase-1-foundation. Update Purpose after archive.
## Requirements
### Requirement: Config schema with defaults
The system SHALL define a nested Pydantic model hierarchy (LexibraryConfig, LLMConfig, TokenizerConfig, CrawlConfig, IgnoreConfig, DaemonConfig, OutputConfig) with sensible defaults for all settings.

#### Scenario: Default LLM config uses Anthropic
- **WHEN** creating a default LLMConfig
- **THEN** it has provider="anthropic", model="claude-sonnet-4-5-20250514", api_key_env="ANTHROPIC_API_KEY", max_retries=3, timeout=60

#### Scenario: Default crawl config has reasonable limits
- **WHEN** creating a default CrawlConfig
- **THEN** it has max_file_size_kb=512, max_files_per_llm_batch=10, summary_max_tokens=80, dir_summary_max_tokens=150

#### Scenario: Default ignore config includes .aindex and node_modules
- **WHEN** creating a default IgnoreConfig
- **THEN** it has use_gitignore=true, additional_patterns includes ".aindex", "lexibrary.toml", "node_modules/", "__pycache__/", ".git/", ".venv/", "venv/", "*.lock"

#### Scenario: Pydantic validates the entire config
- **WHEN** creating a LexibraryConfig with all sub-configs
- **THEN** all sub-configs (LLMConfig, TokenizerConfig, etc.) are validated and accessible as attributes

### Requirement: Config file discovery
The system SHALL search for `lexibrary.toml` starting from a given directory and walking upward to parent directories until found or root is reached.

#### Scenario: Config file is found in current directory
- **WHEN** calling `find_config_file()` from a directory containing `lexibrary.toml`
- **THEN** it returns the path to that `lexibrary.toml`

#### Scenario: Config file is found in a parent directory
- **WHEN** calling `find_config_file()` from a subdirectory without `lexibrary.toml` but whose parent contains it
- **THEN** it walks upward and returns the parent's `lexibrary.toml`

#### Scenario: Config file is not found
- **WHEN** calling `find_config_file()` from a directory tree with no `lexibrary.toml`
- **THEN** it returns None

### Requirement: Config loading and validation
The system SHALL load TOML files, validate against the schema, and return a LexibraryConfig object. If no file is found, return all defaults.

#### Scenario: Config is loaded from file
- **WHEN** calling `load_config(path_to_lexibrary_toml)`
- **THEN** it parses the TOML file and returns a LexibraryConfig with values from the file

#### Scenario: Invalid TOML raises ValidationError
- **WHEN** calling `load_config()` with a TOML file containing invalid values (e.g., max_file_size_kb as string)
- **THEN** Pydantic raises a ValidationError

#### Scenario: Missing config file returns defaults
- **WHEN** calling `load_config()` with no file found
- **THEN** it returns a LexibraryConfig with all default values

#### Scenario: Partial config merges with defaults
- **WHEN** calling `load_config()` with a TOML file that only specifies some fields (e.g., LLM provider)
- **THEN** unspecified fields use defaults and the resulting config is fully valid

### Requirement: Config template for initialization
The system SHALL provide a DEFAULT_CONFIG_TEMPLATE string that serves as a starter `lexibrary.toml` with all sections, sensible defaults, and explanatory comments.

#### Scenario: Template contains all config sections
- **WHEN** reading the DEFAULT_CONFIG_TEMPLATE
- **THEN** it includes sections for [llm], [tokenizer], [crawl], [ignore], [daemon], [output] with defaults and inline comments explaining each field

### Requirement: Crawl configuration
The `CrawlConfig` model SHALL include a `binary_extensions` field containing a set of file extensions (with leading dot) that are known binary formats. These extensions SHALL be used by the directory discovery module to skip files without reading them.

The field SHALL default to a comprehensive list of common binary extensions including image formats (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.ico`, `.svg`, `.webp`), audio/video (`.mp3`, `.wav`, `.mp4`, `.avi`, `.mov`), archives (`.zip`, `.tar`, `.gz`, `.bz2`, `.7z`, `.rar`), compiled (`.pyc`, `.pyo`, `.so`, `.dll`, `.dylib`, `.o`, `.a`, `.class`, `.jar`, `.wasm`), fonts (`.woff`, `.woff2`, `.ttf`, `.otf`, `.eot`), and other binary formats (`.pdf`, `.exe`, `.bin`, `.dat`, `.db`, `.sqlite`).

#### Scenario: Default binary extensions include common formats
- **WHEN** a `CrawlConfig` is created with default values
- **THEN** `binary_extensions` SHALL contain at least `.png`, `.jpg`, `.pyc`, `.zip`, `.exe`, `.pdf`

#### Scenario: Custom binary extensions override defaults
- **WHEN** a user specifies `binary_extensions` in `lexibrary.toml`
- **THEN** the configured list SHALL be used instead of defaults


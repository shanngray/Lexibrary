# config-system Specification

## Purpose
TBD - created by archiving change phase-1-foundation. Update Purpose after archive.
## Requirements
### Requirement: Config schema with defaults
Nested Pydantic model hierarchy (LexibraryConfig, LLMConfig, TokenizerConfig, CrawlConfig, IgnoreConfig, DaemonConfig, OutputConfig, ASTConfig) with sensible defaults. `LexibraryConfig` SHALL include a `scope_root: str` field (default: `"."`) specifying which files get design files — relative to project root. `CrawlConfig` SHALL include a `max_file_size_kb: int` field (default: `512`) — files exceeding this size are skipped during `update_project` with a log warning.

#### Scenario: Default scope_root
- **WHEN** config is loaded without a `scope_root` field
- **THEN** `scope_root` SHALL default to `"."`

#### Scenario: Custom scope_root
- **WHEN** config contains `scope_root: "src/"`
- **THEN** `LexibraryConfig.scope_root` SHALL be `"src/"`

#### Scenario: Default max_file_size_kb
- **WHEN** config is loaded without `crawl.max_file_size_kb`
- **THEN** `CrawlConfig.max_file_size_kb` SHALL default to `512`

#### Scenario: Large file skipped
- **WHEN** a file exceeds `max_file_size_kb` during `update_project`
- **THEN** the file SHALL be skipped with a log warning

### Requirement: Config file discovery
The system SHALL search for the project config at `.lexibrary/config.yaml` relative to the project root (found via `find_project_root()`). The global config SHALL be read from `~/.config/lexibrarian/config.yaml` (XDG base directory).

#### Scenario: Project config file is found via project root
- **WHEN** calling `load_config()` from a directory whose project root contains `.lexibrary/config.yaml`
- **THEN** it loads and returns the project config merged over the global config

#### Scenario: Global config is read from XDG path
- **WHEN** `~/.config/lexibrarian/config.yaml` exists and `.lexibrary/config.yaml` does not
- **THEN** the global config is loaded as-is with all defaults applied

#### Scenario: Neither config file exists
- **WHEN** no global config and no project config exist
- **THEN** `load_config()` returns a `LexibraryConfig` with all defaults

### Requirement: Config loading and validation
The system SHALL load YAML files via PyYAML, validate against the Pydantic schema, and return a `LexibraryConfig`. Two-tier merge: load global → load project → merge with project values taking precedence.

#### Scenario: Config is loaded from YAML file
- **WHEN** calling `load_config()` with a valid `.lexibrary/config.yaml`
- **THEN** it parses the YAML and returns a `LexibraryConfig` with values from the file

#### Scenario: Invalid YAML raises ValidationError
- **WHEN** calling `load_config()` with a YAML file containing type-mismatched values (e.g., timeout as string)
- **THEN** Pydantic raises a `ValidationError`

#### Scenario: Project config overrides global config
- **WHEN** global config sets `llm.model = "claude-opus-4-6"` and project config sets `llm.model = "claude-haiku-4-5-20251001"`
- **THEN** the merged config has `llm.model == "claude-haiku-4-5-20251001"`

#### Scenario: Partial project config merges with global defaults
- **WHEN** the project config only specifies `llm.provider = "anthropic"` and global config provides all other fields
- **THEN** the merged config has the project's LLM provider and global defaults for all other fields

### Requirement: Config template for initialization
DEFAULT_CONFIG_TEMPLATE string SHALL include the new `scope_root` and `crawl.max_file_size_kb` fields with defaults and explanatory comments.

#### Scenario: Template includes scope_root
- **WHEN** the config template is rendered
- **THEN** it SHALL contain `scope_root: "."` with a comment explaining its purpose

#### Scenario: Template includes max_file_size_kb
- **WHEN** the config template is rendered
- **THEN** it SHALL contain `max_file_size_kb: 512` under the crawl section

### Requirement: Mapping strategy config stub
The system SHALL define a `MappingConfig` Pydantic model with a `strategies` field (list of mapping rules, default empty list). The mapping strategies are not evaluated in Phase 1; the model stub locks in the YAML key name so Phase 4 can populate it without breaking existing project configs.

#### Scenario: MappingConfig accepts empty strategies list
- **WHEN** creating a `MappingConfig` with no arguments
- **THEN** `mapping_config.strategies` returns an empty list

#### Scenario: MappingConfig stub does not raise on unknown strategy entries
- **WHEN** loading a project config with a populated `mapping.strategies` list
- **THEN** the config loads without error (entries stored as raw dicts until Phase 4 defines the strategy models)

### Requirement: CrawlConfig with binary extensions
The `CrawlConfig` Pydantic model in `src/lexibrarian/config/schema.py` SHALL include a `binary_extensions: list[str]` field containing file extensions (with leading dot) that are treated as binary. Files with these extensions SHALL be described as `"Binary file (.ext)"` by the index generator rather than having their lines counted.

The field SHALL default to a comprehensive list covering: image formats (`.png`, `.jpg`, `.jpeg`, `.gif`, `.ico`, `.svg`, `.webp`), audio/video (`.mp3`, `.mp4`, `.wav`, `.ogg`, `.webm`), fonts (`.woff`, `.woff2`, `.ttf`, `.eot`), archives (`.zip`, `.tar`, `.gz`, `.bz2`, `.7z`, `.rar`), documents (`.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`), executables/compiled (`.exe`, `.dll`, `.so`, `.dylib`, `.pyc`, `.pyo`, `.class`, `.o`, `.obj`), and database (`.sqlite`, `.db`).

`CrawlConfig` SHALL also be wired into `LexibraryConfig` as `crawl: CrawlConfig = Field(default_factory=CrawlConfig)`.

#### Scenario: CrawlConfig added to LexibraryConfig
- **WHEN** a default `LexibraryConfig` is created
- **THEN** it SHALL have a `crawl` attribute that is a `CrawlConfig` instance

#### Scenario: Default binary extensions include common formats
- **WHEN** a `CrawlConfig` is created with default values
- **THEN** `binary_extensions` SHALL contain at least `.png`, `.jpg`, `.pyc`, `.zip`, `.exe`, `.pdf`, `.mp4`

#### Scenario: Custom binary extensions override defaults
- **WHEN** `LexibraryConfig` is loaded from a config file specifying `crawl.binary_extensions`
- **THEN** `config.crawl.binary_extensions` SHALL contain only the configured values

#### Scenario: CrawlConfig tolerates extra fields
- **WHEN** a `CrawlConfig` is created with an unknown extra field
- **THEN** the extra field SHALL be ignored (not raise a validation error)


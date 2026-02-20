## MODIFIED Requirements

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

### Requirement: Config template for initialization
DEFAULT_CONFIG_TEMPLATE string SHALL include the new `scope_root` and `crawl.max_file_size_kb` fields with defaults and explanatory comments.

#### Scenario: Template includes scope_root
- **WHEN** the config template is rendered
- **THEN** it SHALL contain `scope_root: "."` with a comment explaining its purpose

#### Scenario: Template includes max_file_size_kb
- **WHEN** the config template is rendered
- **THEN** it SHALL contain `max_file_size_kb: 512` under the crawl section

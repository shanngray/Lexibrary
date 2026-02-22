## MODIFIED Requirements

### Requirement: Config schema with defaults
Nested Pydantic model hierarchy (LexibraryConfig, LLMConfig, TokenizerConfig, CrawlConfig, IgnoreConfig, DaemonConfig, OutputConfig, ASTConfig) with sensible defaults. `LexibraryConfig` SHALL include a `scope_root: str` field (default: `"."`) specifying which files get design files — relative to project root. `CrawlConfig` SHALL include a `max_file_size_kb: int` field (default: `512`) — files exceeding this size are skipped during `update_project` with a log warning. `TokenBudgetConfig` SHALL NOT include a `handoff_tokens` field (removed — HANDOFF.md replaced by IWH).

#### Scenario: Default scope_root
- **WHEN** config is loaded without a `scope_root` field
- **THEN** `scope_root` SHALL default to `"."`

#### Scenario: Custom scope_root
- **WHEN** config contains `scope_root: "src/"`
- **THEN** `LexibraryConfig.scope_root` SHALL be `"src/"`

#### Scenario: Default max_file_size_kb
- **WHEN** config is loaded without `crawl.max_file_size_kb`
- **THEN** `CrawlConfig.max_file_size_kb` SHALL default to `512`

#### Scenario: No handoff_tokens in TokenBudgetConfig
- **WHEN** creating a default `TokenBudgetConfig`
- **THEN** the model SHALL NOT have a `handoff_tokens` attribute

#### Scenario: Stale handoff_tokens silently ignored
- **WHEN** loading a config YAML that contains `token_budgets.handoff_tokens: 100`
- **THEN** the config SHALL load without error (Pydantic `extra="ignore"` handles stale keys)

### Requirement: Config template for initialization
DEFAULT_CONFIG_TEMPLATE string SHALL NOT include `handoff_tokens` in the `token_budgets` section. The template SHALL include all other existing token budget fields.

#### Scenario: Template does not include handoff_tokens
- **WHEN** the config template is rendered
- **THEN** it SHALL NOT contain `handoff_tokens`

#### Scenario: Template includes remaining token budgets
- **WHEN** the config template is rendered
- **THEN** it SHALL contain `start_here_tokens`, `design_file_tokens`, `design_file_abridged_tokens`, `aindex_tokens`, and `concept_file_tokens`

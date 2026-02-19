## MODIFIED Requirements

### Requirement: Config schema with defaults
The system SHALL define a nested Pydantic model hierarchy (LexibraryConfig, LLMConfig, TokenizerConfig, CrawlConfig, IgnoreConfig, DaemonConfig, OutputConfig, ASTConfig) with sensible defaults for all settings.

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
- **THEN** all sub-configs (LLMConfig, TokenizerConfig, ASTConfig, etc.) are validated and accessible as attributes

#### Scenario: Default AST config enables all supported languages
- **WHEN** creating a default ASTConfig
- **THEN** it has enabled=True and languages=["python", "typescript", "javascript"]

#### Scenario: AST config can be disabled
- **WHEN** creating an ASTConfig with enabled=False
- **THEN** the enabled field is False and the model validates

#### Scenario: AST config can restrict languages
- **WHEN** creating an ASTConfig with languages=["python"]
- **THEN** only "python" is in the languages list

### Requirement: Config template for initialization
The system SHALL provide a DEFAULT_CONFIG_TEMPLATE string that serves as a starter `lexibrary.toml` with all sections, sensible defaults, and explanatory comments.

#### Scenario: Template contains all config sections
- **WHEN** reading the DEFAULT_CONFIG_TEMPLATE
- **THEN** it includes sections for [llm], [tokenizer], [crawl], [ignore], [daemon], [output], [ast] with defaults and inline comments explaining each field

#### Scenario: Template includes AST section
- **WHEN** reading the DEFAULT_CONFIG_TEMPLATE
- **THEN** it includes an [ast] section with enabled=true and languages list containing python, typescript, javascript

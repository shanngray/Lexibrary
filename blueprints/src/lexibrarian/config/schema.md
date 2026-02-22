# config/schema

**Summary:** Pydantic 2 models for the full Lexibrarian configuration hierarchy, validated from `.lexibrary/config.yaml`.

## Interface

| Name | Key Fields | Purpose |
| --- | --- | --- |
| `CrawlConfig` | `max_file_size_kb: int = 512`, `binary_extensions: list[str]` | Crawl behaviour -- file types to treat as binary and size limits |
| `TokenizerConfig` | `backend`, `model`, `max_tokens_per_chunk` | Tokenizer backend selection |
| `LLMConfig` | `provider`, `model`, `api_key_env`, `max_retries`, `timeout` | LLM provider settings |
| `TokenBudgetConfig` | `start_here_tokens`, `design_file_tokens`, `design_file_abridged_tokens`, `aindex_tokens`, `concept_file_tokens` | Per-artifact token budgets |
| `MappingConfig` | `strategies: list[dict]` | Mapping strategy config (stub for Phase 1) |
| `IgnoreConfig` | `use_gitignore: bool`, `additional_patterns: list[str]` | Ignore pattern settings |
| `DaemonConfig` | `sweep_interval_seconds: int = 3600`, `sweep_skip_if_unchanged`, `git_suppression_seconds`, `watchdog_enabled: bool = False`, `debounce_seconds` | Daemon and scheduled sweep settings |
| `ASTConfig` | `enabled: bool`, `languages: list[str]` | AST-based interface extraction settings |
| `IWHConfig` | `enabled: bool = True` | I Was Here (IWH) agent trace configuration |
| `LexibraryConfig` | `scope_root`, `project_name`, `agent_environment`, `iwh`, `llm`, `token_budgets`, `mapping`, `ignore`, `daemon`, `crawl`, `ast` | Top-level config container |

## Dependencies

- None (only pydantic)

## Dependents

- `lexibrarian.config.loader` -- validates merged YAML into `LexibraryConfig`
- `lexibrarian.config.__init__` -- re-exports all models
- `lexibrarian.ignore.patterns` -- consumes `IgnoreConfig`
- `lexibrarian.llm.factory` -- consumes `LLMConfig`
- `lexibrarian.indexer.orchestrator` -- consumes `LexibraryConfig`
- `lexibrarian.archivist.pipeline` -- uses `LexibraryConfig` for scope_root, token_budgets, crawl settings
- `lexibrarian.archivist.service` -- uses `LLMConfig` for provider routing
- `lexibrarian.init.scaffolder` -- validates wizard answers through `LexibraryConfig.model_validate()`
- `lexibrarian.cli.lexictl_app` -- `setup` command reads `agent_environment` from config

## Dragons

- All models use `extra="ignore"` so unknown YAML keys are silently dropped
- `scope_root` defaults to `"."` (project root); archivist pipeline resolves it to an absolute path for file filtering
- `DaemonConfig.watchdog_enabled` replaces the former `enabled` field; defaults to `False`
- `IWHConfig` was added for Phase 8b init wizard; `project_name` and `agent_environment` are top-level fields on `LexibraryConfig`

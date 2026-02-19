# config/schema

**Summary:** Pydantic 2 models for the full Lexibrarian configuration hierarchy, validated from `.lexibrary/config.yaml`.

## Interface

| Name | Key Fields | Purpose |
| --- | --- | --- |
| `LLMConfig` | `provider`, `model`, `api_key_env`, `max_retries`, `timeout` | LLM provider settings |
| `TokenBudgetConfig` | `start_here_tokens`, `handoff_tokens`, `design_file_tokens`, `aindex_tokens`, `concept_file_tokens` | Per-artifact token budgets |
| `MappingConfig` | `strategies: list[dict]` | Mapping strategy config (stub for Phase 1) |
| `IgnoreConfig` | `use_gitignore: bool`, `additional_patterns: list[str]` | Ignore pattern settings |
| `DaemonConfig` | `debounce_seconds`, `sweep_interval_seconds`, `enabled` | Daemon watch settings |
| `LexibraryConfig` | `llm`, `token_budgets`, `mapping`, `ignore`, `daemon` | Top-level config container |

## Dependencies

- None (only pydantic)

## Dependents

- `lexibrarian.config.loader` — validates merged YAML into `LexibraryConfig`
- `lexibrarian.config.__init__` — re-exports all models
- `lexibrarian.ignore.patterns` — consumes `IgnoreConfig`
- `lexibrarian.llm.factory` — consumes `LLMConfig`
- `lexibrarian.tokenizer.factory` — expects `TokenizerConfig` (not yet defined here)

## Dragons

- `TokenizerConfig`, `CrawlConfig`, and `OutputConfig` are referenced in `crawler/engine.py` and `daemon/service.py` but **not yet defined** in this file — these must be added before the crawler or daemon can run
- All models use `extra="ignore"` so unknown YAML keys are silently dropped

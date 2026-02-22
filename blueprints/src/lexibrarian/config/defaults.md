# config/defaults

**Summary:** Holds the default `config.yaml` template string written by `lexi init` to `.lexibrary/config.yaml`.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `DEFAULT_PROJECT_CONFIG_TEMPLATE` | `str` | YAML template with all config keys and inline comments, including `scope_root`, `project_name`, `agent_environment`, `iwh`, `max_file_size_kb`, and `ast` sections |

## Dependents

- `lexibrarian.config.__init__` -- re-exports it
- `lexibrarian.init.scaffolder` -- writes it to `.lexibrary/config.yaml` on `create_lexibrary_skeleton()`

## Key Concepts

- Template includes all configuration sections: `scope_root`, `project_name`, `agent_environment`, `iwh`, `llm`, `token_budgets`, `mapping`, `ignore`, `daemon`, `crawl`, `ast`
- `project_name` and `agent_environment` were added for Phase 8b init wizard
- `iwh` section controls I Was Here (IWH) agent trace files
- `daemon` section uses `watchdog_enabled` (not `enabled`) with `sweep_interval_seconds` defaulting to 3600

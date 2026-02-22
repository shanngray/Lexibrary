## ADDED Requirements

### Requirement: DaemonService interface
The `DaemonService` class SHALL be completely rewritten with a new interface replacing the old `__init__(root, foreground)` / `start()` / `stop()` pattern.

New interface:
- `__init__(root: Path)` — no `foreground` parameter
- `run_once()` — single sweep, exit
- `run_watch()` — periodic sweeps, blocks until interrupted
- `run_watchdog()` — deprecated real-time watcher, blocks until interrupted
- `stop()` — graceful shutdown of all components

#### Scenario: Constructor takes only root path
- **WHEN** `DaemonService(root)` is created
- **THEN** it SHALL accept only a `root: Path` parameter
- **AND** there SHALL be no `foreground` parameter

#### Scenario: No reference to retired APIs
- **WHEN** `daemon/service.py` is loaded
- **THEN** it SHALL NOT import `full_crawl`, `ChangeDetector`, `create_llm_service`, `create_tokenizer`, or `find_config_file`
- **AND** it SHALL NOT reference `config.output` or `config.tokenizer`

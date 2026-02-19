# daemon/service

**Summary:** `DaemonService` orchestrates the file watcher, debouncer, and periodic sweep; handles PID file, signal handling, and graceful shutdown.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `DaemonService` | class | Top-level daemon orchestrator |
| `DaemonService.__init__` | `(root: Path, foreground: bool = True)` | Configure root and mode |
| `DaemonService.start` | `() -> None` | Load config, wire components, block until shutdown |
| `DaemonService.stop` | `() -> None` | Cancel debouncer, stop sweep, stop observer, remove PID file |

## Dependencies

- `lexibrarian.config` — `load_config`, `find_config_file`, `LexibraryConfig`
- `lexibrarian.crawler` — `full_crawl`
- `lexibrarian.crawler.change_detector` — `ChangeDetector`
- `lexibrarian.daemon.debouncer` — `Debouncer`
- `lexibrarian.daemon.scheduler` — `PeriodicSweep`
- `lexibrarian.daemon.watcher` — `LexibrarianEventHandler`
- `lexibrarian.ignore` — `create_ignore_matcher`
- `lexibrarian.llm` — `create_llm_service`
- `lexibrarian.tokenizer` — `create_tokenizer`

## Key Concepts

- PID file written to `<root>/.lexibrarian.pid`; removed on clean shutdown
- SIGTERM/SIGINT both trigger `_shutdown_event.set()`
- Background mode (`foreground=False`) is not yet implemented — prints warning and returns
- Debouncer callback and sweep callback both call `asyncio.run(full_crawl(...))` from a threading context

## Dragons

- `find_config_file` is imported from `lexibrarian.config` but does **not exist** in the current config package — this will raise `ImportError` at runtime
- `config.output.log_filename`, `config.output.cache_filename`, `config.tokenizer` — referenced but not yet in schema

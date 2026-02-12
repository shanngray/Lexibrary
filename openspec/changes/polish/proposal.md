## Why

All core features (phases 1-7) are implemented but lack production-grade error handling, comprehensive logging, pre-flight validation, and sufficient test coverage. Users currently see raw tracebacks for expected errors (missing API keys, permission issues), and there's no custom exception hierarchy to distinguish recoverable from fatal errors. This phase hardens the system before release.

## What Changes

- Add custom exception hierarchy (`LexibrarianError`, `ConfigError`, `CrawlError`, `LLMError`) in `utils/errors.py`
- Harden error handling across all modules: network errors, file system errors, config parse errors
- Wrap CLI commands in try/except for user-friendly error messages (no tracebacks for expected errors)
- Add pre-flight validation (`preflight_check`) before crawl/daemon operations (API key, directory writable, BAML client generated)
- Formalize logging strategy: `--verbose` flag for DEBUG, structured log levels per module, daemon file logging
- Add comprehensive test coverage targeting 80%+ line coverage overall, 90%+ on critical paths
- Add shared test fixtures (`conftest.py`, `sample_project/`) and mock strategy for LLM/filesystem/network
- Cover edge cases: empty projects, deep nesting, unicode filenames, symlinks, missing gitignore

## Capabilities

### New Capabilities
- `error-handling`: Custom exception hierarchy, module-level error handling for network/filesystem/config errors, user-friendly CLI error display
- `preflight-checks`: Pre-flight validation run before crawl and daemon operations to catch common problems early
- `test-coverage`: Comprehensive test suite with shared fixtures, mock strategy, and edge case coverage

### Modified Capabilities
- `cli-skeleton`: CLI commands wrap operations in try/except for `LexibrarianError`, add `--verbose` flag for DEBUG logging
- `llm-summarization`: LLM service catches and handles specific API errors (timeout, rate limit, auth, network) with fallback summaries
- `crawl-orchestration`: Crawler engine handles file system errors gracefully (permission denied, file deleted during crawl, broken symlinks)

## Impact

- **New files:** `src/lexibrarian/utils/errors.py`, `tests/conftest.py` (shared fixtures), new test files for edge cases
- **Modified files:** `cli.py` (error wrapping, verbose flag), `llm/service.py` (error handling), `crawler/engine.py` (FS error handling), `crawler/discovery.py` (permission handling), `crawler/file_reader.py` (read error handling), `config/loader.py` (config error handling), `utils/logging.py` (logging strategy refinements)
- **Dependencies:** None new — uses stdlib `logging`, existing `rich` for console output
- **Phase:** Phase 8 (final polish phase), depends on all prior phases being complete

## Context

Lexibrarian's core features (phases 1-7) are complete: config loading, ignore matching, directory discovery, file reading, LLM summarization, crawl orchestration, .aindex generation, and daemon mode. However, the system currently lacks:

- A custom exception hierarchy — errors bubble up as raw Python exceptions with full tracebacks
- Systematic error handling for expected failure modes (missing API keys, permission issues, network failures)
- Pre-flight validation before starting expensive operations
- Consistent logging levels across modules (some modules log, some don't)
- Sufficient test coverage for edge cases and error paths

The CLI already has a `--verbose` flag and `setup_logging()` utility, but logging isn't uniformly applied across all modules and the daemon file handler always uses the same level as console (should be DEBUG).

## Goals / Non-Goals

**Goals:**
- User-friendly error messages for all expected failure modes (no tracebacks)
- Pre-flight checks that catch configuration problems before any LLM calls or file writes
- Consistent, structured logging across all modules with appropriate log levels
- Daemon always logs to file at DEBUG level regardless of console verbosity
- Test coverage reaching 80%+ line coverage overall, 90%+ on critical paths (engine, parser, generator)
- Shared test fixtures and mock strategy that make writing new tests straightforward

**Non-Goals:**
- Structured logging (JSON format) — plain text is sufficient for this phase
- Log rotation or log aggregation — out of scope
- Performance optimization — separate concern
- New CLI commands or features beyond `--verbose` improvements
- External monitoring or alerting integrations

## Decisions

### 1. Exception hierarchy in `utils/errors.py`

**Decision:** Create a flat hierarchy: `LexibrarianError` base with three direct subclasses: `ConfigError`, `CrawlError`, `LLMError`.

**Rationale:** Three subclasses map cleanly to the three failure domains (config parsing, file system operations, LLM calls). A flat hierarchy is simpler than nested classes and sufficient for the CLI's try/except needs. Each CLI command catches `LexibrarianError` to print user-friendly messages and exit cleanly.

**Alternative considered:** Per-scenario exceptions (e.g., `APITimeoutError`, `PermissionDeniedError`). Rejected because the CLI only needs domain-level granularity — detailed info goes in the error message string and logs.

### 2. CLI error wrapping pattern

**Decision:** Each CLI command function wraps its core logic in `try/except LexibrarianError as e` and prints `e` via `console.print(f"[red]Error:[/red] {e}")` then exits with code 1. Unexpected exceptions (not `LexibrarianError`) still show full tracebacks for debugging.

**Rationale:** Users see clean messages for expected errors, developers see full context for unexpected ones. This follows the convention of tools like `git` and `uv`.

### 3. Pre-flight checks as a standalone function

**Decision:** Implement `preflight_check(config, root) -> list[str]` in `utils/errors.py`. Called at the top of `crawl` and `daemon` commands. Returns a list of error strings; empty means all checks passed.

**Rationale:** A pure function returning strings is easy to test, easy to extend, and decoupled from the CLI display logic. The CLI formats and displays the errors.

**Checks included:** API key availability (non-Ollama providers), root directory exists and is writable, BAML client generated.

### 4. Daemon file logging always at DEBUG

**Decision:** Modify `setup_logging()` to accept a separate `file_level` parameter. Console level follows `--verbose`, file handler always set to DEBUG when a log file is specified.

**Rationale:** The daemon log file is the primary debugging tool for background issues. Users shouldn't need to restart the daemon in verbose mode to get detailed logs. The file handler already exists; this is a one-line change.

### 5. Shared test fixtures in `tests/conftest.py`

**Decision:** Create `tests/conftest.py` with:
- `sample_project` fixture: creates the standard fixture tree in `tmp_path`
- `mock_llm_service` fixture: `AsyncMock` of `LLMService` with deterministic returns

Also maintain a static `tests/fixtures/sample_project/` for tests that read but don't write.

**Rationale:** Shared fixtures eliminate duplication across test modules. Using `tmp_path` for write tests ensures isolation. The static fixture is useful for read-only tests that don't need a fresh copy.

### 6. LLM error handling with specific fallbacks

**Decision:** `LLMService` catches specific exception types and returns fallback summaries with descriptive messages:
- Timeout → `"Summary unavailable (timeout)"`
- Auth error (401/403) → log actionable message, raise `LLMError` (non-recoverable)
- Rate limit (429) → log warning, back off, retry once, then fallback
- Network unreachable → `"Summary unavailable (network error)"`
- Malformed response → `"Summary unavailable (parse error)"`

**Rationale:** Most LLM errors are recoverable at the file level — a failed summary shouldn't stop the entire crawl. Auth errors are the exception since every subsequent call will also fail, so they escalate.

## Risks / Trade-offs

- **[Risk] Overly broad exception catching masks bugs** → Mitigation: Only catch `LexibrarianError` subclasses at CLI level. Unexpected exceptions still propagate with full tracebacks. Each catch site logs at ERROR level before returning fallbacks.

- **[Risk] Pre-flight checks add latency to every crawl start** → Mitigation: Checks are lightweight (env var lookup, path existence, one import). Total overhead < 10ms.

- **[Risk] Test fixtures diverge from real project structure over time** → Mitigation: Keep fixtures minimal and document their purpose. The fixtures test framework behavior, not real-world content.

- **[Trade-off] Auth errors abort the crawl rather than continuing** → Acceptable because continuing would waste time making calls that will all fail. The error message tells the user exactly what to fix.

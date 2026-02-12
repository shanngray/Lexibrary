## 1. Exception Hierarchy

- [ ] 1.1 Create `src/lexibrarian/utils/errors.py` with `LexibrarianError`, `ConfigError`, `CrawlError`, and `LLMError` classes
- [ ] 1.2 Add `from __future__ import annotations` and ensure all classes are importable from `lexibrarian.utils.errors`

## 2. Config Error Handling

- [ ] 2.1 Wrap TOML parsing in `config/loader.py` to catch `tomllib.TOMLDecodeError` and raise `ConfigError` with parse error details
- [ ] 2.2 Wrap Pydantic validation in `config/loader.py` to catch `ValidationError` and raise `ConfigError` identifying the invalid field
- [ ] 2.3 Update `llm/factory.py` to raise `ConfigError` (not `ValueError`) for unknown provider, listing valid providers in the message

## 3. LLM Error Handling

- [ ] 3.1 Update `llm/service.py` `summarize_file()` to catch timeout exceptions and return fallback `"Summary unavailable (timeout)"`
- [ ] 3.2 Update `llm/service.py` to catch 401/403 auth errors and raise `LLMError` with "Check your API key" message
- [ ] 3.3 Update `llm/service.py` to catch network connectivity errors and return fallback `"Summary unavailable (network error)"`
- [ ] 3.4 Update `llm/service.py` to catch BAML parse errors and return fallback `"Summary unavailable (parse error)"`
- [ ] 3.5 Update `llm/service.py` `summarize_files_batch()` with same error handling pattern (auth escalates, others fallback)
- [ ] 3.6 Update `llm/service.py` `summarize_directory()` with same error handling pattern

## 4. Crawler Error Handling

- [ ] 4.1 Update `crawler/engine.py` to catch `PermissionError` on file read, skip file, log warning, list as "Permission denied" in .aindex
- [ ] 4.2 Update `crawler/engine.py` to catch `FileNotFoundError` on file read (deleted during crawl), skip file, log warning
- [ ] 4.3 Update `crawler/engine.py` to catch `OSError` on .aindex write, log error, increment `CrawlStats.errors`, continue
- [ ] 4.4 Update `crawler/engine.py` to let `LLMError` propagate uncaught (auth failures abort crawl)
- [ ] 4.5 Update `crawler/discovery.py` or `crawler/file_reader.py` to handle broken symlinks (stat failure), skip and log debug

## 5. Pre-flight Checks

- [ ] 5.1 Add `preflight_check(config, root) -> list[str]` function to `utils/errors.py`
- [ ] 5.2 Implement API key check (skip for Ollama), root directory exists check, root writable check, BAML client import check
- [ ] 5.3 Call `preflight_check()` at start of `crawl` command; display errors with Rich and exit code 1 if any
- [ ] 5.4 Call `preflight_check()` at start of `daemon` command; display errors with Rich and exit code 1 if any

## 6. CLI Error Wrapping

- [ ] 6.1 Wrap `crawl` command body in `try/except LexibrarianError` — print `[red]Error:[/red] {e}` and `raise typer.Exit(code=1)`
- [ ] 6.2 Wrap `daemon` command body in `try/except LexibrarianError` — same pattern
- [ ] 6.3 Ensure unexpected exceptions (non-`LexibrarianError`) still show full tracebacks

## 7. Logging Improvements

- [ ] 7.1 Update `setup_logging()` to accept `file_level` parameter; daemon file handler always uses DEBUG
- [ ] 7.2 Replace `logging.basicConfig` call in `crawl` command with `setup_logging(verbose=verbose, log_file=...)`
- [ ] 7.3 Add `logger = logging.getLogger(__name__)` to modules that lack it: `config/loader.py`, `ignore/matcher.py`, `crawler/discovery.py`, `crawler/file_reader.py`, `indexer/writer.py`
- [ ] 7.4 Add appropriate log statements per the logging strategy: DEBUG for each-item operations, INFO for summary events, WARNING for skips/fallbacks, ERROR for failures

## 8. Shared Test Fixtures

- [ ] 8.1 Create `tests/conftest.py` with `sample_project` fixture (creates standard project tree in `tmp_path`)
- [ ] 8.2 Add `mock_llm_service` fixture to `tests/conftest.py` with deterministic `AsyncMock` returns
- [ ] 8.3 Verify static `tests/fixtures/sample_project/` exists and matches expected structure; update if needed

## 9. Error Handling Tests

- [ ] 9.1 Write unit tests for `utils/errors.py`: exception hierarchy, `preflight_check()` with various failure scenarios
- [ ] 9.2 Write tests for config error handling: invalid TOML, invalid field values, unknown provider
- [ ] 9.3 Write tests for LLM error handling: timeout fallback, auth error escalation, network error fallback, parse error fallback
- [ ] 9.4 Write tests for crawler error handling: permission denied, file deleted, write failure, broken symlink

## 10. Edge Case Tests

- [ ] 10.1 Test empty project (no files) produces `.aindex` with `(none)` sections
- [ ] 10.2 Test single file with no subdirectories
- [ ] 10.3 Test deeply nested directories (10+ levels) maintain bottom-up order
- [ ] 10.4 Test files with no extension detected as "Text"
- [ ] 10.5 Test unicode filenames handled correctly in `.aindex`
- [ ] 10.6 Test empty `.gitignore` and missing `.gitignore` scenarios
- [ ] 10.7 Test config with all defaults (no `lexibrary.toml`)

## 11. CLI Tests

- [ ] 11.1 Test `lexi crawl --verbose` enables debug logging
- [ ] 11.2 Test `lexi crawl` with LexibrarianError produces clean error output (no traceback)
- [ ] 11.3 Test `lexi crawl` with pre-flight failure exits before crawl starts

## 12. Coverage Verification

- [ ] 12.1 Run `uv run pytest --cov=lexibrarian --cov-report=term-missing -v` and verify 80%+ overall coverage
- [ ] 12.2 Verify `crawler/engine.py`, `indexer/parser.py`, `indexer/generator.py` each have 90%+ coverage
- [ ] 12.3 Add any missing tests to close coverage gaps on critical paths

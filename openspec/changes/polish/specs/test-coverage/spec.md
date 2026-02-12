## ADDED Requirements

### Requirement: Shared test fixtures in conftest
The test suite SHALL provide shared pytest fixtures in `tests/conftest.py` including a `sample_project` fixture that creates a standard project tree in `tmp_path` and a `mock_llm_service` fixture that returns deterministic summaries.

#### Scenario: sample_project fixture creates expected structure
- **WHEN** a test uses the `sample_project` fixture
- **THEN** a temporary directory SHALL exist containing: `main.py`, `README.md`, `image.png` (binary), `src/__init__.py`, `src/app.py`, `src/utils.py`, `tests/test_app.py`, and `.gitignore`

#### Scenario: mock_llm_service returns deterministic values
- **WHEN** a test uses the `mock_llm_service` fixture
- **THEN** `summarize_file()` SHALL return a `FileSummaryResult` with summary `"Test file summary."`, `summarize_files_batch()` SHALL return an empty list, and `summarize_directory()` SHALL return `"Test directory summary."`

### Requirement: LLM calls always mocked in tests
All test modules SHALL mock LLM service calls. No real network calls to LLM providers SHALL occur during test execution.

#### Scenario: Tests run without API keys
- **WHEN** `uv run pytest` is executed without any LLM API keys set
- **THEN** all tests SHALL pass without network errors

### Requirement: File system tests use tmp_path
All tests that create or modify files SHALL use pytest's `tmp_path` fixture for isolation. No test SHALL write to the real source tree.

#### Scenario: Test cleanup is automatic
- **WHEN** a test that writes files completes
- **THEN** all written files SHALL be in a temporary directory that pytest cleans up automatically

### Requirement: Overall test coverage target
The test suite SHALL achieve at least 80% line coverage across the `lexibrarian` package when run with `--cov=lexibrarian`.

#### Scenario: Coverage meets minimum threshold
- **WHEN** running `uv run pytest --cov=lexibrarian`
- **THEN** the reported line coverage SHALL be 80% or higher

### Requirement: Critical path coverage target
The crawler engine (`crawler/engine.py`), iandex parser (`indexer/parser.py`), and iandex generator (`indexer/generator.py`) modules SHALL each have at least 90% line coverage.

#### Scenario: Engine module coverage
- **WHEN** running `uv run pytest --cov=lexibrarian.crawler.engine`
- **THEN** the reported line coverage SHALL be 90% or higher

#### Scenario: Parser module coverage
- **WHEN** running `uv run pytest --cov=lexibrarian.indexer.parser`
- **THEN** the reported line coverage SHALL be 90% or higher

#### Scenario: Generator module coverage
- **WHEN** running `uv run pytest --cov=lexibrarian.indexer.generator`
- **THEN** the reported line coverage SHALL be 90% or higher

### Requirement: Edge case test coverage
The test suite SHALL include tests for edge cases: empty project (no files), single file with no subdirectories, deeply nested directories (10+ levels), files with no extension, unicode filenames, empty `.gitignore`, no `.gitignore`, and config with all defaults.

#### Scenario: Empty project produces valid iandex
- **WHEN** crawling a project directory containing no files
- **THEN** a `.aindex` file SHALL be created with `(none)` for both files and subdirectories sections

#### Scenario: Unicode filenames handled correctly
- **WHEN** crawling a project containing files with unicode characters in their names
- **THEN** the files SHALL appear correctly in the `.aindex` output

#### Scenario: Deep nesting maintains bottom-up order
- **WHEN** crawling a project with 10+ levels of directory nesting
- **THEN** all directories SHALL be indexed and child directories SHALL be processed before parents

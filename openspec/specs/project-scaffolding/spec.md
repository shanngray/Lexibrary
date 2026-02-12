# project-scaffolding Specification

## Purpose
TBD - created by archiving change phase-1-foundation. Update Purpose after archive.
## Requirements
### Requirement: Project directory structure
The system SHALL have a Python package structure with source code under `src/lexibrarian/` and test code under `tests/`. Supporting directories for BAML, fixtures, and configuration SHALL exist.

#### Scenario: Directory structure exists after initialization
- **WHEN** running `uv sync` in the project root
- **THEN** the following directories are created: `src/lexibrarian/`, `src/lexibrarian/config/`, `src/lexibrarian/ignore/`, `src/lexibrarian/utils/`, `src/lexibrarian/crawler/`, `src/lexibrarian/indexer/`, `src/lexibrarian/llm/`, `src/lexibrarian/tokenizer/`, `src/lexibrarian/daemon/`, `tests/`, `baml_src/`

### Requirement: Project metadata in pyproject.toml
The system SHALL declare the project name as "lexibrary", version "0.1.0", and include all required dependencies for config management, CLI, ignore patterns, tokenization, BAML, and HTTP operations.

#### Scenario: Dependencies are declared
- **WHEN** reading `pyproject.toml`
- **THEN** it contains Typer (>=0.15.0), Pydantic (>=2.0.0), Pathspec (>=0.12.0), Watchdog (>=4.0.0), Tiktoken (>=0.8.0), BAML-py (>=0.75.0), and HTTPx (>=0.27.0)

#### Scenario: Optional dependencies are declared
- **WHEN** reading `pyproject.toml` optional-dependencies
- **THEN** "dev" extras include Pytest, Pytest-asyncio, Pytest-cov, Ruff, Mypy, and Respx; "ollama" extra includes Ollama library

#### Scenario: CLI entry points are configured
- **WHEN** reading `pyproject.toml` project.scripts
- **THEN** both "lexi" and "lexibrarian" commands map to "lexibrarian.cli:app"

### Requirement: Python version is pinned
The system SHALL require Python 3.11+ and pin to Python 3.12 via `.python-version` file.

#### Scenario: Python version file exists
- **WHEN** reading `.python-version`
- **THEN** it contains exactly "3.12"

### Requirement: .gitignore is configured
The system SHALL exclude Python artifacts, virtual environments, Lexibrarian caches, and generated BAML code.

#### Scenario: .gitignore contains project-specific patterns
- **WHEN** reading `.gitignore`
- **THEN** it includes patterns for `.aindex`, `.lexibrarian_cache.json`, `.lexibrarian.log`, `baml_client/`, and standard Python patterns (`__pycache__/`, `*.pyc`, `.venv/`, `venv/`)

### Requirement: Module initialization
The system SHALL have proper `__init__.py` files in all packages with version declaration.

#### Scenario: Root module declares version
- **WHEN** importing `lexibrarian.__version__`
- **THEN** it returns "0.1.0"

#### Scenario: Root module can be run as a script
- **WHEN** running `python -m lexibrarian`
- **THEN** it imports the CLI app without errors


# project-scaffolding Specification

## Purpose
TBD - created by archiving change phase-1-foundation. Update Purpose after archive.
## Requirements
### Requirement: Project directory structure
The system SHALL have a Python package structure with source code under `src/lexibrarian/` and test code under `tests/`. Supporting directories for BAML and fixtures SHALL exist. The `indexer/` module is temporarily retired; the `artifacts/` module is added.

#### Scenario: Directory structure exists after initialization
- **WHEN** running `uv sync` in the project root
- **THEN** the following directories exist: `src/lexibrarian/`, `src/lexibrarian/config/`, `src/lexibrarian/ignore/`, `src/lexibrarian/utils/`, `src/lexibrarian/artifacts/`, `src/lexibrarian/crawler/`, `src/lexibrarian/llm/`, `src/lexibrarian/tokenizer/`, `src/lexibrarian/daemon/`, `tests/`, `baml_src/`

#### Scenario: indexer/ module is absent
- **WHEN** inspecting `src/lexibrarian/`
- **THEN** there is no `indexer/` directory (it has been retired)

### Requirement: Project metadata in pyproject.toml
The system SHALL declare the project name as "lexibrary", version "1.2.0" (or current version), and include all required dependencies including `PyYAML>=6.0.0,<7.0.0` for YAML config parsing.

#### Scenario: Dependencies are declared including PyYAML
- **WHEN** reading `pyproject.toml`
- **THEN** it contains Typer (>=0.15.0,<1.0.0), Pydantic (>=2.0.0,<3.0.0), Pathspec (>=0.12.0,<1.0.0), Watchdog (>=4.0.0,<5.0.0), Tiktoken (>=0.8.0,<1.0.0), BAML-py (>=0.218.0,<1.0.0), HTTPx (>=0.27.0,<1.0.0), and PyYAML (>=6.0.0,<7.0.0)

#### Scenario: CLI entry points are configured
- **WHEN** reading `pyproject.toml` project.scripts
- **THEN** both "lexi" and "lexibrarian" commands map to "lexibrarian.cli:app"

### Requirement: Python version is pinned
The system SHALL require Python 3.11+ and pin to Python 3.12 via `.python-version` file.

#### Scenario: Python version file exists
- **WHEN** reading `.python-version`
- **THEN** it contains exactly "3.12"

### Requirement: .gitignore is configured
The system SHALL exclude Python artifacts, virtual environments, generated BAML code, and `.lexibrary/` generated artifacts while keeping `.lexibrary/config.yaml` tracked.

#### Scenario: .gitignore contains .lexibrary/ generated file patterns
- **WHEN** reading `.gitignore`
- **THEN** it includes patterns for `.lexibrary/START_HERE.md`, `.lexibrary/HANDOFF.md`, `.lexibrary/**/*.md`, `.lexibrary/**/.aindex`, `baml_client/`, and standard Python patterns (`__pycache__/`, `*.pyc`, `.venv/`, `venv/`)

#### Scenario: .lexibrary/config.yaml is NOT gitignored
- **WHEN** running `git status` in a project with `.lexibrary/config.yaml`
- **THEN** `config.yaml` is tracked (not in .gitignore), because project config is version-controlled

### Requirement: Module initialization
The system SHALL have proper `__init__.py` files in all packages with version declaration.

#### Scenario: Root module declares version
- **WHEN** importing `lexibrarian.__version__`
- **THEN** it returns "0.1.0"

#### Scenario: Root module can be run as a script
- **WHEN** running `python -m lexibrarian`
- **THEN** it imports the CLI app without errors

### Requirement: artifacts module structure
The system SHALL have `src/lexibrarian/artifacts/` as a proper Python package with `__init__.py` re-exporting all public model classes.

#### Scenario: artifacts package is importable
- **WHEN** importing `from lexibrarian.artifacts import DesignFile`
- **THEN** the import succeeds without error

#### Scenario: artifacts package has module files
- **WHEN** inspecting `src/lexibrarian/artifacts/`
- **THEN** it contains `__init__.py`, `design_file.py`, `aindex.py`, and `concept.py` (guardrail.py removed)

#### Scenario: stack module exists
- **WHEN** inspecting `src/lexibrarian/stack/`
- **THEN** it contains `__init__.py`, `models.py`, `parser.py`, `serializer.py`, `template.py`, `index.py`, and `mutations.py`

### Requirement: exceptions module
The system SHALL have `src/lexibrarian/exceptions.py` containing all project-level exception classes, starting with `LexibraryNotFoundError`.

#### Scenario: exceptions module is importable
- **WHEN** importing `from lexibrarian.exceptions import LexibraryNotFoundError`
- **THEN** the import succeeds without error

### Requirement: Stack directory in scaffolding
`lexi init` SHALL create a `.lexibrary/stack/` directory (instead of `.lexibrary/guardrails/`) in the project skeleton.

#### Scenario: Init creates stack directory
- **WHEN** running `lexi init` in an empty directory
- **THEN** `.lexibrary/stack/` SHALL be created

#### Scenario: Init does not create guardrails directory
- **WHEN** running `lexi init` in an empty directory
- **THEN** `.lexibrary/guardrails/` SHALL NOT be created


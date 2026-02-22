"""Tests for the maintenance CLI (lexictl) application."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import yaml
from typer.testing import CliRunner

from lexibrarian.archivist.change_checker import ChangeLevel
from lexibrarian.archivist.pipeline import FileResult, UpdateStats
from lexibrarian.cli import lexictl_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------


class TestHelp:
    def test_help_lists_all_commands(self) -> None:
        result = runner.invoke(lexictl_app, ["--help"])
        assert result.exit_code == 0
        for cmd in (
            "init",
            "update",
            "validate",
            "status",
            "setup",
            "daemon",
        ):
            assert cmd in result.output

    def test_help_does_not_include_agent_commands(self) -> None:
        result = runner.invoke(lexictl_app, ["--help"])
        assert result.exit_code == 0
        # Extract the listed command names from Typer help output.
        # Typer formats commands as "│ command_name  Description... │"
        import re

        command_names = re.findall(r"│\s+(\w+)\s{2,}", result.output)
        # Agent commands should NOT be registered as top-level commands in lexictl
        for cmd in ("lookup", "index", "concepts", "search", "stack", "concept", "describe"):
            assert cmd not in command_names, f"Agent command '{cmd}' should not be in lexictl"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_project(tmp_path: Path) -> Path:
    """Create a minimal initialized project at tmp_path with some source files."""
    (tmp_path / ".lexibrary").mkdir()
    (tmp_path / ".lexibrary" / "config.yaml").write_text("")
    # Create source directory with a Python file
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')\n")
    (tmp_path / "src" / "utils.py").write_text("x = 1\ny = 2\n")
    return tmp_path


def _setup_archivist_project(tmp_path: Path) -> Path:
    """Create a minimal project with .lexibrary and source files."""
    (tmp_path / ".lexibrary").mkdir()
    (tmp_path / ".lexibrary" / "config.yaml").write_text("")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hello():\n    pass\n")
    (tmp_path / "src" / "utils.py").write_text("x = 1\n")
    return tmp_path


def _create_design_file(tmp_path: Path, source_rel: str, source_content: str) -> Path:
    """Create a design file in .lexibrary mirror tree with correct metadata footer."""
    content_hash = hashlib.sha256(source_content.encode()).hexdigest()
    design_path = tmp_path / ".lexibrary" / f"{source_rel}.md"
    design_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().isoformat()
    design_content = f"""---
description: Design file for {source_rel}
updated_by: archivist
---

# {source_rel}

Test design file content.

## Interface Contract

```python
def hello(): ...
```

## Dependencies

- (none)

## Dependents

- (none)

<!-- lexibrarian:meta
source: {source_rel}
source_hash: {content_hash}
design_hash: placeholder
generated: {now}
generator: lexibrarian-v2
-->
"""
    design_path.write_text(design_content, encoding="utf-8")
    return design_path


def _create_concept_file(
    tmp_path: Path,
    name: str,
    *,
    tags: list[str] | None = None,
    status: str = "active",
    aliases: list[str] | None = None,
    summary: str = "",
) -> Path:
    """Create a concept markdown file in .lexibrary/concepts/."""
    import re  # noqa: PLC0415

    concepts_dir = tmp_path / ".lexibrary" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)

    resolved_tags = tags or []
    resolved_aliases = aliases or []

    fm_data: dict[str, object] = {
        "title": name,
        "aliases": resolved_aliases,
        "tags": resolved_tags,
        "status": status,
    }
    fm_str = yaml.dump(fm_data, default_flow_style=False, sort_keys=False).rstrip("\n")

    # PascalCase filename
    words = re.split(r"[^a-zA-Z0-9]+", name)
    pascal = "".join(w.capitalize() for w in words if w)
    file_path = concepts_dir / f"{pascal}.md"

    body = f"---\n{fm_str}\n---\n\n{summary}\n\n## Details\n\n## Decision Log\n\n## Related\n"
    file_path.write_text(body, encoding="utf-8")
    return file_path


def _create_stack_post(
    tmp_path: Path,
    post_id: str = "ST-001",
    title: str = "Bug in auth module",
    tags: list[str] | None = None,
    status: str = "open",
    author: str = "tester",
    votes: int = 0,
    problem: str = "Something is broken",
    evidence: list[str] | None = None,
    bead: str | None = None,
    refs_files: list[str] | None = None,
    refs_concepts: list[str] | None = None,
) -> Path:
    """Create a stack post file for testing."""
    resolved_tags = tags or ["auth"]
    resolved_evidence = evidence or []
    import re as _re

    title_slug = _re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:50]
    filename = f"{post_id}-{title_slug}.md"
    stack_dir = tmp_path / ".lexibrary" / "stack"
    stack_dir.mkdir(parents=True, exist_ok=True)
    post_path = stack_dir / filename

    fm_data: dict[str, object] = {
        "id": post_id,
        "title": title,
        "tags": resolved_tags,
        "status": status,
        "created": "2026-01-15",
        "author": author,
        "bead": bead,
        "votes": votes,
        "duplicate_of": None,
        "refs": {
            "concepts": refs_concepts or [],
            "files": refs_files or [],
            "designs": [],
        },
    }
    fm_str = yaml.dump(fm_data, default_flow_style=False, sort_keys=False).rstrip("\n")

    parts = [f"---\n{fm_str}\n---\n\n## Problem\n\n{problem}\n\n### Evidence\n\n"]
    for item in resolved_evidence:
        parts.append(f"- {item}\n")
    parts.append("\n")

    post_path.write_text("".join(parts), encoding="utf-8")
    return post_path


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------


class TestInit:
    """Tests for the wizard-based ``lexictl init`` command."""

    def test_reinit_guard_blocks_existing_project(self, tmp_path: Path) -> None:
        """Init should fail with exit 1 when .lexibrary/ already exists."""
        (tmp_path / ".lexibrary").mkdir()

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(lexictl_app, ["init"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "already initialised" in result.output
        assert "setup --update" in result.output

    def test_defaults_creates_skeleton(self, tmp_path: Path) -> None:
        """``--defaults`` should run the wizard in non-interactive mode and create .lexibrary/."""
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(lexictl_app, ["init", "--defaults"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Created" in result.output
        assert (tmp_path / ".lexibrary" / "config.yaml").exists()
        assert (tmp_path / ".lexibrary" / "START_HERE.md").exists()
        # Wizard path does NOT create HANDOFF.md
        assert not (tmp_path / ".lexibrary" / "HANDOFF.md").exists()
        assert (tmp_path / ".lexibrary" / "concepts" / ".gitkeep").exists()
        assert (tmp_path / ".lexibrary" / "stack" / ".gitkeep").exists()
        assert "lexictl update" in result.output

    def test_defaults_reinit_guard_still_works(self, tmp_path: Path) -> None:
        """Re-init guard should also trigger with ``--defaults``."""
        (tmp_path / ".lexibrary").mkdir()

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(lexictl_app, ["init", "--defaults"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "already initialised" in result.output


# ---------------------------------------------------------------------------
# Update command tests
# ---------------------------------------------------------------------------


class TestUpdateCommand:
    """Tests for the `lexictl update` command."""

    def test_update_single_file(self, tmp_path: Path) -> None:
        """Update single file calls update_file and reports result."""
        project = _setup_archivist_project(tmp_path)

        mock_result = FileResult(change=ChangeLevel.NEW_FILE)
        mock_update_file = AsyncMock(return_value=mock_result)

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            with patch(
                "lexibrarian.archivist.pipeline.update_file",
                mock_update_file,
            ):
                result = runner.invoke(lexictl_app, ["update", "src/main.py"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Done" in result.output
        assert "new_file" in result.output

    def test_update_directory(self, tmp_path: Path) -> None:
        """Update directory calls update_project with progress bar."""
        project = _setup_archivist_project(tmp_path)

        mock_stats = UpdateStats(
            files_scanned=5,
            files_unchanged=2,
            files_updated=2,
            files_created=1,
        )
        mock_update_project = AsyncMock(return_value=mock_stats)

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            with patch(
                "lexibrarian.archivist.pipeline.update_project",
                mock_update_project,
            ):
                result = runner.invoke(lexictl_app, ["update", "src"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Files scanned" in result.output
        assert "5" in result.output

    def test_update_project(self, tmp_path: Path) -> None:
        """Update with no args calls update_project and regenerates START_HERE."""
        project = _setup_archivist_project(tmp_path)

        mock_stats = UpdateStats(files_scanned=3, files_unchanged=3)
        mock_update_project = AsyncMock(return_value=mock_stats)
        mock_start_here = AsyncMock(return_value=project / ".lexibrary" / "START_HERE.md")

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            with (
                patch(
                    "lexibrarian.archivist.pipeline.update_project",
                    mock_update_project,
                ),
                patch(
                    "lexibrarian.archivist.start_here.generate_start_here",
                    mock_start_here,
                ),
            ):
                result = runner.invoke(lexictl_app, ["update"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "START_HERE.md regenerated" in result.output
        assert "Files scanned" in result.output

    def test_update_no_project_error(self, tmp_path: Path) -> None:
        """Update outside a project should exit with error."""
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(lexictl_app, ["update"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "No .lexibrary/" in result.output

    def test_update_single_file_failure(self, tmp_path: Path) -> None:
        """Update single file that fails should exit 1."""
        project = _setup_archivist_project(tmp_path)

        mock_result = FileResult(change=ChangeLevel.INTERFACE_CHANGED, failed=True)
        mock_update_file = AsyncMock(return_value=mock_result)

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            with patch(
                "lexibrarian.archivist.pipeline.update_file",
                mock_update_file,
            ):
                result = runner.invoke(lexictl_app, ["update", "src/main.py"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "Failed" in result.output


# ---------------------------------------------------------------------------
# Validate command tests
# ---------------------------------------------------------------------------


def _setup_validate_project(tmp_path: Path) -> Path:
    """Create a project with known validation issues for testing.

    Sets up:
    - A minimal .lexibrary with config
    - A source file with a matching design file (fresh hash)
    - A concept file with valid frontmatter
    - No deliberate errors (clean baseline)
    """
    (tmp_path / ".lexibrary").mkdir()
    (tmp_path / ".lexibrary" / "config.yaml").write_text("")
    (tmp_path / ".lexibrary" / "concepts").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    source_content = "def hello():\n    pass\n"
    (tmp_path / "src" / "main.py").write_text(source_content)

    # Create a design file with correct hash
    source_hash = hashlib.sha256(source_content.encode()).hexdigest()
    design_dir = tmp_path / ".lexibrary" / "src"
    design_dir.mkdir(parents=True, exist_ok=True)
    design_content = f"""---
description: Main module
updated_by: archivist
---

# src/main.py

Main module.

## Interface Contract

```python
def hello(): ...
```

## Dependencies

- (none)

## Dependents

- (none)

<!-- lexibrarian:meta
source: src/main.py
source_hash: {source_hash}
design_hash: placeholder
generated: 2026-01-01T00:00:00
generator: lexibrarian-v2
-->
"""
    (design_dir / "main.py.md").write_text(design_content, encoding="utf-8")
    return tmp_path


def _setup_validate_project_with_errors(tmp_path: Path) -> Path:
    """Create a project that will produce validation errors.

    Includes a concept file missing mandatory frontmatter fields.
    """
    project = _setup_validate_project(tmp_path)
    # Create a broken concept file (missing required frontmatter fields)
    concepts_dir = project / ".lexibrary" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    (concepts_dir / "BrokenConcept.md").write_text(
        "---\ntitle: Broken\n---\n\nMissing aliases, tags, status.\n",
        encoding="utf-8",
    )
    return project


def _setup_validate_project_with_warnings(tmp_path: Path) -> Path:
    """Create a project with stale hash (warning) but no errors.

    Writes a design file whose source_hash does not match the actual source.
    """
    (tmp_path / ".lexibrary").mkdir()
    (tmp_path / ".lexibrary" / "config.yaml").write_text("")
    (tmp_path / ".lexibrary" / "concepts").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    source_content = "def hello():\n    return 42\n"
    (tmp_path / "src" / "main.py").write_text(source_content)

    # Design file with WRONG hash (stale)
    design_dir = tmp_path / ".lexibrary" / "src"
    design_dir.mkdir(parents=True, exist_ok=True)
    design_content = """---
description: Main module
updated_by: archivist
---

# src/main.py

Main module.

## Interface Contract

```python
def hello(): ...
```

## Dependencies

- (none)

## Dependents

- (none)

<!-- lexibrarian:meta
source: src/main.py
source_hash: 0000000000000000000000000000000000000000000000000000000000000000
design_hash: placeholder
generated: 2026-01-01T00:00:00
generator: lexibrarian-v2
-->
"""
    (design_dir / "main.py.md").write_text(design_content, encoding="utf-8")
    return tmp_path


class TestValidateCommand:
    """Tests for the `lexictl validate` command."""

    def _invoke(self, tmp_path: Path, args: list[str]) -> object:
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(lexictl_app, args)
        finally:
            os.chdir(old_cwd)

    def test_validate_clean_exit_0(self, tmp_path: Path) -> None:
        """A clean library with no issues exits with code 0."""
        project = _setup_validate_project(tmp_path)
        # Make an .aindex so aindex_coverage does not fire info
        aindex_dir = project / ".lexibrary" / "src"
        aindex_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime as _dt

        now = _dt.now().isoformat()
        (aindex_dir / ".aindex").write_text(
            f"""# src/

Source directory

## Child Map

| Name | Type | Description |
| --- | --- | --- |
| `main.py` | file | Main module |

## Local Conventions

(none)

<!-- lexibrarian:meta source="src" source_hash="abc" generated="{now}" -->
""",
            encoding="utf-8",
        )
        # Also create root .aindex
        root_aindex_dir = project / ".lexibrary"
        (root_aindex_dir / ".aindex").write_text(
            f"""# ./

Project root

## Child Map

| Name | Type | Description |
| --- | --- | --- |
| `src/` | dir | Source code |

## Local Conventions

(none)

<!-- lexibrarian:meta source="." source_hash="abc" generated="{now}" generator="lexibrarian-v2" -->
""",
            encoding="utf-8",
        )
        result = self._invoke(project, ["validate"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "No validation issues found" in result.output  # type: ignore[union-attr]

    def test_validate_errors_exit_1(self, tmp_path: Path) -> None:
        """A library with error-severity issues exits with code 1."""
        project = _setup_validate_project_with_errors(tmp_path)
        result = self._invoke(project, ["validate"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "error" in output.lower()

    def test_validate_warnings_only_exit_2(self, tmp_path: Path) -> None:
        """A library with only warning-severity issues exits with code 2."""
        project = _setup_validate_project_with_warnings(tmp_path)
        # Run only hash_freshness check (warning-level) to isolate warnings
        result = self._invoke(project, ["validate", "--check", "hash_freshness"])
        assert result.exit_code == 2  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "warning" in output.lower()

    def test_validate_json_produces_valid_json(self, tmp_path: Path) -> None:
        """The --json flag outputs valid JSON with issues and summary."""
        import json as _json

        project = _setup_validate_project(tmp_path)
        result = self._invoke(project, ["validate", "--json"])
        output = result.output  # type: ignore[union-attr]
        parsed = _json.loads(output)
        assert "issues" in parsed
        assert "summary" in parsed
        assert isinstance(parsed["issues"], list)
        assert isinstance(parsed["summary"], dict)
        assert "error_count" in parsed["summary"]
        assert "warning_count" in parsed["summary"]
        assert "info_count" in parsed["summary"]
        assert "total" in parsed["summary"]

    def test_validate_severity_filter(self, tmp_path: Path) -> None:
        """The --severity flag filters checks by severity level."""
        import json as _json

        project = _setup_validate_project_with_warnings(tmp_path)
        # With --severity error, only error-level checks run (no warnings expected)
        result = self._invoke(project, ["validate", "--severity", "error", "--json"])
        output = result.output  # type: ignore[union-attr]
        parsed = _json.loads(output)
        # No warning or info issues should be present because only error-level checks ran
        assert parsed["summary"]["warning_count"] == 0
        assert parsed["summary"]["info_count"] == 0

    def test_validate_check_runs_single_check(self, tmp_path: Path) -> None:
        """The --check flag runs only the specified check."""
        import json as _json

        project = _setup_validate_project(tmp_path)
        result = self._invoke(project, ["validate", "--check", "concept_frontmatter", "--json"])
        output = result.output  # type: ignore[union-attr]
        parsed = _json.loads(output)
        # All issues (if any) should be from the concept_frontmatter check
        for issue in parsed["issues"]:
            assert issue["check"] == "concept_frontmatter"

    def test_validate_invalid_check_name_shows_available(self, tmp_path: Path) -> None:
        """An invalid --check name shows available checks and exits 1."""
        project = _setup_validate_project(tmp_path)
        result = self._invoke(project, ["validate", "--check", "nonexistent_check"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "Available checks" in output or "Unknown check" in output
        # Should list some real check names
        assert "concept_frontmatter" in output
        assert "hash_freshness" in output

    def test_validate_no_project_root(self, tmp_path: Path) -> None:
        """Validate without .lexibrary should exit 1."""
        result = self._invoke(tmp_path, ["validate"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Status command tests
# ---------------------------------------------------------------------------


def _setup_status_project(tmp_path: Path) -> Path:
    """Create a project with design files, concepts, and stack posts for status tests."""
    (tmp_path / ".lexibrary").mkdir()
    (tmp_path / ".lexibrary" / "config.yaml").write_text("")
    (tmp_path / "src").mkdir()
    return tmp_path


class TestStatusCommand:
    """Tests for the `lexictl status` command."""

    def _invoke(self, tmp_path: Path, args: list[str]) -> object:
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(lexictl_app, args)
        finally:
            os.chdir(old_cwd)

    def test_status_output_format(self, tmp_path: Path) -> None:
        """Status shows dashboard with artifact counts and issues."""
        project = _setup_status_project(tmp_path)

        # Create source files and design files
        src_content = "def hello(): pass\n"
        (project / "src" / "main.py").write_text(src_content)
        _create_design_file(project, "src/main.py", src_content)

        # Create concepts
        _create_concept_file(project, "Auth", tags=["security"], status="active")
        _create_concept_file(project, "Cache", tags=["perf"], status="draft")

        # Create stack posts
        _create_stack_post(project, post_id="ST-001", title="Test bug", status="open")
        _create_stack_post(project, post_id="ST-002", title="Fixed issue", status="resolved")

        result = self._invoke(project, ["status"])
        output = result.output  # type: ignore[union-attr]

        # Dashboard header
        assert "Lexibrarian Status" in output
        # File counts
        assert "Files:" in output
        assert "1 tracked" in output
        # Concept counts
        assert "Concepts:" in output
        assert "1 active" in output
        assert "1 draft" in output
        # Stack counts
        assert "Stack:" in output
        assert "2 post" in output
        assert "1 resolved" in output
        assert "1 open" in output
        # Issues line
        assert "Issues:" in output
        # Updated line
        assert "Updated:" in output

    def test_status_clean_library_exits_0(self, tmp_path: Path) -> None:
        """Clean library with no validation issues exits with code 0."""
        project = _setup_status_project(tmp_path)
        src_content = "x = 1\n"
        (project / "src" / "main.py").write_text(src_content)
        _create_design_file(project, "src/main.py", src_content)

        result = self._invoke(project, ["status"])
        assert result.exit_code == 0  # type: ignore[union-attr]

    def test_status_empty_library(self, tmp_path: Path) -> None:
        """Empty library shows zero counts and 'Updated: never'."""
        project = _setup_status_project(tmp_path)
        result = self._invoke(project, ["status"])
        output = result.output  # type: ignore[union-attr]
        assert "Files: 0 tracked" in output
        assert "Concepts: 0" in output
        assert "Stack: 0 posts" in output
        assert "Updated: never" in output
        assert result.exit_code == 0  # type: ignore[union-attr]

    def test_status_quiet_healthy(self, tmp_path: Path) -> None:
        """Quiet mode with no issues outputs 'lexictl: library healthy'."""
        project = _setup_status_project(tmp_path)
        result = self._invoke(project, ["status", "--quiet"])
        output = result.output.strip()  # type: ignore[union-attr]
        assert output == "lexictl: library healthy"
        assert result.exit_code == 0  # type: ignore[union-attr]

    def test_status_quiet_with_warnings(self, tmp_path: Path) -> None:
        """Quiet mode with warnings shows count and suggests lexictl validate."""
        project = _setup_status_project(tmp_path)

        # Create a stale design file (source hash mismatch -> warning from hash_freshness)
        original_content = "def hello(): pass\n"
        (project / "src" / "stale.py").write_text("def hello(): return 1\n")
        _create_design_file(project, "src/stale.py", original_content)

        result = self._invoke(project, ["status", "--quiet"])
        output = result.output.strip()  # type: ignore[union-attr]
        # Should mention warnings and suggest lexictl validate
        assert "warning" in output
        assert "lexictl validate" in output
        assert result.exit_code == 2  # type: ignore[union-attr]

    def test_status_stale_files_counted(self, tmp_path: Path) -> None:
        """Status reports stale file count when hashes mismatch."""
        project = _setup_status_project(tmp_path)

        # Create a fresh file
        fresh_content = "x = 1\n"
        (project / "src" / "fresh.py").write_text(fresh_content)
        _create_design_file(project, "src/fresh.py", fresh_content)

        # Create a stale file (content differs from hash in design file)
        original_content = "y = 2\n"
        (project / "src" / "stale.py").write_text("y = 3\n")
        _create_design_file(project, "src/stale.py", original_content)

        result = self._invoke(project, ["status"])
        output = result.output  # type: ignore[union-attr]
        assert "2 tracked" in output
        assert "1 stale" in output

    def test_status_concept_status_breakdown(self, tmp_path: Path) -> None:
        """Status shows concept counts broken down by status."""
        project = _setup_status_project(tmp_path)

        _create_concept_file(project, "Alpha", tags=["a"], status="active")
        _create_concept_file(project, "Beta", tags=["b"], status="active")
        _create_concept_file(project, "Gamma", tags=["c"], status="deprecated")
        _create_concept_file(project, "Delta", tags=["d"], status="draft")

        result = self._invoke(project, ["status"])
        output = result.output  # type: ignore[union-attr]
        assert "2 active" in output
        assert "1 deprecated" in output
        assert "1 draft" in output

    def test_status_no_validate_suggestion_when_clean(self, tmp_path: Path) -> None:
        """When no issues, the 'Run lexictl validate' suggestion is not shown."""
        project = _setup_status_project(tmp_path)
        result = self._invoke(project, ["status"])
        output = result.output  # type: ignore[union-attr]
        assert "lexictl validate" not in output

    def test_status_validate_suggestion_when_issues(self, tmp_path: Path) -> None:
        """When issues exist, suggests running lexictl validate."""
        project = _setup_status_project(tmp_path)

        # Create stale file to generate a warning
        original = "x = 1\n"
        (project / "src" / "s.py").write_text("x = 2\n")
        _create_design_file(project, "src/s.py", original)

        result = self._invoke(project, ["status"])
        output = result.output  # type: ignore[union-attr]
        assert "Run `lexictl validate` for details." in output

    def test_status_exit_code_with_warnings(self, tmp_path: Path) -> None:
        """Status exits with code 2 when warnings exist but no errors."""
        project = _setup_status_project(tmp_path)

        # Stale file -> hash_freshness warning
        original = "a = 1\n"
        (project / "src" / "w.py").write_text("a = 2\n")
        _create_design_file(project, "src/w.py", original)

        result = self._invoke(project, ["status"])
        assert result.exit_code == 2  # type: ignore[union-attr]

    def test_status_no_project_exits_1(self, tmp_path: Path) -> None:
        """Status without .lexibrary should exit 1."""
        result = self._invoke(tmp_path, ["status"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Setup command tests
# ---------------------------------------------------------------------------


class TestSetupCommand:
    """Tests for the ``lexictl setup`` command."""

    def _invoke(self, tmp_path: Path, args: list[str]) -> object:
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(lexictl_app, args)
        finally:
            os.chdir(old_cwd)

    def test_setup_without_update_shows_usage(self, tmp_path: Path) -> None:
        """Running ``setup`` without ``--update`` shows usage instructions and exits 0."""
        result = self._invoke(tmp_path, ["setup"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "setup --update" in output
        assert "lexictl init" in output

    def test_setup_update_no_project_exits_1(self, tmp_path: Path) -> None:
        """``setup --update`` outside a project should exit 1."""
        result = self._invoke(tmp_path, ["setup", "--update"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]

    def test_setup_update_empty_env_shows_message(self, tmp_path: Path) -> None:
        """``setup --update`` with no agent environments shows a message and exits 1."""
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text(
            "scope_root: .\nagent_environment: []\n"
        )

        result = self._invoke(tmp_path, ["setup", "--update"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "No agent environments configured" in output
        assert "lexictl init" in output

    def test_setup_update_config_persisted_envs(self, tmp_path: Path) -> None:
        """``setup --update`` reads environments from config and generates rules."""
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text(
            "scope_root: .\nagent_environment:\n  - claude\n  - cursor\n"
        )

        result = self._invoke(tmp_path, ["setup", "--update"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "claude" in output
        assert "cursor" in output
        assert "Setup complete" in output
        # Verify files were actually created
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".cursor" / "rules" / "lexibrarian.mdc").exists()

    def test_setup_update_explicit_env_arg(self, tmp_path: Path) -> None:
        """``--env`` overrides config-persisted environments."""
        (tmp_path / ".lexibrary").mkdir()
        # Config has claude, but we explicitly request codex
        (tmp_path / ".lexibrary" / "config.yaml").write_text(
            "scope_root: .\nagent_environment:\n  - claude\n"
        )

        result = self._invoke(tmp_path, ["setup", "--update", "--env", "codex"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "codex" in output
        assert "Setup complete" in output
        # Codex file created, Claude file NOT created
        assert (tmp_path / "AGENTS.md").exists()
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_setup_update_explicit_env_overrides_empty_config(self, tmp_path: Path) -> None:
        """``--env`` works even when config has no environments."""
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text(
            "scope_root: .\nagent_environment: []\n"
        )

        result = self._invoke(tmp_path, ["setup", "--update", "--env", "claude"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "claude" in output
        assert "Setup complete" in output
        assert (tmp_path / "CLAUDE.md").exists()

    def test_setup_update_no_env_error(self, tmp_path: Path) -> None:
        """``setup --update`` with no config envs and no ``--env`` exits 1."""
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text("scope_root: .\n")

        result = self._invoke(tmp_path, ["setup", "--update"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "No agent environments configured" in output

    def test_setup_update_unsupported_env_error(self, tmp_path: Path) -> None:
        """``setup --update --env fake`` exits 1 with unsupported environment error."""
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text("scope_root: .\n")

        result = self._invoke(tmp_path, ["setup", "--update", "--env", "nonexistent"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "Unsupported" in output
        assert "nonexistent" in output
        # Should show supported environments
        assert "claude" in output

    def test_setup_update_unsupported_env_from_config(self, tmp_path: Path) -> None:
        """Config with unsupported environment exits 1 with clear error."""
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text(
            "scope_root: .\nagent_environment:\n  - vscode\n"
        )

        result = self._invoke(tmp_path, ["setup", "--update"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "Unsupported" in output
        assert "vscode" in output

    def test_setup_update_flag_generates_rules_and_gitignore(self, tmp_path: Path) -> None:
        """``--update`` generates rules AND adds IWH pattern to gitignore."""
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text(
            "scope_root: .\nagent_environment:\n  - claude\n"
        )

        result = self._invoke(tmp_path, ["setup", "--update"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        # Rules generated
        assert "claude" in output
        assert "file(s) written" in output
        # Gitignore updated
        assert ".gitignore" in output
        assert "IWH" in output
        # .gitignore file should exist with IWH pattern
        gitignore = (tmp_path / ".gitignore").read_text()
        assert "**/.iwh" in gitignore

    def test_setup_update_idempotent_gitignore(self, tmp_path: Path) -> None:
        """Running ``setup --update`` twice does not duplicate .gitignore pattern."""
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text(
            "scope_root: .\nagent_environment:\n  - claude\n"
        )
        # Pre-existing gitignore with pattern
        (tmp_path / ".gitignore").write_text("**/.iwh\n")

        result = self._invoke(tmp_path, ["setup", "--update"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        # Should NOT report gitignore modification
        assert ".gitignore" not in output
        # Pattern should appear only once
        gitignore = (tmp_path / ".gitignore").read_text()
        assert gitignore.count("**/.iwh") == 1

    def test_setup_update_multiple_envs(self, tmp_path: Path) -> None:
        """``setup --update`` with multiple --env flags generates for all."""
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text("scope_root: .\n")

        result = self._invoke(
            tmp_path, ["setup", "--update", "--env", "claude", "--env", "codex"]
        )
        assert result.exit_code == 0  # type: ignore[union-attr]
        output = result.output  # type: ignore[union-attr]
        assert "claude" in output
        assert "codex" in output
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "AGENTS.md").exists()


# ---------------------------------------------------------------------------
# Stub commands — should exit 0 with "Not yet implemented" when .lexibrary/ exists
# ---------------------------------------------------------------------------


class TestStubCommands:
    """Remaining stub commands print stub and exit 0 with project root."""

    def _invoke_in_project(self, tmp_path: Path, args: list[str]) -> object:
        (tmp_path / ".lexibrary").mkdir(exist_ok=True)
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(lexictl_app, args)
        finally:
            os.chdir(old_cwd)

    def test_daemon_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["daemon"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Commands without .lexibrary/ should exit 1 with friendly error (lexictl)
# ---------------------------------------------------------------------------


class TestNoProjectRoot:
    def _invoke_without_project(self, tmp_path: Path, args: list[str]) -> object:
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(lexictl_app, args)
        finally:
            os.chdir(old_cwd)

    def test_status_no_project_root(self, tmp_path: Path) -> None:
        result = self._invoke_without_project(tmp_path, ["status"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]

    def test_validate_no_project_root(self, tmp_path: Path) -> None:
        result = self._invoke_without_project(tmp_path, ["validate"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "lexictl init" in result.output  # type: ignore[union-attr]

    def test_daemon_no_project_root(self, tmp_path: Path) -> None:
        result = self._invoke_without_project(tmp_path, ["daemon"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]

    def test_update_no_project_root(self, tmp_path: Path) -> None:
        result = self._invoke_without_project(tmp_path, ["update"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]

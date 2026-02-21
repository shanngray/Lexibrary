"""Tests for the v2 CLI application."""

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
from lexibrarian.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------


class TestHelp:
    def test_help_lists_all_commands(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        for cmd in (
            "init",
            "lookup",
            "index",
            "concepts",
            "guardrails",
            "search",
            "update",
            "validate",
            "status",
            "setup",
            "daemon",
            "guardrail",
            "concept",
            "describe",
        ):
            assert cmd in result.output

    def test_help_mentions_lexibrary(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert ".lexibrary/" in result.output


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------


class TestInit:
    def test_init_creates_skeleton(self, tmp_path: Path, monkeypatch: object) -> None:
        import pytest  # noqa: F811

        monkeypatch_ = pytest.MonkeyPatch()  # type: ignore[attr-defined]
        monkeypatch_.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        monkeypatch_.undo()

        assert result.exit_code == 0
        assert "Created" in result.output
        assert (tmp_path / ".lexibrary" / "config.yaml").exists()
        assert (tmp_path / ".lexibrary" / "START_HERE.md").exists()
        assert (tmp_path / ".lexibrary" / "HANDOFF.md").exists()
        assert (tmp_path / ".lexibrary" / "concepts" / ".gitkeep").exists()
        assert (tmp_path / ".lexibrary" / "guardrails" / ".gitkeep").exists()

    def test_init_idempotent(self, tmp_path: Path) -> None:
        (tmp_path / ".lexibrary").mkdir()
        (tmp_path / ".lexibrary" / "config.yaml").write_text("existing")
        (tmp_path / ".lexibrary" / "START_HERE.md").write_text("existing")
        (tmp_path / ".lexibrary" / "HANDOFF.md").write_text("existing")
        (tmp_path / ".lexibrary" / "concepts").mkdir()
        (tmp_path / ".lexibrary" / "concepts" / ".gitkeep").touch()
        (tmp_path / ".lexibrary" / "guardrails").mkdir()
        (tmp_path / ".lexibrary" / "guardrails" / ".gitkeep").touch()
        (tmp_path / ".lexignore").write_text("")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["init"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "already exists" in result.output
        # Files not overwritten
        assert (tmp_path / ".lexibrary" / "config.yaml").read_text() == "existing"

    def test_init_agent_flag(self, tmp_path: Path) -> None:
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["init", "--agent", "claude"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "lexi setup claude" in result.output


# ---------------------------------------------------------------------------
# Index command
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


class TestIndexCommand:
    """Tests for the `lexi index` command."""

    def test_index_single_directory(self, tmp_path: Path) -> None:
        _setup_project(tmp_path)
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["index", "src"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Wrote" in result.output
        assert (tmp_path / ".lexibrary" / "src" / ".aindex").exists()

    def test_index_recursive(self, tmp_path: Path) -> None:
        _setup_project(tmp_path)
        # Add a subdirectory
        (tmp_path / "src" / "sub").mkdir()
        (tmp_path / "src" / "sub" / "mod.py").write_text("a = 1\n")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["index", "-r", "."])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Indexing complete" in result.output
        assert "directories indexed" in result.output
        # Root and src and src/sub should all have .aindex files
        assert (tmp_path / ".lexibrary" / "src" / ".aindex").exists()
        assert (tmp_path / ".lexibrary" / "src" / "sub" / ".aindex").exists()
        assert (tmp_path / ".lexibrary" / ".aindex").exists()

    def test_index_missing_project(self, tmp_path: Path) -> None:
        """Index should fail if no .lexibrary/ exists."""
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["index", "."])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "No .lexibrary/" in result.output

    def test_index_missing_directory(self, tmp_path: Path) -> None:
        """Index should fail if target directory does not exist."""
        _setup_project(tmp_path)
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["index", "nonexistent"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "Directory not found" in result.output

    def test_index_outside_project_root(self, tmp_path: Path) -> None:
        """Index should fail if target directory is outside the project root."""
        project = tmp_path / "project"
        project.mkdir()
        _setup_project(project)
        outside = tmp_path / "outside"
        outside.mkdir()

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            result = runner.invoke(app, ["index", str(outside)])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "outside the project root" in result.output


# ---------------------------------------------------------------------------
# Stub commands — should exit 0 with "Not yet implemented" when .lexibrary/ exists
# ---------------------------------------------------------------------------


class TestStubCommands:
    """All non-init commands should print stub and exit 0 with project root."""

    def _invoke_in_project(self, tmp_path: Path, args: list[str]) -> object:
        (tmp_path / ".lexibrary").mkdir(exist_ok=True)
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(app, args)
        finally:
            os.chdir(old_cwd)

    def test_guardrails_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["guardrails"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_search_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["search"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_validate_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["validate"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_status_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["status"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_setup_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["setup"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_daemon_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["daemon"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Commands without .lexibrary/ should exit 1 with friendly error
# ---------------------------------------------------------------------------


class TestNoProjectRoot:
    def _invoke_without_project(self, tmp_path: Path, args: list[str]) -> object:
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(app, args)
        finally:
            os.chdir(old_cwd)

    def test_status_no_project_root(self, tmp_path: Path) -> None:
        result = self._invoke_without_project(tmp_path, ["status"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]

    def test_validate_no_project_root(self, tmp_path: Path) -> None:
        result = self._invoke_without_project(tmp_path, ["validate"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "lexi init" in result.output  # type: ignore[union-attr]

    def test_daemon_no_project_root(self, tmp_path: Path) -> None:
        result = self._invoke_without_project(tmp_path, ["daemon"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Helpers for archivist CLI tests
# ---------------------------------------------------------------------------


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


def _create_aindex(tmp_path: Path, directory_rel: str, billboard: str) -> Path:
    """Create a .aindex file in the .lexibrary mirror tree."""
    aindex_path = tmp_path / ".lexibrary" / directory_rel / ".aindex"
    aindex_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().isoformat()
    content = f"""# {directory_rel}/

{billboard}

## Child Map

| Name | Type | Description |
| --- | --- | --- |
| `main.py` | file | Main module |
| `utils.py` | file | Utility functions |

## Local Conventions

(none)

<!-- lexibrarian:meta source="{directory_rel}" source_hash="abc123" """
    content += f"""generated="{now}" generator="lexibrarian-v2" -->
"""
    aindex_path.write_text(content, encoding="utf-8")
    return aindex_path


# ---------------------------------------------------------------------------
# Update command tests
# ---------------------------------------------------------------------------


class TestUpdateCommand:
    """Tests for the `lexi update` command."""

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
                result = runner.invoke(app, ["update", "src/main.py"])
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
                result = runner.invoke(app, ["update", "src"])
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
                result = runner.invoke(app, ["update"])
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
            result = runner.invoke(app, ["update"])
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
                result = runner.invoke(app, ["update", "src/main.py"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "Failed" in result.output


# ---------------------------------------------------------------------------
# Lookup command tests
# ---------------------------------------------------------------------------


class TestLookupCommand:
    """Tests for the `lexi lookup` command."""

    def test_lookup_exists(self, tmp_path: Path) -> None:
        """Lookup with existing design file prints its content."""
        project = _setup_archivist_project(tmp_path)
        source_content = "def hello():\n    pass\n"
        _create_design_file(project, "src/main.py", source_content)

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            result = runner.invoke(app, ["lookup", "src/main.py"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Interface Contract" in result.output

    def test_lookup_missing(self, tmp_path: Path) -> None:
        """Lookup without design file suggests running update."""
        project = _setup_archivist_project(tmp_path)

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            result = runner.invoke(app, ["lookup", "src/main.py"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "No design file found" in result.output
        assert "lexi update" in result.output

    def test_lookup_stale(self, tmp_path: Path) -> None:
        """Lookup with changed source file shows staleness warning."""
        project = _setup_archivist_project(tmp_path)
        # Create design file with the original content hash
        original_content = "def hello():\n    pass\n"
        _create_design_file(project, "src/main.py", original_content)

        # Now change the source file
        (project / "src" / "main.py").write_text("def hello():\n    return 42\n")

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            result = runner.invoke(app, ["lookup", "src/main.py"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Warning" in result.output
        assert "changed" in result.output

    def test_lookup_outside_scope(self, tmp_path: Path) -> None:
        """Lookup outside scope_root should print message and exit."""
        project = _setup_archivist_project(tmp_path)
        # Set scope_root to src/ only
        (project / ".lexibrary" / "config.yaml").write_text("scope_root: src\n")
        # Create a file outside scope
        (project / "scripts").mkdir()
        (project / "scripts" / "deploy.sh").write_text("#!/bin/bash\n")

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            result = runner.invoke(app, ["lookup", "scripts/deploy.sh"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "outside" in result.output


# ---------------------------------------------------------------------------
# Describe command tests
# ---------------------------------------------------------------------------


class TestDescribeCommand:
    """Tests for the `lexi describe` command."""

    def test_describe_directory(self, tmp_path: Path) -> None:
        """Describe updates the .aindex billboard for a directory."""
        project = _setup_archivist_project(tmp_path)
        _create_aindex(project, "src", "Old description of src")

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            result = runner.invoke(
                app, ["describe", "src", "Authentication and authorization services"]
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "Updated" in result.output

        # Verify the .aindex was actually updated
        aindex_content = (project / ".lexibrary" / "src" / ".aindex").read_text(encoding="utf-8")
        assert "Authentication and authorization services" in aindex_content

    def test_describe_missing_aindex(self, tmp_path: Path) -> None:
        """Describe with no .aindex suggests running index first."""
        project = _setup_archivist_project(tmp_path)

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            result = runner.invoke(app, ["describe", "src", "New description"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "No .aindex" in result.output
        assert "lexi index" in result.output

    def test_describe_missing_directory(self, tmp_path: Path) -> None:
        """Describe with nonexistent directory should fail."""
        project = _setup_archivist_project(tmp_path)

        old_cwd = os.getcwd()
        os.chdir(project)
        try:
            result = runner.invoke(app, ["describe", "nonexistent", "Description"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "Directory not found" in result.output

    def test_describe_no_project(self, tmp_path: Path) -> None:
        """Describe without .lexibrary should fail."""
        (tmp_path / "src").mkdir()

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(app, ["describe", "src", "Description"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 1
        assert "No .lexibrary/" in result.output


# ---------------------------------------------------------------------------
# Helper for concept tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Concepts command tests
# ---------------------------------------------------------------------------


class TestConceptsCommand:
    """Tests for the `lexi concepts` command."""

    def _invoke(self, tmp_path: Path, args: list[str]) -> object:
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(app, args)
        finally:
            os.chdir(old_cwd)

    def test_concepts_empty(self, tmp_path: Path) -> None:
        """Show message when no concepts exist."""
        _setup_project(tmp_path)
        result = self._invoke(tmp_path, ["concepts"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "No concepts found" in result.output  # type: ignore[union-attr]

    def test_concepts_list_all(self, tmp_path: Path) -> None:
        """List all concepts in a Rich table."""
        _setup_project(tmp_path)
        _create_concept_file(tmp_path, "Authentication", tags=["security"])
        _create_concept_file(tmp_path, "Rate Limiting", tags=["performance"])

        result = self._invoke(tmp_path, ["concepts"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Authentication" in result.output  # type: ignore[union-attr]
        assert "Rate Limiting" in result.output  # type: ignore[union-attr]

    def test_concepts_search(self, tmp_path: Path) -> None:
        """Search concepts by topic."""
        _setup_project(tmp_path)
        _create_concept_file(tmp_path, "Authentication", tags=["security"])
        _create_concept_file(tmp_path, "Rate Limiting", tags=["performance"])

        result = self._invoke(tmp_path, ["concepts", "auth"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Authentication" in result.output  # type: ignore[union-attr]
        assert "Rate Limiting" not in result.output  # type: ignore[union-attr]

    def test_concepts_search_no_match(self, tmp_path: Path) -> None:
        """Search with no matches shows message."""
        _setup_project(tmp_path)
        _create_concept_file(tmp_path, "Authentication", tags=["security"])

        result = self._invoke(tmp_path, ["concepts", "zzzzz"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "No concepts matching" in result.output  # type: ignore[union-attr]

    def test_concepts_no_project(self, tmp_path: Path) -> None:
        """Concepts without .lexibrary should fail."""
        result = self._invoke(tmp_path, ["concepts"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Concept new command tests
# ---------------------------------------------------------------------------


class TestConceptNewCommand:
    """Tests for the `lexi concept new` command."""

    def _invoke(self, tmp_path: Path, args: list[str]) -> object:
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(app, args)
        finally:
            os.chdir(old_cwd)

    def test_create_concept(self, tmp_path: Path) -> None:
        """Create a new concept file."""
        _setup_project(tmp_path)
        (tmp_path / ".lexibrary" / "concepts").mkdir(parents=True, exist_ok=True)

        result = self._invoke(tmp_path, ["concept", "new", "Rate Limiting"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Created" in result.output  # type: ignore[union-attr]
        assert (tmp_path / ".lexibrary" / "concepts" / "RateLimiting.md").exists()

    def test_create_concept_with_tags(self, tmp_path: Path) -> None:
        """Create a concept with tags."""
        _setup_project(tmp_path)
        (tmp_path / ".lexibrary" / "concepts").mkdir(parents=True, exist_ok=True)

        result = self._invoke(
            tmp_path, ["concept", "new", "Auth", "--tag", "security", "--tag", "core"]
        )
        assert result.exit_code == 0  # type: ignore[union-attr]

        content = (tmp_path / ".lexibrary" / "concepts" / "Auth.md").read_text()
        assert "security" in content
        assert "core" in content

    def test_create_concept_already_exists(self, tmp_path: Path) -> None:
        """Refuse to overwrite existing concept file."""
        _setup_project(tmp_path)
        _create_concept_file(tmp_path, "Authentication")

        result = self._invoke(tmp_path, ["concept", "new", "Authentication"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "already exists" in result.output  # type: ignore[union-attr]

    def test_create_concept_no_project(self, tmp_path: Path) -> None:
        """Concept new without .lexibrary should fail."""
        result = self._invoke(tmp_path, ["concept", "new", "Test"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]

    def test_create_concept_pascalcase(self, tmp_path: Path) -> None:
        """Concept name with spaces gets PascalCase filename."""
        _setup_project(tmp_path)
        (tmp_path / ".lexibrary" / "concepts").mkdir(parents=True, exist_ok=True)

        result = self._invoke(tmp_path, ["concept", "new", "my cool concept"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert (tmp_path / ".lexibrary" / "concepts" / "MyCoolConcept.md").exists()


# ---------------------------------------------------------------------------
# Concept link command tests
# ---------------------------------------------------------------------------


class TestConceptLinkCommand:
    """Tests for the `lexi concept link` command."""

    def _invoke(self, tmp_path: Path, args: list[str]) -> object:
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            return runner.invoke(app, args)
        finally:
            os.chdir(old_cwd)

    def test_link_concept(self, tmp_path: Path) -> None:
        """Link a concept to a source file's design file."""
        project = _setup_archivist_project(tmp_path)
        _create_concept_file(project, "Authentication")
        source_content = "def hello():\n    pass\n"
        _create_design_file(project, "src/main.py", source_content)

        result = self._invoke(project, ["concept", "link", "Authentication", "src/main.py"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Linked" in result.output  # type: ignore[union-attr]

        # Verify wikilink was added to design file
        design_content = (project / ".lexibrary" / "src" / "main.py.md").read_text(encoding="utf-8")
        assert "[[Authentication]]" in design_content

    def test_link_concept_already_linked(self, tmp_path: Path) -> None:
        """Linking an already-linked concept shows message."""
        project = _setup_archivist_project(tmp_path)
        _create_concept_file(project, "Authentication")
        source_content = "def hello():\n    pass\n"
        _create_design_file(project, "src/main.py", source_content)

        # Link once
        self._invoke(project, ["concept", "link", "Authentication", "src/main.py"])
        # Link again
        result = self._invoke(project, ["concept", "link", "Authentication", "src/main.py"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Already linked" in result.output  # type: ignore[union-attr]

    def test_link_concept_not_found(self, tmp_path: Path) -> None:
        """Linking a nonexistent concept should fail."""
        project = _setup_archivist_project(tmp_path)
        source_content = "def hello():\n    pass\n"
        _create_design_file(project, "src/main.py", source_content)

        result = self._invoke(project, ["concept", "link", "Nonexistent", "src/main.py"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "Concept not found" in result.output  # type: ignore[union-attr]

    def test_link_source_not_found(self, tmp_path: Path) -> None:
        """Linking to a nonexistent source file should fail."""
        project = _setup_archivist_project(tmp_path)
        _create_concept_file(project, "Authentication")

        result = self._invoke(project, ["concept", "link", "Authentication", "src/missing.py"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "Source file not found" in result.output  # type: ignore[union-attr]

    def test_link_no_design_file(self, tmp_path: Path) -> None:
        """Linking when no design file exists should suggest running update."""
        project = _setup_archivist_project(tmp_path)
        _create_concept_file(project, "Authentication")

        result = self._invoke(project, ["concept", "link", "Authentication", "src/main.py"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No design file found" in result.output  # type: ignore[union-attr]
        assert "lexi update" in result.output  # type: ignore[union-attr]

    def test_link_no_project(self, tmp_path: Path) -> None:
        """Concept link without .lexibrary should fail."""
        result = self._invoke(tmp_path, ["concept", "link", "Test", "file.py"])
        assert result.exit_code == 1  # type: ignore[union-attr]
        assert "No .lexibrary/" in result.output  # type: ignore[union-attr]

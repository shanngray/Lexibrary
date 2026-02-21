"""Unit tests for info-severity validation checks.

Tests check_forward_dependencies, check_stack_staleness, and check_aindex_coverage.
"""

from __future__ import annotations

from pathlib import Path

from lexibrarian.utils.hashing import hash_file
from lexibrarian.validator.checks import (
    check_aindex_coverage,
    check_forward_dependencies,
    check_stack_staleness,
)

# ---------------------------------------------------------------------------
# Helpers for writing test fixtures
# ---------------------------------------------------------------------------

_DESIGN_FILE_TEMPLATE = """\
---
description: {description}
updated_by: archivist
---

# {source_path}

## Interface Contract

```python
def example() -> None: ...
```

## Dependencies

{dependencies}

## Dependents

(none)

<!-- lexibrarian:meta
source: {source_path}
source_hash: {source_hash}
design_hash: deadbeef
generated: 2026-01-01T12:00:00
generator: lexibrarian-v2
-->
"""

_STACK_POST_TEMPLATE = """\
---
id: {post_id}
title: {title}
tags:
  - test
status: open
created: 2026-01-01
author: tester
refs:
  files:
{refs_files}
---

## Problem

Something was broken.

### A1

**Date:** 2026-01-01 | **Author:** tester | **Votes:** 0

The fix is to do X.
"""

_AINDEX_META = (
    '<!-- lexibrarian:meta source="{dir}" source_hash="abc123"'
    ' generated="2026-01-01T12:00:00" generator="lexibrarian-v2" -->'
)

_AINDEX_TEMPLATE = """\
# {directory_path}

{billboard}

## Child Map

| Name | Type | Description |
| --- | --- | --- |
{entries}

## Local Conventions

(none)

{meta}
"""


def _write_design_file(
    lexibrary_dir: Path,
    source_path: str,
    source_hash: str = "abc123",
    dependencies: str = "(none)",
    description: str = "Test design file",
) -> Path:
    """Write a design file to the expected mirror path."""
    design_path = lexibrary_dir / f"{source_path}.md"
    design_path.parent.mkdir(parents=True, exist_ok=True)
    design_path.write_text(
        _DESIGN_FILE_TEMPLATE.format(
            description=description,
            source_path=source_path,
            source_hash=source_hash,
            dependencies=dependencies,
        ),
        encoding="utf-8",
    )
    return design_path


def _write_stack_post(
    lexibrary_dir: Path,
    post_id: str,
    title: str,
    refs_files: list[str],
) -> Path:
    """Write a Stack post file."""
    stack_dir = lexibrary_dir / "stack"
    stack_dir.mkdir(parents=True, exist_ok=True)
    post_path = stack_dir / f"{post_id}.md"
    # Format refs.files as YAML list
    refs_lines = "\n".join(f"    - {f}" for f in refs_files) if refs_files else "    []"
    post_path.write_text(
        _STACK_POST_TEMPLATE.format(
            post_id=post_id,
            title=title,
            refs_files=refs_lines,
        ),
        encoding="utf-8",
    )
    return post_path


def _write_aindex(
    lexibrary_dir: Path,
    directory_path: str,
    billboard: str = "Test directory.",
) -> Path:
    """Write a .aindex file to the expected mirror path."""
    aindex = lexibrary_dir / directory_path / ".aindex"
    aindex.parent.mkdir(parents=True, exist_ok=True)
    meta = _AINDEX_META.format(dir=directory_path)
    aindex.write_text(
        _AINDEX_TEMPLATE.format(
            directory_path=directory_path,
            billboard=billboard,
            entries="(none)",
            meta=meta,
        ),
        encoding="utf-8",
    )
    return aindex


def _write_config(project_root: Path, scope_root: str = ".") -> None:
    """Write a minimal config.yaml."""
    config_dir = project_root / ".lexibrary"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(f"scope_root: {scope_root}\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# check_forward_dependencies
# ---------------------------------------------------------------------------


class TestCheckForwardDependencies:
    """Tests for check_forward_dependencies."""

    def test_all_dependencies_exist(self, tmp_path: Path) -> None:
        """When all dependency targets exist on disk, no issues are returned."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        # Create a source file
        src_dir = project_root / "src"
        src_dir.mkdir()
        source_file = src_dir / "main.py"
        source_file.write_text("print('hello')", encoding="utf-8")

        # Create a dependency target that exists
        dep_file = src_dir / "utils.py"
        dep_file.write_text("def helper(): pass", encoding="utf-8")

        # Create a design file that lists the dependency
        _write_design_file(
            lexibrary_dir,
            "src/main.py",
            dependencies="- src/utils.py",
        )

        issues = check_forward_dependencies(project_root, lexibrary_dir)
        assert len(issues) == 0

    def test_missing_dependency_produces_info(self, tmp_path: Path) -> None:
        """When a dependency target does not exist, an info issue is returned."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        # Create a design file referencing a non-existent dependency
        _write_design_file(
            lexibrary_dir,
            "src/main.py",
            dependencies="- src/missing_module.py",
        )

        issues = check_forward_dependencies(project_root, lexibrary_dir)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "info"
        assert issue.check == "forward_dependencies"
        assert "src/missing_module.py" in issue.message
        assert "missing_module.py" in issue.suggestion

    def test_none_dependency_ignored(self, tmp_path: Path) -> None:
        """Dependencies listed as '(none)' are skipped."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        _write_design_file(
            lexibrary_dir,
            "src/main.py",
            dependencies="(none)",
        )

        issues = check_forward_dependencies(project_root, lexibrary_dir)
        assert len(issues) == 0

    def test_multiple_deps_mixed(self, tmp_path: Path) -> None:
        """Mix of existing and missing dependencies produces issues only for missing."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        # Create one existing dependency
        src_dir = project_root / "src"
        src_dir.mkdir()
        (src_dir / "exists.py").write_text("pass", encoding="utf-8")

        _write_design_file(
            lexibrary_dir,
            "src/main.py",
            dependencies="- src/exists.py\n- src/gone.py",
        )

        issues = check_forward_dependencies(project_root, lexibrary_dir)
        assert len(issues) == 1
        assert "src/gone.py" in issues[0].message

    def test_empty_lexibrary(self, tmp_path: Path) -> None:
        """No design files means no issues."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        issues = check_forward_dependencies(project_root, lexibrary_dir)
        assert len(issues) == 0

    def test_nonexistent_lexibrary_dir(self, tmp_path: Path) -> None:
        """If .lexibrary doesn't exist, no issues (graceful)."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"

        issues = check_forward_dependencies(project_root, lexibrary_dir)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# check_stack_staleness
# ---------------------------------------------------------------------------


class TestCheckStackStaleness:
    """Tests for check_stack_staleness."""

    def test_unchanged_refs_pass(self, tmp_path: Path) -> None:
        """When all referenced files have fresh design files, no issues returned."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        # Create source file
        src_dir = project_root / "src"
        src_dir.mkdir()
        source_file = src_dir / "api.py"
        source_file.write_text("def handle(): pass", encoding="utf-8")

        # Compute current hash
        current_hash = hash_file(source_file)

        # Create design file with matching hash
        _write_design_file(
            lexibrary_dir,
            "src/api.py",
            source_hash=current_hash,
        )

        # Create stack post referencing the file
        _write_stack_post(
            lexibrary_dir,
            post_id="Q-001",
            title="How to handle requests",
            refs_files=["src/api.py"],
        )

        issues = check_stack_staleness(project_root, lexibrary_dir)
        assert len(issues) == 0

    def test_stale_ref_produces_info(self, tmp_path: Path) -> None:
        """When a referenced file's design file has a stale hash, info issue returned."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        # Create source file
        src_dir = project_root / "src"
        src_dir.mkdir()
        source_file = src_dir / "events.py"
        source_file.write_text("def emit(): pass", encoding="utf-8")

        # Create design file with a STALE hash (doesn't match current content)
        _write_design_file(
            lexibrary_dir,
            "src/events.py",
            source_hash="stale_hash_value",
        )

        # Create stack post referencing the file
        _write_stack_post(
            lexibrary_dir,
            post_id="Q-002",
            title="Event handling patterns",
            refs_files=["src/events.py"],
        )

        issues = check_stack_staleness(project_root, lexibrary_dir)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "info"
        assert issue.check == "stack_staleness"
        assert "Event handling patterns" in issue.message
        assert "src/events.py" in issue.message
        assert "Verify" in issue.suggestion

    def test_no_stack_posts(self, tmp_path: Path) -> None:
        """If no stack directory exists, no issues."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        issues = check_stack_staleness(project_root, lexibrary_dir)
        assert len(issues) == 0

    def test_stack_post_without_refs(self, tmp_path: Path) -> None:
        """Stack posts with no refs.files are skipped."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        _write_stack_post(
            lexibrary_dir,
            post_id="Q-003",
            title="General question",
            refs_files=[],
        )

        issues = check_stack_staleness(project_root, lexibrary_dir)
        assert len(issues) == 0

    def test_missing_design_file_not_flagged(self, tmp_path: Path) -> None:
        """If a referenced file has no design file, staleness can't be determined."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        # Create source file but NO design file
        src_dir = project_root / "src"
        src_dir.mkdir()
        (src_dir / "orphan.py").write_text("pass", encoding="utf-8")

        _write_stack_post(
            lexibrary_dir,
            post_id="Q-004",
            title="About orphan",
            refs_files=["src/orphan.py"],
        )

        issues = check_stack_staleness(project_root, lexibrary_dir)
        assert len(issues) == 0

    def test_missing_source_file_not_flagged(self, tmp_path: Path) -> None:
        """If the source file itself is missing, file_existence handles it."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()

        # Design file exists but source does not
        _write_design_file(
            lexibrary_dir,
            "src/gone.py",
            source_hash="whatever",
        )

        _write_stack_post(
            lexibrary_dir,
            post_id="Q-005",
            title="About gone module",
            refs_files=["src/gone.py"],
        )

        issues = check_stack_staleness(project_root, lexibrary_dir)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# check_aindex_coverage
# ---------------------------------------------------------------------------


class TestCheckAindexCoverage:
    """Tests for check_aindex_coverage."""

    def test_all_dirs_indexed(self, tmp_path: Path) -> None:
        """When every directory has an .aindex file, no issues returned."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()
        _write_config(project_root)

        # Create directory structure
        src_dir = project_root / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("pass", encoding="utf-8")

        # Create .aindex files for project_root (.) and src
        _write_aindex(lexibrary_dir, ".", billboard="Project root.")
        _write_aindex(lexibrary_dir, "src", billboard="Source code.")

        issues = check_aindex_coverage(project_root, lexibrary_dir)
        assert len(issues) == 0

    def test_unindexed_dir_produces_info(self, tmp_path: Path) -> None:
        """When a directory lacks an .aindex file, an info issue is returned."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()
        _write_config(project_root)

        # Create directory structure
        src_dir = project_root / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("pass", encoding="utf-8")

        # Only create .aindex for root, not src
        _write_aindex(lexibrary_dir, ".", billboard="Project root.")

        issues = check_aindex_coverage(project_root, lexibrary_dir)
        # Should flag the unindexed "src" directory
        src_issues = [i for i in issues if "src" in i.message]
        assert len(src_issues) == 1
        issue = src_issues[0]
        assert issue.severity == "info"
        assert issue.check == "aindex_coverage"
        assert "not indexed" in issue.message
        assert "lexi index" in issue.suggestion

    def test_hidden_dirs_skipped(self, tmp_path: Path) -> None:
        """Hidden directories (starting with .) are not checked."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()
        _write_config(project_root)

        # Create a hidden directory
        hidden_dir = project_root / ".hidden"
        hidden_dir.mkdir()

        # Create .aindex for root only
        _write_aindex(lexibrary_dir, ".", billboard="Project root.")

        issues = check_aindex_coverage(project_root, lexibrary_dir)
        # Should not flag .hidden
        hidden_issues = [i for i in issues if ".hidden" in i.message]
        assert len(hidden_issues) == 0

    def test_nested_unindexed_dirs(self, tmp_path: Path) -> None:
        """Nested directories without .aindex files produce individual issues."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()
        _write_config(project_root)

        # Create nested dirs
        deep = project_root / "src" / "core"
        deep.mkdir(parents=True)

        # Only index root
        _write_aindex(lexibrary_dir, ".", billboard="Project root.")

        issues = check_aindex_coverage(project_root, lexibrary_dir)
        messages = [i.message for i in issues]
        assert any("src" in m for m in messages)
        assert any("core" in m for m in messages)

    def test_empty_project(self, tmp_path: Path) -> None:
        """Project with no subdirectories only checks root."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()
        _write_config(project_root)

        # Index root
        _write_aindex(lexibrary_dir, ".", billboard="Empty project.")

        issues = check_aindex_coverage(project_root, lexibrary_dir)
        assert len(issues) == 0

    def test_scope_root_respected(self, tmp_path: Path) -> None:
        """Only directories under scope_root are checked."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"
        lexibrary_dir.mkdir()
        _write_config(project_root, scope_root="src")

        # Create dirs inside and outside scope_root
        src_dir = project_root / "src"
        src_dir.mkdir()
        docs_dir = project_root / "docs"
        docs_dir.mkdir()

        # Index src
        _write_aindex(lexibrary_dir, "src", billboard="Source code.")

        issues = check_aindex_coverage(project_root, lexibrary_dir)
        # docs is outside scope_root, should not be flagged
        docs_issues = [i for i in issues if "docs" in i.message]
        assert len(docs_issues) == 0

    def test_nonexistent_lexibrary_dir(self, tmp_path: Path) -> None:
        """If .lexibrary doesn't exist, graceful handling."""
        project_root = tmp_path
        lexibrary_dir = project_root / ".lexibrary"

        issues = check_aindex_coverage(project_root, lexibrary_dir)
        # The config load will fail but should be handled gracefully
        # The scope_root walk should still work
        assert isinstance(issues, list)

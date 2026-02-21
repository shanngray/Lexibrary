"""Tests for init/scaffolder.py — .lexibrary/ skeleton creation."""

from __future__ import annotations

from pathlib import Path

from lexibrarian.init.scaffolder import create_lexibrary_skeleton


def test_creates_stack_directory(tmp_path: Path) -> None:
    """lexi init creates .lexibrary/stack/ directory."""
    create_lexibrary_skeleton(tmp_path)

    stack_dir = tmp_path / ".lexibrary" / "stack"
    assert stack_dir.is_dir(), ".lexibrary/stack/ should be created"
    assert (stack_dir / ".gitkeep").exists(), ".lexibrary/stack/.gitkeep should exist"


def test_does_not_create_guardrails_directory(tmp_path: Path) -> None:
    """lexi init does NOT create .lexibrary/guardrails/ directory."""
    create_lexibrary_skeleton(tmp_path)

    guardrails_dir = tmp_path / ".lexibrary" / "guardrails"
    assert not guardrails_dir.exists(), ".lexibrary/guardrails/ should NOT be created"


def test_creates_full_skeleton(tmp_path: Path) -> None:
    """lexi init creates the complete .lexibrary/ skeleton with expected dirs."""
    created = create_lexibrary_skeleton(tmp_path)

    base = tmp_path / ".lexibrary"
    assert base.is_dir()
    assert (base / "concepts").is_dir()
    assert (base / "stack").is_dir()
    assert (base / "config.yaml").is_file()
    assert (base / "START_HERE.md").is_file()
    assert (base / "HANDOFF.md").is_file()
    assert (tmp_path / ".lexignore").is_file()
    assert len(created) > 0


def test_idempotent(tmp_path: Path) -> None:
    """Running create_lexibrary_skeleton twice returns empty list on second call."""
    create_lexibrary_skeleton(tmp_path)
    second_run = create_lexibrary_skeleton(tmp_path)
    assert second_run == [], "Second call should create nothing"

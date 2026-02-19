"""Tests for the v2 CLI application."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

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
            "init", "lookup", "index", "concepts", "guardrails",
            "search", "update", "validate", "status", "setup", "daemon",
            "guardrail",
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

    def test_lookup_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["lookup", "foo.py"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_index_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["index"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_concepts_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["concepts"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_guardrails_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["guardrails"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_search_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["search"])
        assert result.exit_code == 0  # type: ignore[union-attr]
        assert "Not yet implemented" in result.output  # type: ignore[union-attr]

    def test_update_stub(self, tmp_path: Path) -> None:
        result = self._invoke_in_project(tmp_path, ["update"])
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

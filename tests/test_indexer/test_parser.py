from __future__ import annotations

from pathlib import Path

from lexibrarian.indexer import DirEntry, FileEntry
from lexibrarian.indexer.parser import get_cached_file_entries, parse_iandex

VALID_IANDEX = """\
# myproject/

A sample project with multiple modules.

## Files

| File | Tokens | Description |
| --- | --- | --- |
| `cli.py` | 150 | CLI entry point |
| `config.py` | 200 | Configuration loading |

## Subdirectories

| Directory | Description |
| --- | --- |
| `utils/` | Utility functions |
"""


class TestParseIandex:
    def test_basic_parse(self, tmp_path: Path) -> None:
        p = tmp_path / ".aindex"
        p.write_text(VALID_IANDEX, encoding="utf-8")
        data = parse_iandex(p)
        assert data is not None
        assert data.directory_name == "myproject/"
        assert data.summary == "A sample project with multiple modules."
        assert len(data.files) == 2
        assert data.files[0] == FileEntry("cli.py", 150, "CLI entry point")
        assert data.files[1] == FileEntry("config.py", 200, "Configuration loading")
        assert len(data.subdirectories) == 1
        assert data.subdirectories[0] == DirEntry("utils/", "Utility functions")

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        result = parse_iandex(tmp_path / "does_not_exist")
        assert result is None

    def test_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / ".aindex"
        p.write_text("", encoding="utf-8")
        assert parse_iandex(p) is None

    def test_malformed_no_h1(self, tmp_path: Path) -> None:
        p = tmp_path / ".aindex"
        p.write_text("just some random text\nwithout heading\n", encoding="utf-8")
        assert parse_iandex(p) is None

    def test_empty_sections_none_marker(self, tmp_path: Path) -> None:
        content = """\
# empty/

Nothing here.

## Files

(none)

## Subdirectories

(none)
"""
        p = tmp_path / ".aindex"
        p.write_text(content, encoding="utf-8")
        data = parse_iandex(p)
        assert data is not None
        assert data.files == []
        assert data.subdirectories == []

    def test_pipe_in_description(self, tmp_path: Path) -> None:
        content = """\
# pipes/

Pipe test.

## Files

| File | Tokens | Description |
| --- | --- | --- |
| `io.py` | 50 | Handles input \\| output |

## Subdirectories

(none)
"""
        p = tmp_path / ".aindex"
        p.write_text(content, encoding="utf-8")
        data = parse_iandex(p)
        assert data is not None
        assert data.files[0].description == "Handles input | output"

    def test_multi_line_summary(self, tmp_path: Path) -> None:
        content = """\
# proj/

First sentence.
Second sentence.

## Files

(none)

## Subdirectories

(none)
"""
        p = tmp_path / ".aindex"
        p.write_text(content, encoding="utf-8")
        data = parse_iandex(p)
        assert data is not None
        assert data.summary == "First sentence. Second sentence."


class TestGetCachedFileEntries:
    def test_returns_dict(self, tmp_path: Path) -> None:
        p = tmp_path / ".aindex"
        p.write_text(VALID_IANDEX, encoding="utf-8")
        result = get_cached_file_entries(p)
        assert "cli.py" in result
        assert "config.py" in result
        assert result["cli.py"] == FileEntry("cli.py", 150, "CLI entry point")

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = get_cached_file_entries(tmp_path / "nope")
        assert result == {}

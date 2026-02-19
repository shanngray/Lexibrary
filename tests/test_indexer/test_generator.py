"""Tests for the index generator."""

from __future__ import annotations

from pathlib import Path

import pathspec

from lexibrarian.artifacts.aindex_serializer import serialize_aindex
from lexibrarian.ignore.matcher import IgnoreMatcher
from lexibrarian.indexer.generator import generate_aindex

_BINARY_EXTS: set[str] = {".png", ".jpg", ".gif", ".pdf", ".exe", ".zip"}


def _matcher(root: Path, patterns: list[str] | None = None) -> IgnoreMatcher:
    """Build an IgnoreMatcher with optional config patterns and no gitignore specs."""
    spec = pathspec.PathSpec.from_lines("gitignore", patterns or [])
    return IgnoreMatcher(root=root, config_spec=spec, gitignore_specs=[])


class TestGenerateAIndexEmptyDir:
    def test_empty_dir_returns_empty_entries(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert result.entries == []

    def test_empty_dir_billboard(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert result.billboard == "Empty directory."

    def test_empty_dir_local_conventions_empty(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert result.local_conventions == []


class TestGenerateAIndexFiles:
    def test_python_file_description(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("line1\nline2\nline3\n", encoding="utf-8")
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        entry = next(e for e in result.entries if e.name == "main.py")
        assert entry.description == "Python source (3 lines)"
        assert entry.entry_type == "file"

    def test_binary_file_description(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "logo.png").write_bytes(b"\x89PNG")
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        entry = next(e for e in result.entries if e.name == "logo.png")
        assert entry.description == "Binary file (.png)"

    def test_unknown_extension_description(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "data.xyz").write_text("content", encoding="utf-8")
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        entry = next(e for e in result.entries if e.name == "data.xyz")
        assert entry.description == "Unknown file type"

    def test_single_language_billboard(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "foo.py").write_text("x\n", encoding="utf-8")
        (src / "bar.py").write_text("y\n", encoding="utf-8")
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert result.billboard == "Directory containing Python source files."

    def test_mixed_language_billboard(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text("x\n", encoding="utf-8")
        (src / "index.js").write_text("y\n", encoding="utf-8")
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert result.billboard.startswith("Mixed-language directory (")
        assert "Python" in result.billboard
        assert "JavaScript" in result.billboard

    def test_binary_only_billboard(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "logo.png").write_bytes(b"\x89PNG")
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert result.billboard == "Directory containing binary and data files."


class TestGenerateAIndexDirectories:
    def test_subdir_without_child_aindex_uses_direct_count(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        utils = src / "utils"
        utils.mkdir()
        (utils / "a.py").write_text("", encoding="utf-8")
        (utils / "b.py").write_text("", encoding="utf-8")
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        entry = next(e for e in result.entries if e.name == "utils")
        assert entry.entry_type == "dir"
        assert entry.description == "Contains 2 items"

    def test_subdir_with_child_aindex_uses_entry_counts(self, tmp_path: Path) -> None:
        from datetime import datetime

        from lexibrarian.artifacts.aindex import AIndexEntry, AIndexFile
        from lexibrarian.artifacts.design_file import StalenessMetadata

        src = tmp_path / "src"
        src.mkdir()
        utils = src / "utils"
        utils.mkdir()

        # Build a child .aindex for utils in the .lexibrary mirror
        meta = StalenessMetadata(
            source="src/utils",
            source_hash="abc",
            generated=datetime(2026, 1, 1),
            generator="lexibrarian-v2",
        )
        child_model = AIndexFile(
            directory_path="src/utils",
            billboard="Utils.",
            entries=[
                AIndexEntry(name="a.py", entry_type="file", description="Python source (1 lines)"),
                AIndexEntry(name="b.py", entry_type="file", description="Python source (2 lines)"),
                AIndexEntry(name="sub", entry_type="dir", description="Contains 1 items"),
            ],
            metadata=meta,
        )
        mirror_dir = tmp_path / ".lexibrary" / "src" / "utils"
        mirror_dir.mkdir(parents=True)
        (mirror_dir / ".aindex").write_text(serialize_aindex(child_model), encoding="utf-8")

        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        entry = next(e for e in result.entries if e.name == "utils")
        assert entry.description == "Contains 2 files, 1 subdirectories"

    def test_subdir_with_files_only_aindex_omits_subdir_count(self, tmp_path: Path) -> None:
        from datetime import datetime

        from lexibrarian.artifacts.aindex import AIndexEntry, AIndexFile
        from lexibrarian.artifacts.design_file import StalenessMetadata

        src = tmp_path / "src"
        src.mkdir()
        utils = src / "utils"
        utils.mkdir()

        meta = StalenessMetadata(
            source="src/utils",
            source_hash="abc",
            generated=datetime(2026, 1, 1),
            generator="lexibrarian-v2",
        )
        child_model = AIndexFile(
            directory_path="src/utils",
            billboard="Utils.",
            entries=[
                AIndexEntry(name="a.py", entry_type="file", description="Python source (1 lines)"),
            ],
            metadata=meta,
        )
        mirror_dir = tmp_path / ".lexibrary" / "src" / "utils"
        mirror_dir.mkdir(parents=True)
        (mirror_dir / ".aindex").write_text(serialize_aindex(child_model), encoding="utf-8")

        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        entry = next(e for e in result.entries if e.name == "utils")
        assert entry.description == "Contains 1 files"


class TestGenerateAIndexIgnored:
    def test_ignored_entries_excluded(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "keep.py").write_text("x\n", encoding="utf-8")
        (src / "skip.log").write_text("log\n", encoding="utf-8")
        matcher = _matcher(tmp_path, ["*.log"])
        result = generate_aindex(src, tmp_path, matcher, _BINARY_EXTS)
        names = [e.name for e in result.entries]
        assert "keep.py" in names
        assert "skip.log" not in names

    def test_ignored_dir_excluded(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x\n", encoding="utf-8")
        pycache = src / "__pycache__"
        pycache.mkdir()
        matcher = _matcher(tmp_path, ["__pycache__/"])
        result = generate_aindex(src, tmp_path, matcher, _BINARY_EXTS)
        names = [e.name for e in result.entries]
        assert "__pycache__" not in names


class TestGenerateAIndexMetadata:
    def test_metadata_source_is_relative_path(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert result.metadata.source == "src"
        assert result.directory_path == "src"

    def test_metadata_source_hash_is_hex(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "foo.py").write_text("x\n", encoding="utf-8")
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert len(result.metadata.source_hash) == 64
        assert all(c in "0123456789abcdef" for c in result.metadata.source_hash)

    def test_metadata_generator(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert result.metadata.generator == "lexibrarian-v2"

    def test_metadata_generated_is_datetime(self, tmp_path: Path) -> None:
        from datetime import datetime

        src = tmp_path / "src"
        src.mkdir()
        result = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert isinstance(result.metadata.generated, datetime)

    def test_source_hash_changes_with_directory_contents(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        r1 = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        (src / "new.py").write_text("x\n", encoding="utf-8")
        r2 = generate_aindex(src, tmp_path, _matcher(tmp_path), _BINARY_EXTS)
        assert r1.metadata.source_hash != r2.metadata.source_hash

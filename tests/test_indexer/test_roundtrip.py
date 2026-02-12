from __future__ import annotations

from pathlib import Path

from lexibrarian.indexer import DirEntry, FileEntry, IandexData
from lexibrarian.indexer.generator import generate_iandex
from lexibrarian.indexer.parser import parse_iandex
from lexibrarian.indexer.writer import write_iandex


class TestRoundTrip:
    def test_roundtrip_with_data(self, tmp_path: Path) -> None:
        original = IandexData(
            directory_name="lexibrarian/",
            summary="Main package with CLI and configuration.",
            files=[
                FileEntry("cli.py", 150, "CLI entry point"),
                FileEntry("config.py", 200, "Configuration loading"),
            ],
            subdirectories=[
                DirEntry("utils/", "Utility functions"),
                DirEntry("indexer/", "Index file handling"),
            ],
        )
        content = generate_iandex(original)
        path = write_iandex(tmp_path, content)
        parsed = parse_iandex(path)

        assert parsed is not None
        assert parsed.directory_name == original.directory_name
        assert parsed.summary == original.summary
        # Files are sorted by generator, compare sorted versions
        sorted_files = sorted(original.files, key=lambda f: f.name.lower())
        assert parsed.files == sorted_files
        sorted_dirs = sorted(original.subdirectories, key=lambda d: d.name.lower())
        assert parsed.subdirectories == sorted_dirs

    def test_roundtrip_empty(self, tmp_path: Path) -> None:
        original = IandexData(
            directory_name="empty/",
            summary="An empty directory.",
        )
        content = generate_iandex(original)
        path = write_iandex(tmp_path, content)
        parsed = parse_iandex(path)

        assert parsed is not None
        assert parsed.directory_name == original.directory_name
        assert parsed.summary == original.summary
        assert parsed.files == []
        assert parsed.subdirectories == []

    def test_roundtrip_unicode(self, tmp_path: Path) -> None:
        original = IandexData(
            directory_name="proyecto/",
            summary="Proyecto con caracteres especiales: ñ, ü, 日本語.",
            files=[
                FileEntry("café.py", 42, "Manejo de café"),
                FileEntry("日本.py", 99, "日本語のモジュール"),
            ],
            subdirectories=[
                DirEntry("données/", "Répertoire de données"),
            ],
        )
        content = generate_iandex(original)
        path = write_iandex(tmp_path, content)
        parsed = parse_iandex(path)

        assert parsed is not None
        assert parsed.directory_name == original.directory_name
        assert parsed.summary == original.summary
        sorted_files = sorted(original.files, key=lambda f: f.name.lower())
        assert parsed.files == sorted_files
        assert parsed.subdirectories == original.subdirectories

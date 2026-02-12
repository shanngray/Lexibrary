from __future__ import annotations

import contextlib
from pathlib import Path
from unittest.mock import patch

from lexibrarian.indexer.writer import write_iandex


class TestWriteIandex:
    def test_creates_file(self, tmp_path: Path) -> None:
        result = write_iandex(tmp_path, "hello")
        assert result == tmp_path / ".aindex"
        assert result.exists()

    def test_content_matches(self, tmp_path: Path) -> None:
        content = "# test/\n\nSummary.\n"
        write_iandex(tmp_path, content)
        assert (tmp_path / ".aindex").read_text(encoding="utf-8") == content

    def test_overwrite(self, tmp_path: Path) -> None:
        write_iandex(tmp_path, "first")
        write_iandex(tmp_path, "second")
        assert (tmp_path / ".aindex").read_text(encoding="utf-8") == "second"

    def test_custom_filename(self, tmp_path: Path) -> None:
        result = write_iandex(tmp_path, "backup", filename=".aindex.bak")
        assert result == tmp_path / ".aindex.bak"
        assert result.read_text(encoding="utf-8") == "backup"

    def test_utf8_content(self, tmp_path: Path) -> None:
        content = "# proyecto/\n\nResumen con ñ y 日本語.\n"
        write_iandex(tmp_path, content)
        assert (tmp_path / ".aindex").read_text(encoding="utf-8") == content

    def test_atomic_no_partial_on_failure(self, tmp_path: Path) -> None:
        # Write initial content
        write_iandex(tmp_path, "original")

        # Simulate a write failure — patch os.fdopen's returned file to fail on write
        with patch("lexibrarian.indexer.writer.os.fdopen") as mock_fdopen:
            mock_file = mock_fdopen.return_value.__enter__.return_value
            mock_file.write.side_effect = OSError("disk full")

            with contextlib.suppress(OSError):
                write_iandex(tmp_path, "should not appear")

        # Original file should still have original content
        assert (tmp_path / ".aindex").read_text(encoding="utf-8") == "original"

        # No temp files left behind
        remaining = list(tmp_path.glob(".aindex_tmp_*"))
        assert remaining == []

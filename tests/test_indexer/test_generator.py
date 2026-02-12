from __future__ import annotations

from lexibrarian.indexer import DirEntry, FileEntry, IandexData
from lexibrarian.indexer.generator import generate_iandex


class TestGenerateIandex:
    def test_basic_generation(self) -> None:
        data = IandexData(
            directory_name="myproject/",
            summary="A sample project.",
            files=[FileEntry("cli.py", 150, "CLI entry point")],
            subdirectories=[DirEntry("config/", "Configuration loading")],
        )
        result = generate_iandex(data)
        assert result.startswith("# myproject/\n")
        assert "A sample project." in result
        assert "| `cli.py` | 150 | CLI entry point |" in result
        assert "| `config/` | Configuration loading |" in result

    def test_no_files(self) -> None:
        data = IandexData(
            directory_name="empty/",
            summary="Nothing here.",
            files=[],
            subdirectories=[DirEntry("sub/", "A subdirectory")],
        )
        result = generate_iandex(data)
        assert "## Files\n\n(none)" in result
        assert "| File |" not in result

    def test_no_subdirs(self) -> None:
        data = IandexData(
            directory_name="flat/",
            summary="No subdirs.",
            files=[FileEntry("main.py", 100, "Main module")],
            subdirectories=[],
        )
        result = generate_iandex(data)
        assert "## Subdirectories\n\n(none)" in result
        assert "| Directory |" not in result

    def test_empty(self) -> None:
        data = IandexData(
            directory_name="bare/",
            summary="Empty directory.",
        )
        result = generate_iandex(data)
        assert "## Files\n\n(none)" in result
        assert "## Subdirectories\n\n(none)" in result

    def test_case_insensitive_file_sorting(self) -> None:
        data = IandexData(
            directory_name="sorted/",
            summary="Sorted files.",
            files=[
                FileEntry("Zebra.py", 10, "Z file"),
                FileEntry("alpha.py", 20, "A file"),
                FileEntry("Beta.py", 30, "B file"),
            ],
        )
        result = generate_iandex(data)
        alpha_pos = result.index("`alpha.py`")
        beta_pos = result.index("`Beta.py`")
        zebra_pos = result.index("`Zebra.py`")
        assert alpha_pos < beta_pos < zebra_pos

    def test_case_insensitive_dir_sorting(self) -> None:
        data = IandexData(
            directory_name="sorted/",
            summary="Sorted dirs.",
            subdirectories=[
                DirEntry("Zutils/", "Z utils"),
                DirEntry("api/", "API layer"),
                DirEntry("Config/", "Config stuff"),
            ],
        )
        result = generate_iandex(data)
        api_pos = result.index("`api/`")
        config_pos = result.index("`Config/`")
        zutils_pos = result.index("`Zutils/`")
        assert api_pos < config_pos < zutils_pos

    def test_trailing_slash_enforcement(self) -> None:
        data = IandexData(
            directory_name="root/",
            summary="Root.",
            subdirectories=[DirEntry("notrail", "Missing slash")],
        )
        result = generate_iandex(data)
        assert "`notrail/`" in result

    def test_trailing_newline(self) -> None:
        data = IandexData(directory_name="dir/", summary="S.")
        result = generate_iandex(data)
        assert result.endswith("\n")

    def test_pipe_escaping(self) -> None:
        data = IandexData(
            directory_name="pipes/",
            summary="Pipe test.",
            files=[FileEntry("io.py", 50, "Handles input | output streams")],
            subdirectories=[DirEntry("a|b/", "Dir with | pipe")],
        )
        result = generate_iandex(data)
        assert "Handles input \\| output streams" in result
        assert "Dir with \\| pipe" in result

    def test_blank_line_separation(self) -> None:
        data = IandexData(
            directory_name="sep/",
            summary="Separation test.",
            files=[FileEntry("a.py", 1, "A")],
            subdirectories=[DirEntry("b/", "B")],
        )
        result = generate_iandex(data)
        # blank line between H1 and summary
        assert "# sep/\n\nSeparation test." in result
        # blank line between summary and Files
        assert "Separation test.\n\n## Files" in result
        # blank line between Files section and Subdirectories
        assert "|\n\n## Subdirectories" in result

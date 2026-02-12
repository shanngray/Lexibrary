from __future__ import annotations

import re
from pathlib import Path

from lexibrarian.indexer import DirEntry, FileEntry, IandexData

_FILE_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|$"
)
_DIR_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|$"
)


def _unescape_pipe(text: str) -> str:
    """Unescape \\| back to literal pipe characters."""
    return text.replace("\\|", "|")


def parse_iandex(path: Path) -> IandexData | None:
    """Parse an .aindex file into IandexData.

    Returns None for missing, empty, or malformed files.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if not text.strip():
        return None

    lines = text.split("\n")

    # H1 header
    if not lines[0].startswith("# "):
        return None
    directory_name = lines[0][2:].strip()

    # Find summary lines between H1 and first H2
    summary_lines: list[str] = []
    files: list[FileEntry] = []
    subdirectories: list[DirEntry] = []

    current_section: str | None = None
    i = 1
    while i < len(lines):
        line = lines[i]

        if line.startswith("## Files"):
            current_section = "files"
            i += 1
            continue
        if line.startswith("## Subdirectories"):
            current_section = "subdirs"
            i += 1
            continue
        if line.startswith("## "):
            current_section = "other"
            i += 1
            continue

        if current_section is None:
            # Between H1 and first H2 — summary area
            stripped = line.strip()
            if stripped:
                summary_lines.append(stripped)
        elif current_section == "files":
            m = _FILE_ROW_RE.match(line)
            if m:
                files.append(
                    FileEntry(
                        name=m.group(1),
                        tokens=int(m.group(2)),
                        description=_unescape_pipe(m.group(3)),
                    )
                )
        elif current_section == "subdirs":
            m = _DIR_ROW_RE.match(line)
            if m:
                subdirectories.append(
                    DirEntry(
                        name=m.group(1),
                        description=_unescape_pipe(m.group(2)),
                    )
                )

        i += 1

    summary = " ".join(summary_lines)

    return IandexData(
        directory_name=directory_name,
        summary=summary,
        files=files,
        subdirectories=subdirectories,
    )


def get_cached_file_entries(iandex_path: Path) -> dict[str, FileEntry]:
    """Parse an .aindex file and return file entries keyed by filename.

    Returns an empty dict if the file is missing or malformed.
    """
    data = parse_iandex(iandex_path)
    if data is None:
        return {}
    return {entry.name: entry for entry in data.files}

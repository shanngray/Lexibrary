from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FileEntry:
    """A file entry in an .aindex index."""

    name: str
    tokens: int
    description: str


@dataclass
class DirEntry:
    """A subdirectory entry in an .aindex index."""

    name: str
    description: str


@dataclass
class IandexData:
    """The structured contents of a single .aindex file."""

    directory_name: str
    summary: str
    files: list[FileEntry] = field(default_factory=list)
    subdirectories: list[DirEntry] = field(default_factory=list)

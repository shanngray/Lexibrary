"""Pydantic 2 models for .aindex file artifacts."""

from __future__ import annotations

from pydantic import BaseModel

from lexibrarian.artifacts.design_file import StalenessMetadata


class AIndexEntry(BaseModel):
    """A single entry in a directory's .aindex file."""

    name: str
    description: str
    is_directory: bool


class AIndexFile(BaseModel):
    """Represents a .aindex file artifact for a directory."""

    directory_path: str
    billboard: str
    entries: list[AIndexEntry]
    local_conventions: list[str] = []
    metadata: StalenessMetadata

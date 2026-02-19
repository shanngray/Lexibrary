"""Pydantic 2 model for concept file artifacts."""

from __future__ import annotations

from pydantic import BaseModel

from lexibrarian.artifacts.design_file import StalenessMetadata


class ConceptFile(BaseModel):
    """Represents a concept file artifact."""

    name: str
    summary: str
    linked_files: list[str] = []
    tags: list[str] = []
    decision_log: list[str] = []
    wikilinks: list[str] = []
    metadata: StalenessMetadata | None = None

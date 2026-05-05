"""Conventions module -- convention file parser, serializer, and index utilities."""

from __future__ import annotations

from lexibrary.conventions.index import ConventionIndex
from lexibrary.conventions.parser import (
    ConventionValidationError,
    parse_convention_file,
    parse_convention_file_strict,
)
from lexibrary.conventions.serializer import serialize_convention_file

__all__ = [
    "ConventionIndex",
    "ConventionValidationError",
    "parse_convention_file",
    "parse_convention_file_strict",
    "serialize_convention_file",
]

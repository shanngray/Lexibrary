"""Project-level exception classes for Lexibrarian."""

from __future__ import annotations


class LexibraryNotFoundError(Exception):
    """Raised when no .lexibrary/ directory is found walking up from the start path."""

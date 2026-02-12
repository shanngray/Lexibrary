"""Path utilities for project root discovery."""

from __future__ import annotations

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """
    Find project root by walking upward looking for .git or lexibrary.toml.

    Args:
        start: Directory to start search from. Defaults to current working directory.

    Returns:
        Path to project root directory. Falls back to current working directory
        if no root markers found.
    """
    start = Path.cwd() if start is None else Path(start).resolve()

    current = start
    while True:
        # Check for root markers
        if (current / ".git").exists() or (current / "lexibrary.toml").exists():
            return current

        # Stop at filesystem root
        if current.parent == current:
            break

        current = current.parent

    # No root found, return current working directory
    return Path.cwd()

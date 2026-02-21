"""Create the .lexibrary/ directory skeleton for a new project."""

from __future__ import annotations

from pathlib import Path

from lexibrarian.config.defaults import DEFAULT_PROJECT_CONFIG_TEMPLATE

LEXIBRARY_DIR = ".lexibrary"

LEXIGNORE_HEADER = """\
# .lexignore — Lexibrarian-specific ignore patterns
# Files matching these patterns will NOT receive design files, even if tracked by git.
# Uses .gitignore format and rules.
# Example: **/migrations/
"""

START_HERE_PLACEHOLDER = """\
# START HERE

This library has not been generated yet.

Run `lexi update` to crawl the project and generate the full Lexibrarian library.
"""

HANDOFF_PLACEHOLDER = """\
# Handoff

**Task:** No active session
**Status:** No active session
**Next step:** No active session
**Key files:** No active session
**Watch out:** No active session
"""


def create_lexibrary_skeleton(project_root: Path) -> list[Path]:
    """Create the ``.lexibrary/`` directory skeleton at *project_root*.

    Idempotent — existing files are never overwritten.

    Args:
        project_root: Absolute path to the project root directory.

    Returns:
        List of paths that were created (empty if skeleton already exists).
    """
    base = project_root / LEXIBRARY_DIR
    created: list[Path] = []

    # Directories
    for subdir in [base, base / "concepts", base / "stack"]:
        if not subdir.exists():
            subdir.mkdir(parents=True)
            created.append(subdir)

    # .gitkeep files for empty directories
    for gitkeep in [base / "concepts" / ".gitkeep", base / "stack" / ".gitkeep"]:
        if not gitkeep.exists():
            gitkeep.touch()
            created.append(gitkeep)

    # Template files — never overwrite existing
    files: dict[Path, str] = {
        base / "config.yaml": DEFAULT_PROJECT_CONFIG_TEMPLATE,
        base / "START_HERE.md": START_HERE_PLACEHOLDER,
        base / "HANDOFF.md": HANDOFF_PLACEHOLDER,
        project_root / ".lexignore": LEXIGNORE_HEADER,
    }
    for path, content in files.items():
        if not path.exists():
            path.write_text(content)
            created.append(path)

    return created

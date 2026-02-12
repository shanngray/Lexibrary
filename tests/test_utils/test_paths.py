"""Tests for path utilities."""

from __future__ import annotations

from pathlib import Path

from lexibrarian.utils.paths import find_project_root


def test_find_project_root_with_git(tmp_path: Path) -> None:
    """find_project_root should find .git directory."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    subdir = tmp_path / "src" / "nested"
    subdir.mkdir(parents=True)

    result = find_project_root(subdir)
    assert result == tmp_path


def test_find_project_root_with_lexibrary_toml(tmp_path: Path) -> None:
    """find_project_root should find lexibrary.toml."""
    config_file = tmp_path / "lexibrary.toml"
    config_file.write_text("")

    subdir = tmp_path / "src" / "nested"
    subdir.mkdir(parents=True)

    result = find_project_root(subdir)
    assert result == tmp_path


def test_find_project_root_no_markers(tmp_path: Path) -> None:
    """find_project_root should return cwd when no markers found."""
    subdir = tmp_path / "some" / "nested" / "dir"
    subdir.mkdir(parents=True)

    result = find_project_root(subdir)
    # Should fall back to current working directory
    assert result == Path.cwd()


def test_find_project_root_closest_marker(tmp_path: Path) -> None:
    """find_project_root should return closest marker."""
    # Root has .git
    root_git = tmp_path / ".git"
    root_git.mkdir()

    # Nested dir has lexibrary.toml
    nested = tmp_path / "project"
    nested.mkdir()
    nested_config = nested / "lexibrary.toml"
    nested_config.write_text("")

    # Should find the closest one (nested)
    result = find_project_root(nested / "src")
    assert result == nested


def test_find_project_root_from_root_directory(tmp_path: Path) -> None:
    """find_project_root should work when called from root directory."""
    config_file = tmp_path / "lexibrary.toml"
    config_file.write_text("")

    result = find_project_root(tmp_path)
    assert result == tmp_path

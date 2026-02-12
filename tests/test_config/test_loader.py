"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

from lexibrarian.config.loader import find_config_file, load_config
from lexibrarian.config.schema import LexibraryConfig


def test_find_config_file_in_current_directory(tmp_path: Path) -> None:
    """find_config_file should find config in current directory."""
    config_file = tmp_path / "lexibrary.toml"
    config_file.write_text("")

    result = find_config_file(tmp_path)
    assert result == config_file


def test_find_config_file_in_parent_directory(tmp_path: Path) -> None:
    """find_config_file should walk upward to find config."""
    config_file = tmp_path / "lexibrary.toml"
    config_file.write_text("")

    subdir = tmp_path / "subdir" / "nested"
    subdir.mkdir(parents=True)

    result = find_config_file(subdir)
    assert result == config_file


def test_find_config_file_not_found(tmp_path: Path) -> None:
    """find_config_file should return None if config not found."""
    result = find_config_file(tmp_path)
    assert result is None


def test_load_config_with_defaults() -> None:
    """load_config should return defaults when no file found."""
    config = load_config(Path("/nonexistent/path/lexibrary.toml"))
    assert isinstance(config, LexibraryConfig)
    assert config.llm.provider == "anthropic"


def test_load_config_from_file(tmp_path: Path) -> None:
    """load_config should load and validate TOML file."""
    config_file = tmp_path / "lexibrary.toml"
    config_file.write_text(
        """
[llm]
provider = "openai"
model = "gpt-4"

[crawl]
max_file_size_kb = 1024
"""
    )

    config = load_config(config_file)
    assert config.llm.provider == "openai"
    assert config.llm.model == "gpt-4"
    assert config.crawl.max_file_size_kb == 1024
    # Other fields should use defaults
    assert config.llm.max_retries == 3


def test_load_config_partial_override(tmp_path: Path) -> None:
    """load_config should merge partial config with defaults."""
    config_file = tmp_path / "lexibrary.toml"
    config_file.write_text(
        """
[crawl]
max_files_per_llm_batch = 20
"""
    )

    config = load_config(config_file)
    assert config.crawl.max_files_per_llm_batch == 20
    # Other fields should use defaults
    assert config.crawl.max_file_size_kb == 512
    assert config.llm.provider == "anthropic"

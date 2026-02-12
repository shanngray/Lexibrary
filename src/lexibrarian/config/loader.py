"""Configuration file discovery and loading."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from lexibrarian.config.schema import LexibraryConfig


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """
    Search for lexibrary.toml starting from start_dir and walking upward.

    Args:
        start_dir: Directory to start search from. Defaults to current working directory.

    Returns:
        Path to lexibrary.toml if found, None otherwise.
    """
    start_dir = Path.cwd() if start_dir is None else Path(start_dir).resolve()

    current = start_dir
    while True:
        config_path = current / "lexibrary.toml"
        if config_path.exists():
            return config_path

        # Stop at filesystem root
        if current.parent == current:
            break

        current = current.parent

    return None


def load_config(config_path: Path | None = None) -> LexibraryConfig:
    """
    Load and validate configuration from a TOML file.

    Args:
        config_path: Path to config file. If None, searches for lexibrary.toml
                    using find_config_file(). If not found, returns defaults.

    Returns:
        Validated LexibraryConfig instance.

    Raises:
        pydantic.ValidationError: If config file contains invalid values.
    """
    # If no path provided, search for config file
    if config_path is None:
        config_path = find_config_file()

    # If no config file found, return all defaults
    if config_path is None or not config_path.exists():
        return LexibraryConfig()

    # Load and parse TOML file
    with open(config_path, "rb") as f:
        config_data: dict[str, Any] = tomllib.load(f)

    # Validate and return config (Pydantic handles merging with defaults)
    return LexibraryConfig.model_validate(config_data)

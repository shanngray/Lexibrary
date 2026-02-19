"""Configuration schema with Pydantic 2 models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    model_config = ConfigDict(extra="ignore")

    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key_env: str = "ANTHROPIC_API_KEY"
    max_retries: int = 3
    timeout: int = 60


class TokenBudgetConfig(BaseModel):
    """Per-artifact token budget configuration."""

    model_config = ConfigDict(extra="ignore")

    start_here_tokens: int = 800
    handoff_tokens: int = 100
    design_file_tokens: int = 400
    design_file_abridged_tokens: int = 100
    aindex_tokens: int = 200
    concept_file_tokens: int = 400


class MappingConfig(BaseModel):
    """Mapping strategy configuration (stub for Phase 1)."""

    model_config = ConfigDict(extra="ignore")

    strategies: list[dict[str, Any]] = Field(default_factory=list)


class IgnoreConfig(BaseModel):
    """Ignore pattern configuration."""

    model_config = ConfigDict(extra="ignore")

    use_gitignore: bool = True
    additional_patterns: list[str] = Field(
        default_factory=lambda: [
            ".lexibrary/START_HERE.md",
            ".lexibrary/HANDOFF.md",
            ".lexibrary/**/*.md",
            ".lexibrary/**/.aindex",
            "node_modules/",
            "__pycache__/",
            ".git/",
            ".venv/",
            "venv/",
            "*.lock",
        ]
    )


class DaemonConfig(BaseModel):
    """Daemon watch configuration."""

    model_config = ConfigDict(extra="ignore")

    debounce_seconds: float = 2.0
    sweep_interval_seconds: int = 300
    enabled: bool = True


class LexibraryConfig(BaseModel):
    """Top-level Lexibrarian configuration."""

    model_config = ConfigDict(extra="ignore")

    llm: LLMConfig = Field(default_factory=LLMConfig)
    token_budgets: TokenBudgetConfig = Field(default_factory=TokenBudgetConfig)
    mapping: MappingConfig = Field(default_factory=MappingConfig)
    ignore: IgnoreConfig = Field(default_factory=IgnoreConfig)
    daemon: DaemonConfig = Field(default_factory=DaemonConfig)

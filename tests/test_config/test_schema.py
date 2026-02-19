"""Tests for v2 configuration schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lexibrarian.config.schema import (
    DaemonConfig,
    IgnoreConfig,
    LexibraryConfig,
    LLMConfig,
    MappingConfig,
    TokenBudgetConfig,
)


def test_llm_config_defaults() -> None:
    config = LLMConfig()
    assert config.provider == "anthropic"
    assert config.model == "claude-sonnet-4-6"
    assert config.api_key_env == "ANTHROPIC_API_KEY"
    assert config.max_retries == 3
    assert config.timeout == 60


def test_token_budget_defaults() -> None:
    config = TokenBudgetConfig()
    assert config.start_here_tokens == 800
    assert config.design_file_tokens == 400


def test_mapping_config_defaults() -> None:
    config = MappingConfig()
    assert config.strategies == []


def test_ignore_config_defaults() -> None:
    config = IgnoreConfig()
    assert config.use_gitignore is True
    assert "node_modules/" in config.additional_patterns
    assert "__pycache__/" in config.additional_patterns


def test_daemon_config_defaults() -> None:
    config = DaemonConfig()
    assert config.debounce_seconds == 2.0
    assert config.sweep_interval_seconds == 300
    assert config.enabled is True


def test_lexibrary_config_validates_all_subconfigs() -> None:
    config = LexibraryConfig()
    assert isinstance(config.llm, LLMConfig)
    assert isinstance(config.token_budgets, TokenBudgetConfig)
    assert isinstance(config.mapping, MappingConfig)
    assert isinstance(config.ignore, IgnoreConfig)
    assert isinstance(config.daemon, DaemonConfig)


def test_lexibrary_config_partial_override() -> None:
    config = LexibraryConfig.model_validate({"llm": {"provider": "openai"}})
    assert config.llm.provider == "openai"
    assert config.llm.max_retries == 3
    assert config.daemon.enabled is True


def test_invalid_type_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        LLMConfig(max_retries="not_a_number")  # type: ignore[arg-type]


def test_extra_fields_ignored() -> None:
    config = LLMConfig.model_validate({"provider": "x", "unknown": "y"})
    assert config.provider == "x"
    assert not hasattr(config, "unknown")

"""Tests for configuration schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lexibrarian.config.schema import (
    CrawlConfig,
    DaemonConfig,
    IgnoreConfig,
    LexibraryConfig,
    LLMConfig,
    OutputConfig,
    TokenizerConfig,
)


def test_llm_config_defaults() -> None:
    """LLMConfig should have Anthropic defaults."""
    config = LLMConfig()
    assert config.provider == "anthropic"
    assert config.model == "claude-sonnet-4-5-20250514"
    assert config.api_key_env == "ANTHROPIC_API_KEY"
    assert config.max_retries == 3
    assert config.timeout == 60


def test_crawl_config_defaults() -> None:
    """CrawlConfig should have reasonable limits."""
    config = CrawlConfig()
    assert config.max_file_size_kb == 512
    assert config.max_files_per_llm_batch == 10
    assert config.summary_max_tokens == 80
    assert config.dir_summary_max_tokens == 150


def test_ignore_config_defaults() -> None:
    """IgnoreConfig should include common patterns."""
    config = IgnoreConfig()
    assert config.use_gitignore is True
    assert ".aindex" in config.additional_patterns
    assert "lexibrary.toml" in config.additional_patterns
    assert "node_modules/" in config.additional_patterns
    assert "__pycache__/" in config.additional_patterns


def test_lexibrary_config_validates_all_subconfigs() -> None:
    """LexibraryConfig should validate all sub-configs."""
    config = LexibraryConfig()
    assert isinstance(config.llm, LLMConfig)
    assert isinstance(config.tokenizer, TokenizerConfig)
    assert isinstance(config.crawl, CrawlConfig)
    assert isinstance(config.ignore, IgnoreConfig)
    assert isinstance(config.daemon, DaemonConfig)
    assert isinstance(config.output, OutputConfig)


def test_lexibrary_config_partial_override() -> None:
    """LexibraryConfig should merge partial config with defaults."""
    config = LexibraryConfig.model_validate({"llm": {"provider": "openai"}})
    assert config.llm.provider == "openai"
    # Other fields should use defaults
    assert config.llm.max_retries == 3
    assert config.crawl.max_file_size_kb == 512


def test_crawl_config_invalid_type_raises_validation_error() -> None:
    """Invalid config values should raise ValidationError."""
    with pytest.raises(ValidationError):
        CrawlConfig(max_file_size_kb="not_a_number")  # type: ignore


def test_llm_config_custom_values() -> None:
    """LLMConfig should accept custom values."""
    config = LLMConfig(provider="ollama", model="llama2", max_retries=5)
    assert config.provider == "ollama"
    assert config.model == "llama2"
    assert config.max_retries == 5

"""Tests for config default template rendering."""

from __future__ import annotations

from lexibrarian.config.defaults import render_default_config


class TestRenderDefaultConfig:
    def test_anthropic_provider(self) -> None:
        result = render_default_config("anthropic")
        assert 'provider = "anthropic"' in result
        assert 'model = "claude-sonnet-4-5-20250514"' in result
        assert 'api_key_env = "ANTHROPIC_API_KEY"' in result

    def test_openai_provider(self) -> None:
        result = render_default_config("openai")
        assert 'provider = "openai"' in result
        assert 'model = "gpt-4o-mini"' in result
        assert 'api_key_env = "OPENAI_API_KEY"' in result

    def test_ollama_provider(self) -> None:
        result = render_default_config("ollama")
        assert 'provider = "ollama"' in result
        assert 'model = "llama3.2"' in result
        assert 'api_key_env = ""' in result

    def test_unknown_provider_falls_back_to_anthropic(self) -> None:
        result = render_default_config("unknown_provider")
        assert 'provider = "anthropic"' in result
        assert 'model = "claude-sonnet-4-5-20250514"' in result
        assert 'api_key_env = "ANTHROPIC_API_KEY"' in result

    def test_output_is_valid_toml_structure(self) -> None:
        result = render_default_config("anthropic")
        assert result.startswith("# Lexibrarian Configuration")
        assert "[llm]" in result
        assert "[output]" in result

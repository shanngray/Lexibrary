"""Tests for the default project config template."""

from __future__ import annotations

from lexibrarian.config.defaults import DEFAULT_PROJECT_CONFIG_TEMPLATE


def test_template_is_nonempty_yaml() -> None:
    assert "llm:" in DEFAULT_PROJECT_CONFIG_TEMPLATE
    assert "daemon:" in DEFAULT_PROJECT_CONFIG_TEMPLATE


def test_template_contains_all_sections() -> None:
    for section in ("llm:", "token_budgets:", "mapping:", "ignore:", "daemon:"):
        assert section in DEFAULT_PROJECT_CONFIG_TEMPLATE


def test_template_contains_project_name() -> None:
    """Template includes project_name with default."""
    assert 'project_name: ""' in DEFAULT_PROJECT_CONFIG_TEMPLATE


def test_template_contains_agent_environment() -> None:
    """Template includes agent_environment with default."""
    assert "agent_environment: []" in DEFAULT_PROJECT_CONFIG_TEMPLATE


def test_template_contains_iwh_section() -> None:
    """Template includes iwh section with enabled: true."""
    assert "iwh:" in DEFAULT_PROJECT_CONFIG_TEMPLATE
    assert "enabled: true" in DEFAULT_PROJECT_CONFIG_TEMPLATE

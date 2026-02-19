"""Tests for the default project config template."""

from __future__ import annotations

from lexibrarian.config.defaults import DEFAULT_PROJECT_CONFIG_TEMPLATE


def test_template_is_nonempty_yaml() -> None:
    assert "llm:" in DEFAULT_PROJECT_CONFIG_TEMPLATE
    assert "daemon:" in DEFAULT_PROJECT_CONFIG_TEMPLATE


def test_template_contains_all_sections() -> None:
    for section in ("llm:", "token_budgets:", "mapping:", "ignore:", "daemon:"):
        assert section in DEFAULT_PROJECT_CONFIG_TEMPLATE

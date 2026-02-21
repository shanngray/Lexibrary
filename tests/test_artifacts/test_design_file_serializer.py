"""Tests for design file serializer."""

from __future__ import annotations

from datetime import datetime

from lexibrarian.artifacts.design_file import DesignFile, DesignFileFrontmatter, StalenessMetadata
from lexibrarian.artifacts.design_file_serializer import serialize_design_file


def _meta(**overrides: object) -> StalenessMetadata:
    base: dict = {
        "source": "src/lexibrarian/cli.py",
        "source_hash": "abc123",
        "design_hash": "def456",
        "generated": datetime(2026, 1, 1, 12, 0, 0),
        "generator": "lexibrarian-v2",
    }
    base.update(overrides)
    return StalenessMetadata(**base)


def _frontmatter(**overrides: object) -> DesignFileFrontmatter:
    base: dict = {"description": "CLI entry point for the lexi command."}
    base.update(overrides)
    return DesignFileFrontmatter(**base)


def _design_file(**overrides: object) -> DesignFile:
    base: dict = {
        "source_path": "src/lexibrarian/cli.py",
        "frontmatter": _frontmatter(),
        "summary": "CLI entry point for the lexi command.",
        "interface_contract": "def main() -> None: ...",
        "metadata": _meta(),
    }
    base.update(overrides)
    return DesignFile(**base)


class TestSerializeDesignFileFrontmatter:
    def test_yaml_frontmatter_delimiters(self) -> None:
        result = serialize_design_file(_design_file())
        assert result.startswith("---\n")
        lines = result.split("\n")
        closing_idx = lines.index("---", 1)
        assert closing_idx > 1

    def test_frontmatter_description(self) -> None:
        result = serialize_design_file(_design_file())
        assert "description: CLI entry point for the lexi command." in result

    def test_frontmatter_updated_by_default(self) -> None:
        result = serialize_design_file(_design_file())
        assert "updated_by: archivist" in result

    def test_frontmatter_updated_by_agent(self) -> None:
        df = _design_file(frontmatter=_frontmatter(updated_by="agent"))
        result = serialize_design_file(df)
        assert "updated_by: agent" in result


class TestSerializeDesignFileStructure:
    def test_h1_heading_with_source_path(self) -> None:
        result = serialize_design_file(_design_file())
        assert "# src/lexibrarian/cli.py\n" in result

    def test_interface_contract_section(self) -> None:
        result = serialize_design_file(_design_file())
        assert "## Interface Contract" in result
        assert "```python" in result
        assert "def main() -> None: ..." in result

    def test_interface_contract_fenced_block_closed(self) -> None:
        result = serialize_design_file(_design_file())
        # Should have both opening and closing fences
        assert result.count("```python") == 1
        # closing ``` after opening
        ic_idx = result.index("```python")
        rest = result[ic_idx + 9:]
        assert "```" in rest

    def test_dependencies_section_empty(self) -> None:
        result = serialize_design_file(_design_file())
        assert "## Dependencies" in result
        deps_body = result.split("## Dependencies")[1].split("##")[0]
        assert "(none)" in deps_body

    def test_dependencies_section_populated(self) -> None:
        df = _design_file(dependencies=["src/lexibrarian/config/schema.py"])
        result = serialize_design_file(df)
        assert "- src/lexibrarian/config/schema.py" in result

    def test_dependents_section_empty(self) -> None:
        result = serialize_design_file(_design_file())
        assert "## Dependents" in result
        dep_body = result.split("## Dependents")[1].split("##")[0]
        assert "(none)" in dep_body

    def test_dependents_section_populated(self) -> None:
        df = _design_file(dependents=["src/lexibrarian/__main__.py"])
        result = serialize_design_file(df)
        assert "- src/lexibrarian/__main__.py" in result

    def test_output_ends_with_trailing_newline(self) -> None:
        result = serialize_design_file(_design_file())
        assert result.endswith("\n")


class TestSerializeDesignFileOptionalSections:
    def test_optional_sections_omitted_when_empty(self) -> None:
        result = serialize_design_file(_design_file())
        assert "## Tests" not in result
        assert "## Complexity Warning" not in result
        assert "## Wikilinks" not in result
        assert "## Tags" not in result
        assert "## Guardrails" not in result

    def test_tests_section_included_when_set(self) -> None:
        df = _design_file(tests="See tests/test_cli.py")
        result = serialize_design_file(df)
        assert "## Tests" in result
        assert "See tests/test_cli.py" in result

    def test_complexity_warning_included(self) -> None:
        df = _design_file(complexity_warning="High cyclomatic complexity.")
        result = serialize_design_file(df)
        assert "## Complexity Warning" in result
        assert "High cyclomatic complexity." in result

    def test_wikilinks_included(self) -> None:
        df = _design_file(wikilinks=["[[Config]]", "[[LLMService]]"])
        result = serialize_design_file(df)
        assert "## Wikilinks" in result
        assert "- [[Config]]" in result
        assert "- [[LLMService]]" in result

    def test_tags_included(self) -> None:
        df = _design_file(tags=["cli", "entry-point"])
        result = serialize_design_file(df)
        assert "## Tags" in result
        assert "- cli" in result
        assert "- entry-point" in result

    def test_guardrails_included(self) -> None:
        df = _design_file(guardrail_refs=["G-01", "G-02"])
        result = serialize_design_file(df)
        assert "## Guardrails" in result
        assert "- G-01" in result
        assert "- G-02" in result


class TestSerializeDesignFileFooter:
    def test_footer_present(self) -> None:
        result = serialize_design_file(_design_file())
        assert "<!-- lexibrarian:meta" in result
        assert "-->" in result

    def test_footer_contains_required_fields(self) -> None:
        result = serialize_design_file(_design_file())
        assert "source: src/lexibrarian/cli.py" in result
        assert "source_hash: abc123" in result
        assert "design_hash:" in result
        assert "generated:" in result
        assert "generator: lexibrarian-v2" in result

    def test_footer_interface_hash_omitted_when_none(self) -> None:
        result = serialize_design_file(_design_file())
        assert "interface_hash" not in result

    def test_footer_interface_hash_included_when_set(self) -> None:
        df = _design_file(metadata=_meta(interface_hash="ifhash999"))
        result = serialize_design_file(df)
        assert "interface_hash: ifhash999" in result

    def test_design_hash_is_sha256_hex(self) -> None:
        result = serialize_design_file(_design_file())
        # Extract design_hash value
        for line in result.splitlines():
            if line.startswith("design_hash:"):
                value = line.split(": ", 1)[1].strip()
                assert len(value) == 64
                assert all(c in "0123456789abcdef" for c in value)
                break
        else:
            raise AssertionError("design_hash not found in footer")

    def test_footer_multiline_format(self) -> None:
        result = serialize_design_file(_design_file())
        # Footer should span multiple lines (key: value pairs)
        footer_start = result.index("<!-- lexibrarian:meta")
        footer_end = result.index("-->", footer_start)
        footer_content = result[footer_start:footer_end]
        assert "\n" in footer_content

    def test_language_tag_python(self) -> None:
        df = _design_file(source_path="src/foo.py")
        result = serialize_design_file(df)
        assert "```python" in result

    def test_language_tag_typescript(self) -> None:
        df = _design_file(source_path="src/foo.ts")
        result = serialize_design_file(df)
        assert "```typescript" in result

    def test_language_tag_unknown_defaults_to_text(self) -> None:
        df = _design_file(source_path="src/foo.xyz")
        result = serialize_design_file(df)
        assert "```text" in result


class TestSerializeDesignFileWikilinkBrackets:
    """Tests for wikilink [[bracket]] wrapping in serializer (Task 5.3)."""

    def test_unbracketed_wikilinks_get_brackets(self) -> None:
        """Wikilinks stored without brackets are wrapped in [[]] on output."""
        df = _design_file(wikilinks=["Config", "LLMService"])
        result = serialize_design_file(df)
        assert "- [[Config]]" in result
        assert "- [[LLMService]]" in result

    def test_already_bracketed_wikilinks_not_double_wrapped(self) -> None:
        """Wikilinks already in [[brackets]] are not double-wrapped."""
        df = _design_file(wikilinks=["[[Config]]", "[[LLMService]]"])
        result = serialize_design_file(df)
        assert "- [[Config]]" in result
        assert "- [[LLMService]]" in result
        # Ensure no double-wrapping
        assert "[[[[" not in result
        assert "]]]]" not in result

    def test_mixed_bracketed_and_unbracketed(self) -> None:
        """Mix of bracketed and unbracketed wikilinks both serialize correctly."""
        df = _design_file(wikilinks=["Config", "[[LLMService]]"])
        result = serialize_design_file(df)
        assert "- [[Config]]" in result
        assert "- [[LLMService]]" in result
        assert "[[[[" not in result

    def test_single_unbracketed_wikilink(self) -> None:
        """A single unbracketed wikilink is correctly wrapped."""
        df = _design_file(wikilinks=["ErrorHandling"])
        result = serialize_design_file(df)
        assert "- [[ErrorHandling]]" in result

    def test_empty_wikilinks_no_section(self) -> None:
        """Empty wikilinks list produces no Wikilinks section."""
        df = _design_file(wikilinks=[])
        result = serialize_design_file(df)
        assert "## Wikilinks" not in result

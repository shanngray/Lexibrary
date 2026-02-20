"""Tests for design file parser."""

from __future__ import annotations

from pathlib import Path

from lexibrarian.artifacts.design_file_parser import (
    parse_design_file,
    parse_design_file_frontmatter,
    parse_design_file_metadata,
)

_FULL_DESIGN_FILE = """\
---
description: CLI entry point for the lexi command.
updated_by: archivist
---

# src/lexibrarian/cli.py

## Interface Contract

```python
def main() -> None: ...
```

## Dependencies

- src/lexibrarian/config/schema.py

## Dependents

(none)

<!-- lexibrarian:meta
source: src/lexibrarian/cli.py
source_hash: abc123
design_hash: def456
generated: 2026-01-01T12:00:00
generator: lexibrarian-v2
-->
"""

_FULL_WITH_OPTIONAL = """\
---
description: Full design file with all sections.
updated_by: agent
---

# src/foo.py

## Interface Contract

```python
class Foo: ...
```

## Dependencies

(none)

## Dependents

- src/bar.py

## Tests

See tests/test_foo.py

## Complexity Warning

High cyclomatic complexity.

## Wikilinks

- [[Config]]

## Tags

- core

## Guardrails

- G-01

<!-- lexibrarian:meta
source: src/foo.py
source_hash: src123
interface_hash: iface456
design_hash: dsgn789
generated: 2026-06-15T08:30:00
generator: lexibrarian-v2
-->
"""

_NO_FOOTER = """\
---
description: A file without footer.
updated_by: archivist
---

# src/bar.py

## Interface Contract

```python
pass
```

## Dependencies

(none)

## Dependents

(none)
"""

_CORRUPT_FOOTER = """\
---
description: Corrupt footer file.
updated_by: archivist
---

# src/baz.py

## Interface Contract

```python
pass
```

## Dependencies

(none)

## Dependents

(none)

<!-- lexibrarian:meta
not_a_valid_key_value_pair
-->
"""


class TestParseDesignFileMetadata:
    def test_extracts_metadata_from_valid_footer(self, tmp_path: Path) -> None:
        f = tmp_path / "design.md"
        f.write_text(_FULL_DESIGN_FILE)
        meta = parse_design_file_metadata(f)
        assert meta is not None
        assert meta.source == "src/lexibrarian/cli.py"
        assert meta.source_hash == "abc123"
        assert meta.design_hash == "def456"
        assert meta.generator == "lexibrarian-v2"

    def test_returns_none_for_nonexistent_file(self, tmp_path: Path) -> None:
        result = parse_design_file_metadata(tmp_path / "missing.md")
        assert result is None

    def test_returns_none_when_no_footer(self, tmp_path: Path) -> None:
        f = tmp_path / "no_footer.md"
        f.write_text(_NO_FOOTER)
        assert parse_design_file_metadata(f) is None

    def test_returns_none_for_corrupt_footer(self, tmp_path: Path) -> None:
        f = tmp_path / "corrupt.md"
        f.write_text(_CORRUPT_FOOTER)
        assert parse_design_file_metadata(f) is None

    def test_interface_hash_optional(self, tmp_path: Path) -> None:
        f = tmp_path / "design.md"
        f.write_text(_FULL_DESIGN_FILE)
        meta = parse_design_file_metadata(f)
        assert meta is not None
        assert meta.interface_hash is None

    def test_interface_hash_parsed_when_present(self, tmp_path: Path) -> None:
        f = tmp_path / "full.md"
        f.write_text(_FULL_WITH_OPTIONAL)
        meta = parse_design_file_metadata(f)
        assert meta is not None
        assert meta.interface_hash == "iface456"


class TestParseDesignFileFrontmatter:
    def test_extracts_description(self, tmp_path: Path) -> None:
        f = tmp_path / "design.md"
        f.write_text(_FULL_DESIGN_FILE)
        fm = parse_design_file_frontmatter(f)
        assert fm is not None
        assert fm.description == "CLI entry point for the lexi command."

    def test_extracts_updated_by(self, tmp_path: Path) -> None:
        f = tmp_path / "design.md"
        f.write_text(_FULL_WITH_OPTIONAL)
        fm = parse_design_file_frontmatter(f)
        assert fm is not None
        assert fm.updated_by == "agent"

    def test_updated_by_defaults_to_archivist(self, tmp_path: Path) -> None:
        content = "---\ndescription: No updated_by field.\n---\n\n# src/x.py\n"
        f = tmp_path / "design.md"
        f.write_text(content)
        fm = parse_design_file_frontmatter(f)
        assert fm is not None
        assert fm.updated_by == "archivist"

    def test_returns_none_for_nonexistent_file(self, tmp_path: Path) -> None:
        assert parse_design_file_frontmatter(tmp_path / "missing.md") is None

    def test_returns_none_when_no_frontmatter(self, tmp_path: Path) -> None:
        f = tmp_path / "no_fm.md"
        f.write_text("# Just a heading\n\nNo frontmatter.\n")
        assert parse_design_file_frontmatter(f) is None


class TestParseDesignFileFull:
    def test_parse_full_design_file(self, tmp_path: Path) -> None:
        f = tmp_path / "design.md"
        f.write_text(_FULL_DESIGN_FILE)
        df = parse_design_file(f)
        assert df is not None
        assert df.source_path == "src/lexibrarian/cli.py"
        assert df.frontmatter.description == "CLI entry point for the lexi command."
        assert df.frontmatter.updated_by == "archivist"
        assert df.interface_contract == "def main() -> None: ..."
        assert df.dependencies == ["src/lexibrarian/config/schema.py"]
        assert df.dependents == []
        assert df.metadata.source_hash == "abc123"

    def test_parse_file_with_all_optional_sections(self, tmp_path: Path) -> None:
        f = tmp_path / "full.md"
        f.write_text(_FULL_WITH_OPTIONAL)
        df = parse_design_file(f)
        assert df is not None
        assert df.tests == "See tests/test_foo.py"
        assert df.complexity_warning == "High cyclomatic complexity."
        assert df.wikilinks == ["[[Config]]"]
        assert df.tags == ["core"]
        assert df.guardrail_refs == ["G-01"]
        assert df.dependents == ["src/bar.py"]

    def test_returns_none_for_nonexistent_file(self, tmp_path: Path) -> None:
        assert parse_design_file(tmp_path / "missing.md") is None

    def test_returns_none_when_no_footer(self, tmp_path: Path) -> None:
        f = tmp_path / "no_footer.md"
        f.write_text(_NO_FOOTER)
        assert parse_design_file(f) is None

    def test_returns_none_for_corrupt_footer(self, tmp_path: Path) -> None:
        f = tmp_path / "corrupt.md"
        f.write_text(_CORRUPT_FOOTER)
        assert parse_design_file(f) is None

    def test_returns_none_when_no_frontmatter(self, tmp_path: Path) -> None:
        content = "# src/x.py\n\n## Interface Contract\n\n```python\npass\n```\n"
        f = tmp_path / "no_fm.md"
        f.write_text(content)
        assert parse_design_file(f) is None

"""Tests for ``check_parseable_artifacts``.

Verifies the validator surfaces malformed artifacts that the lenient
parsers silently skip.  Covers one malformed fixture per artifact kind,
the all-valid baseline, file-not-found / no-frontmatter benign cases,
unexpected-error defensive handling, severity-filter registration, and
an end-to-end CLI excerpt that must include the parser's full
self-describing detail.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from lexibrary.utils.paths import DESIGNS_DIR, LEXIBRARY_DIR
from lexibrary.validator import AVAILABLE_CHECKS, validate_library
from lexibrary.validator.checks import check_parseable_artifacts

# ---------------------------------------------------------------------------
# Fixture writers — one per artifact kind, each producing both a valid file
# and a deliberately malformed file (frontmatter-level Pydantic / YAML failure).
# ---------------------------------------------------------------------------


_VALID_STACK = """---
id: ST-001
title: Valid post
tags: [bug]
status: open
created: 2026-01-15
author: tester
---

## Problem

Body.
"""

# resolution_type 'documentation' is rejected by the ResolutionType enum.
# This mirrors the real failure mode found in the user's P3394-CLI repo.
_BAD_STACK = """---
id: ST-099
title: Bad post
tags: [bug]
status: resolved
created: 2026-01-15
author: tester
resolution_type: documentation
---

## Problem

Body.
"""

_VALID_CONCEPT = """---
title: Valid Concept
id: CN-001
aliases: []
tags: []
status: active
---

# Valid Concept

Body.
"""

# status 'archived' is rejected by the Literal enum on ConceptFileFrontmatter.
_BAD_CONCEPT = """---
title: Bad Concept
id: CN-002
aliases: []
tags: []
status: archived
---

# Bad Concept

Body.
"""

_VALID_CONVENTION = """---
title: Valid Convention
id: CV-001
status: active
source: user
scope: project
tags: [general]
priority: 0
---

Convention rule body.
"""

# source 'somebody-else' is rejected by the Literal enum.
_BAD_CONVENTION = """---
title: Bad Convention
id: CV-002
status: active
source: somebody-else
scope: project
tags: [general]
priority: 0
---

Body.
"""

_VALID_PLAYBOOK = """---
title: Valid Playbook
id: PB-001
status: active
source: user
---

## Overview

Steps.
"""

# status 'archived' is rejected by the playbook Literal enum.
_BAD_PLAYBOOK = """---
title: Bad Playbook
id: PB-002
status: archived
source: user
---

## Overview

Steps.
"""

# Designs use a different schema; updated_by 'wizard' is rejected.
_VALID_DESIGN = """---
description: Valid design
id: DS-001
updated_by: archivist
status: active
---

# src/main.py

Design body.

<!-- lexibrary:meta source="src/main.py" source_hash="abc"
generated="2026-01-01T00:00:00" -->
"""

_BAD_DESIGN = """---
description: Bad design
id: DS-002
updated_by: wizard
status: active
---

# src/other.py

Design body.

<!-- lexibrary:meta source="src/other.py" source_hash="abc"
generated="2026-01-01T00:00:00" -->
"""


def _setup_lib(tmp_path: Path) -> Path:
    """Create an empty .lexibrary/ tree with all artifact subdirectories."""
    lib = tmp_path / LEXIBRARY_DIR
    lib.mkdir()
    (lib / "stack").mkdir()
    (lib / "concepts").mkdir()
    (lib / "conventions").mkdir()
    (lib / "playbooks").mkdir()
    (lib / DESIGNS_DIR / "src").mkdir(parents=True)
    return lib


# ---------------------------------------------------------------------------
# Per-kind malformed fixture cases
# ---------------------------------------------------------------------------


class TestPerKindMalformed:
    """Each artifact kind: one malformed file -> one error finding with parser detail."""

    def test_malformed_stack_post_emits_finding(self, tmp_path: Path) -> None:
        lib = _setup_lib(tmp_path)
        (lib / "stack" / "ST-099-bad.md").write_text(_BAD_STACK, encoding="utf-8")

        issues = check_parseable_artifacts(tmp_path, lib)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "error"
        assert issue.check == "parseable_artifacts"
        # Parser's self-describing detail must thread through verbatim.
        assert "resolution_type" in issue.message
        assert "documentation" in issue.message
        assert "fix" in issue.message
        assert "workaround" in issue.message
        assert issue.artifact.endswith("ST-099-bad.md")

    def test_malformed_concept_emits_finding(self, tmp_path: Path) -> None:
        lib = _setup_lib(tmp_path)
        (lib / "concepts" / "CN-002-bad.md").write_text(_BAD_CONCEPT, encoding="utf-8")

        issues = check_parseable_artifacts(tmp_path, lib)

        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "status" in issues[0].message
        assert "archived" in issues[0].message

    def test_malformed_convention_emits_finding(self, tmp_path: Path) -> None:
        lib = _setup_lib(tmp_path)
        (lib / "conventions" / "CV-002-bad.md").write_text(_BAD_CONVENTION, encoding="utf-8")

        issues = check_parseable_artifacts(tmp_path, lib)

        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "source" in issues[0].message
        assert "somebody-else" in issues[0].message

    def test_malformed_playbook_emits_finding(self, tmp_path: Path) -> None:
        lib = _setup_lib(tmp_path)
        (lib / "playbooks" / "PB-002-bad.md").write_text(_BAD_PLAYBOOK, encoding="utf-8")

        issues = check_parseable_artifacts(tmp_path, lib)

        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "status" in issues[0].message
        assert "archived" in issues[0].message

    def test_malformed_design_emits_finding(self, tmp_path: Path) -> None:
        lib = _setup_lib(tmp_path)
        (lib / DESIGNS_DIR / "src" / "other.py.md").write_text(_BAD_DESIGN, encoding="utf-8")

        issues = check_parseable_artifacts(tmp_path, lib)

        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "updated_by" in issues[0].message
        assert "wizard" in issues[0].message

    def test_malformed_design_frontmatter_yaml_error(self, tmp_path: Path) -> None:
        """A YAML syntax error inside the frontmatter block surfaces verbatim."""
        lib = _setup_lib(tmp_path)
        # Unclosed bracket on tags list -> yaml.YAMLError -> DesignFileValidationError
        bad_yaml = """---
description: broken yaml
id: DS-003
updated_by: archivist
status: active
deprecated_at: not-a-real-date: [oops
---

# src/yaml_break.py

Body.
"""
        (lib / DESIGNS_DIR / "src" / "yaml_break.py.md").write_text(bad_yaml, encoding="utf-8")

        issues = check_parseable_artifacts(tmp_path, lib)

        assert len(issues) == 1
        assert issues[0].severity == "error"
        # YAML errors thread through with the parser's "YAML syntax error" prefix.
        assert "YAML" in issues[0].message or "syntax" in issues[0].message.lower()


# ---------------------------------------------------------------------------
# All-valid library
# ---------------------------------------------------------------------------


class TestAllValid:
    def test_all_valid_emits_no_findings(self, tmp_path: Path) -> None:
        lib = _setup_lib(tmp_path)
        (lib / "stack" / "ST-001-ok.md").write_text(_VALID_STACK, encoding="utf-8")
        (lib / "concepts" / "CN-001-ok.md").write_text(_VALID_CONCEPT, encoding="utf-8")
        (lib / "conventions" / "CV-001-ok.md").write_text(_VALID_CONVENTION, encoding="utf-8")
        (lib / "playbooks" / "PB-001-ok.md").write_text(_VALID_PLAYBOOK, encoding="utf-8")
        (lib / DESIGNS_DIR / "src" / "main.py.md").write_text(_VALID_DESIGN, encoding="utf-8")

        issues = check_parseable_artifacts(tmp_path, lib)

        assert issues == []


# ---------------------------------------------------------------------------
# Benign cases — no frontmatter / missing dirs / empty file should be silent
# ---------------------------------------------------------------------------


class TestBenignCases:
    def test_missing_artifact_dirs_silent(self, tmp_path: Path) -> None:
        """When .lexibrary/ has no artifact subdirs, no findings are produced."""
        lib = tmp_path / LEXIBRARY_DIR
        lib.mkdir()

        issues = check_parseable_artifacts(tmp_path, lib)

        assert issues == []

    def test_file_without_frontmatter_silent(self, tmp_path: Path) -> None:
        """A markdown file with no `---` frontmatter is not malformed; it's not an artifact."""
        lib = _setup_lib(tmp_path)
        (lib / "stack" / "ST-no-fm.md").write_text(
            "# Just a heading\n\nNo frontmatter at all.\n", encoding="utf-8"
        )
        (lib / "concepts" / "CN-no-fm.md").write_text("plain text\n", encoding="utf-8")

        issues = check_parseable_artifacts(tmp_path, lib)

        assert issues == []

    def test_empty_file_silent(self, tmp_path: Path) -> None:
        """An empty file lacks frontmatter, so the strict parser returns None."""
        lib = _setup_lib(tmp_path)
        (lib / "stack" / "ST-empty.md").write_text("", encoding="utf-8")

        issues = check_parseable_artifacts(tmp_path, lib)

        assert issues == []


# ---------------------------------------------------------------------------
# Defensive boundary — unexpected parser failures must not crash the check
# ---------------------------------------------------------------------------


class TestUnexpectedParserError:
    def test_unanticipated_exception_emits_finding(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the parser raises something other than its typed error, surface it defensively."""
        lib = _setup_lib(tmp_path)
        # File needs to exist with frontmatter so the strict parser is invoked.
        (lib / "stack" / "ST-001-ok.md").write_text(_VALID_STACK, encoding="utf-8")

        def boom(_path: Path) -> Any:
            raise RuntimeError("unanticipated explosion")

        # Patch the symbol used by the check module, not the source module.
        monkeypatch.setattr(
            "lexibrary.validator.checks.parse_stack_post_strict",
            boom,
        )

        issues = check_parseable_artifacts(tmp_path, lib)

        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "unexpected parser error" in issues[0].message
        assert "RuntimeError" in issues[0].message
        assert "unanticipated explosion" in issues[0].message


# ---------------------------------------------------------------------------
# Registry / severity-filter — proves the check is registered as 'error'
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_registered_as_error_severity(self) -> None:
        assert "parseable_artifacts" in AVAILABLE_CHECKS
        check_fn, severity = AVAILABLE_CHECKS["parseable_artifacts"]
        assert check_fn is check_parseable_artifacts
        assert severity == "error"

    def test_runs_under_error_severity_filter(self, tmp_path: Path) -> None:
        """A severity_filter='error' run must include this check (proves registration)."""
        lib = _setup_lib(tmp_path)
        (lib / "stack" / "ST-099-bad.md").write_text(_BAD_STACK, encoding="utf-8")

        report = validate_library(
            tmp_path,
            lib,
            severity_filter="error",
            check_filter="parseable_artifacts",
        )

        assert any(i.check == "parseable_artifacts" for i in report.issues)

    def test_skipped_under_warning_only_filter_via_checks(self, tmp_path: Path) -> None:
        """When the caller restricts to a check set that excludes us, we don't run.

        This proves the check name is the only handle the caller has — i.e.
        the check is fully gated by AVAILABLE_CHECKS, not by ad-hoc dispatch.
        """
        lib = _setup_lib(tmp_path)
        (lib / "stack" / "ST-099-bad.md").write_text(_BAD_STACK, encoding="utf-8")

        report = validate_library(
            tmp_path,
            lib,
            checks=["hash_freshness"],  # not 'parseable_artifacts'
        )

        assert not any(i.check == "parseable_artifacts" for i in report.issues)


# ---------------------------------------------------------------------------
# End-to-end CLI excerpt — validates the rendered output carries detail
# ---------------------------------------------------------------------------


class TestCliEndToEnd:
    def test_cli_validate_surfaces_resolution_type_failure(self, tmp_path: Path) -> None:
        """Replicates the user-reported P3394-CLI failure shape and asserts the
        rendered ``lexi validate`` output names the field, the bad value, and
        the accepted set.
        """
        from typer.testing import CliRunner  # noqa: PLC0415

        from lexibrary.cli.lexi_app import lexi_app  # noqa: PLC0415

        # Build a minimal valid project.
        lib = _setup_lib(tmp_path)
        (lib / "config.yaml").write_text("", encoding="utf-8")
        # Two posts that reproduce the P3394 failure mode (different bad values).
        bad_post_a = _BAD_STACK.replace("ST-099", "ST-041").replace(
            "documentation", "documentation"
        )
        bad_post_b = _BAD_STACK.replace("ST-099", "ST-042").replace("documentation", "closure")
        (lib / "stack" / "ST-041-bad.md").write_text(bad_post_a, encoding="utf-8")
        (lib / "stack" / "ST-042-bad.md").write_text(bad_post_b, encoding="utf-8")

        runner = CliRunner()
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = runner.invoke(lexi_app, ["validate", "--check", "parseable_artifacts"])
        finally:
            os.chdir(old_cwd)

        output = result.output
        assert result.exit_code == 1, output
        # Both files surface in the report.
        assert "ST-041-bad.md" in output
        assert "ST-042-bad.md" in output
        # The message carries field name, bad value, and accepted set.
        assert "resolution_type" in output
        assert "documentation" in output
        assert "closure" in output
        assert "fix" in output
        assert "workaround" in output

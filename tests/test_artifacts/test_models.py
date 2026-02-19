"""Tests for artifact Pydantic 2 data models."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from lexibrarian.artifacts.aindex import AIndexEntry, AIndexFile
from lexibrarian.artifacts.concept import ConceptFile
from lexibrarian.artifacts.design_file import DesignFile, StalenessMetadata
from lexibrarian.artifacts.guardrail import GuardrailThread

# ---------------------------------------------------------------------------
# StalenessMetadata
# ---------------------------------------------------------------------------

def _meta(**overrides: object) -> dict:
    """Return a minimal valid StalenessMetadata dict, with optional overrides."""
    base: dict = {
        "source": "src/foo.py",
        "source_hash": "abc123",
        "generated": datetime(2026, 1, 1),
        "generator": "lexibrarian-v2",
    }
    base.update(overrides)
    return base


class TestStalenessMetadata:
    def test_valid_defaults(self) -> None:
        meta = StalenessMetadata(**_meta())
        assert meta.source == "src/foo.py"
        assert meta.interface_hash is None

    def test_interface_hash_optional(self) -> None:
        meta = StalenessMetadata(**_meta(interface_hash="xyz"))
        assert meta.interface_hash == "xyz"

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            StalenessMetadata(source="x", source_hash="y", generator="z")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# DesignFile
# ---------------------------------------------------------------------------

class TestDesignFile:
    def test_minimal_valid(self) -> None:
        df = DesignFile(
            source_path="src/foo.py",
            summary="A module",
            interface_contract="def foo()",
            metadata=StalenessMetadata(**_meta()),
        )
        assert df.dependencies == []
        assert df.tags == []

    def test_full_fields(self) -> None:
        df = DesignFile(
            source_path="src/foo.py",
            summary="A module",
            interface_contract="def foo()",
            dependencies=["bar.py"],
            dependents=["baz.py"],
            tests="test_foo.py",
            complexity_warning="high",
            wikilinks=["[[bar]]"],
            tags=["auth"],
            guardrail_refs=["GR-001"],
            metadata=StalenessMetadata(**_meta()),
        )
        assert df.dependencies == ["bar.py"]
        assert df.guardrail_refs == ["GR-001"]

    def test_missing_metadata_raises(self) -> None:
        with pytest.raises(ValidationError):
            DesignFile(
                source_path="x",
                summary="y",
                interface_contract="z",
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# AIndexFile
# ---------------------------------------------------------------------------

class TestAIndexFile:
    def test_minimal_valid(self) -> None:
        entry = AIndexEntry(name="foo.py", description="A file", is_directory=False)
        aindex = AIndexFile(
            directory_path="src/",
            billboard="Source code",
            entries=[entry],
            metadata=StalenessMetadata(**_meta()),
        )
        assert len(aindex.entries) == 1
        assert aindex.local_conventions == []

    def test_entry_missing_field(self) -> None:
        with pytest.raises(ValidationError):
            AIndexEntry(name="foo.py", description="A file")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ConceptFile
# ---------------------------------------------------------------------------

class TestConceptFile:
    def test_minimal_valid(self) -> None:
        cf = ConceptFile(name="auth", summary="Authentication system")
        assert cf.linked_files == []
        assert cf.metadata is None

    def test_with_metadata(self) -> None:
        cf = ConceptFile(
            name="auth",
            summary="Authentication",
            metadata=StalenessMetadata(**_meta()),
        )
        assert cf.metadata is not None


# ---------------------------------------------------------------------------
# GuardrailThread
# ---------------------------------------------------------------------------

class TestGuardrailThread:
    def test_minimal_valid(self) -> None:
        gt = GuardrailThread(
            thread_id="GR-001",
            title="Don't use eval",
            status="active",
            scope=["src/"],
            reported_by="dev",
            date=date(2026, 1, 1),
            problem="eval is dangerous",
        )
        assert gt.failed_approaches == []
        assert gt.resolution is None

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GuardrailThread(
                thread_id="GR-001",
                title="Bad",
                status="invalid",  # type: ignore[arg-type]
                scope=[],
                reported_by="dev",
                date=date(2026, 1, 1),
                problem="test",
            )

    def test_all_statuses(self) -> None:
        for status in ("active", "resolved", "stale"):
            gt = GuardrailThread(
                thread_id="GR-001",
                title="Test",
                status=status,  # type: ignore[arg-type]
                scope=[],
                reported_by="dev",
                date=date(2026, 1, 1),
                problem="test",
            )
            assert gt.status == status

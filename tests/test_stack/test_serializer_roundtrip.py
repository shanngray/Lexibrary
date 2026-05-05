"""Round-trip tests for Stack post serializer.

These tests serialize a StackPost, write the result to a temp file,
parse it back using the real parser, and verify equivalence.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from lexibrary.stack.models import (
    StackFinding,
    StackPost,
    StackPostFrontmatter,
    StackPostRefs,
)
from lexibrary.stack.parser import parse_stack_post
from lexibrary.stack.serializer import serialize_stack_post

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_frontmatter(**overrides: object) -> StackPostFrontmatter:
    defaults: dict[str, object] = {
        "id": "ST-001",
        "title": "Test post",
        "tags": ["bug"],
        "created": date(2026, 2, 21),
        "author": "agent-123",
    }
    defaults.update(overrides)
    return StackPostFrontmatter(**defaults)  # type: ignore[arg-type]


def _roundtrip(post: StackPost, tmp_path: Path) -> StackPost:
    """Serialize a post, write to disk, and parse it back."""
    text = serialize_stack_post(post)
    path = tmp_path / "ST-001-test.md"
    path.write_text(text, encoding="utf-8")
    parsed = parse_stack_post(path)
    assert parsed is not None, "Parser returned None for serialized output"
    return parsed


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """Verify serialize -> parse -> compare equivalence."""

    def test_roundtrip_no_findings(self, tmp_path: Path) -> None:
        original = StackPost(
            frontmatter=_make_frontmatter(),
            problem="Something is broken.",
            evidence=["Error line 1", "Error line 2"],
        )
        parsed = _roundtrip(original, tmp_path)

        assert parsed.frontmatter == original.frontmatter
        assert parsed.problem == original.problem
        assert parsed.evidence == original.evidence
        assert parsed.findings == []

    def test_roundtrip_with_findings_and_comments(self, tmp_path: Path) -> None:
        f1 = StackFinding(
            number=1,
            date=date(2026, 2, 21),
            author="agent-456",
            votes=3,
            accepted=True,
            body="Use approach X.",
            comments=[
                "**2026-02-22 agent-789 [upvote]:** Confirmed this works.",
            ],
        )
        f2 = StackFinding(
            number=2,
            date=date(2026, 2, 22),
            author="agent-789",
            votes=-1,
            body="Alternative approach Y.",
            comments=[
                "**2026-02-23 agent-123 [downvote]:** This is unreliable.",
            ],
        )
        original = StackPost(
            frontmatter=_make_frontmatter(
                refs=StackPostRefs(
                    concepts=["DateHandling"],
                    files=["src/foo.py"],
                    designs=["src/bar.py"],
                ),
                bead="lexibrary-abc.1",
                votes=5,
            ),
            problem="Date parsing fails in edge cases.",
            evidence=["ValueError on line 42", "Timezone mismatch"],
            findings=[f1, f2],
        )
        parsed = _roundtrip(original, tmp_path)

        assert parsed.frontmatter == original.frontmatter
        assert parsed.problem == original.problem
        assert parsed.evidence == original.evidence
        assert len(parsed.findings) == 2

        for orig_f, parsed_f in zip(original.findings, parsed.findings, strict=True):
            assert parsed_f.number == orig_f.number
            assert parsed_f.date == orig_f.date
            assert parsed_f.author == orig_f.author
            assert parsed_f.votes == orig_f.votes
            assert parsed_f.accepted == orig_f.accepted
            assert parsed_f.body == orig_f.body
            assert parsed_f.comments == orig_f.comments

    def test_roundtrip_all_fields(self, tmp_path: Path) -> None:
        """Fully populated StackPost round-trips faithfully."""
        original = StackPost(
            frontmatter=_make_frontmatter(
                id="ST-042",
                title="Complex scenario",
                tags=["perf", "config"],
                status="resolved",
                created=date(2026, 1, 15),
                author="agent-007",
                bead="lexibrary-xyz.5",
                votes=10,
                duplicate_of="ST-001",
                refs=StackPostRefs(
                    concepts=["Caching", "Retry"],
                    files=["src/cache.py", "src/retry.py"],
                    designs=["src/cache.py", "src/retry.py"],
                ),
            ),
            problem="Performance degrades under load.",
            evidence=["p99 latency >500ms", "CPU at 100%"],
            findings=[
                StackFinding(
                    number=1,
                    date=date(2026, 1, 16),
                    author="agent-456",
                    votes=7,
                    accepted=True,
                    body="Add caching layer.",
                    comments=[
                        "**2026-01-17 agent-789 [upvote]:** Works great.",
                        "**2026-01-18 agent-007 [upvote]:** Deployed.",
                    ],
                ),
            ],
        )
        parsed = _roundtrip(original, tmp_path)

        assert parsed.frontmatter == original.frontmatter
        assert parsed.problem == original.problem
        assert parsed.evidence == original.evidence
        assert len(parsed.findings) == len(original.findings)
        assert parsed.findings[0] == original.findings[0]

    def test_roundtrip_all_new_fields(self, tmp_path: Path) -> None:
        """Round-trip with context, attempts, and resolution_type (task 4.10)."""
        original = StackPost(
            frontmatter=_make_frontmatter(
                resolution_type="fix",
                status="resolved",
            ),
            problem="Import fails with circular dependency.",
            context="Upgrading from v1.0 to v2.0 of the library.",
            evidence=["ImportError traceback", "Module graph cycle"],
            attempts=["Reordered imports", "Used lazy loading"],
            findings=[
                StackFinding(
                    number=1,
                    date=date(2026, 2, 25),
                    author="agent-456",
                    votes=2,
                    accepted=True,
                    body="Break the cycle by extracting shared types.",
                ),
            ],
        )
        parsed = _roundtrip(original, tmp_path)

        assert parsed.frontmatter == original.frontmatter
        assert parsed.frontmatter.resolution_type == "fix"
        assert parsed.problem == original.problem
        assert parsed.context == original.context
        assert parsed.evidence == original.evidence
        assert parsed.attempts == original.attempts
        assert len(parsed.findings) == 1
        assert parsed.findings[0] == original.findings[0]

    def test_roundtrip_partial_fields(self, tmp_path: Path) -> None:
        """Round-trip with empty context and empty attempts (task 4.11)."""
        original = StackPost(
            frontmatter=_make_frontmatter(),
            problem="Something is broken.",
            context="",
            evidence=["Error line 1"],
            attempts=[],
        )
        parsed = _roundtrip(original, tmp_path)

        assert parsed.frontmatter == original.frontmatter
        assert parsed.problem == original.problem
        assert parsed.context == ""
        assert parsed.evidence == original.evidence
        assert parsed.attempts == []

    def test_roundtrip_resolution_type_survives(self, tmp_path: Path) -> None:
        """resolution_type survives serialize -> parse -> serialize (task 4.12)."""
        original = StackPost(
            frontmatter=_make_frontmatter(resolution_type="workaround"),
            problem="Flaky test in CI.",
        )
        # First round-trip
        parsed = _roundtrip(original, tmp_path)
        assert parsed.frontmatter.resolution_type == "workaround"

        # Second round-trip: serialize the parsed result and parse again
        text2 = serialize_stack_post(parsed)
        path2 = tmp_path / "ST-001-test-rt2.md"
        path2.write_text(text2, encoding="utf-8")
        parsed2 = parse_stack_post(path2)
        assert parsed2 is not None
        assert parsed2.frontmatter.resolution_type == "workaround"


# ---------------------------------------------------------------------------
# TG6: Serializer & Parser Updates — stale_at round-trip tests (task 6.2)
# ---------------------------------------------------------------------------


class TestStaleAtRoundTrip:
    """Verify stale_at field survives serialize -> parse round-trips."""

    def test_roundtrip_stale_post_with_stale_at(self, tmp_path: Path) -> None:
        """A stale post with stale_at round-trips faithfully."""
        original = StackPost(
            frontmatter=_make_frontmatter(
                status="stale",
                resolution_type="fix",
                stale_at="2026-06-15T10:00:00",
            ),
            problem="Old fix no longer applies.",
        )
        parsed = _roundtrip(original, tmp_path)

        assert parsed.frontmatter.status == "stale"
        assert parsed.frontmatter.stale_at == datetime(2026, 6, 15, 10, 0, 0)
        assert parsed.frontmatter.resolution_type == "fix"
        assert parsed.frontmatter == original.frontmatter

    def test_roundtrip_stale_at_none_omitted(self, tmp_path: Path) -> None:
        """When stale_at is None, it does not appear in YAML and parses back as None."""
        original = StackPost(
            frontmatter=_make_frontmatter(status="open"),
            problem="Something is broken.",
        )
        # Verify stale_at is None before round-trip
        assert original.frontmatter.stale_at is None

        parsed = _roundtrip(original, tmp_path)

        assert parsed.frontmatter.stale_at is None
        assert parsed.frontmatter == original.frontmatter

    def test_roundtrip_stale_at_survives_double_roundtrip(self, tmp_path: Path) -> None:
        """stale_at survives serialize -> parse -> serialize -> parse."""
        original = StackPost(
            frontmatter=_make_frontmatter(
                status="stale",
                stale_at="2026-07-01T14:30:00",
            ),
            problem="Stale resolution.",
        )
        # First round-trip
        parsed = _roundtrip(original, tmp_path)
        assert parsed.frontmatter.stale_at == datetime(2026, 7, 1, 14, 30, 0)

        # Second round-trip: serialize the parsed result and parse again
        text2 = serialize_stack_post(parsed)
        path2 = tmp_path / "ST-001-test-rt2.md"
        path2.write_text(text2, encoding="utf-8")
        parsed2 = parse_stack_post(path2)
        assert parsed2 is not None
        assert parsed2.frontmatter.stale_at == datetime(2026, 7, 1, 14, 30, 0)

    def test_roundtrip_stale_post_with_all_fields(self, tmp_path: Path) -> None:
        """Fully populated stale post round-trips faithfully."""
        original = StackPost(
            frontmatter=_make_frontmatter(
                id="ST-099",
                title="Stale post full scenario",
                tags=["perf", "database"],
                status="stale",
                created=date(2026, 3, 1),
                author="agent-500",
                bead="lexibrary-xyz.3",
                votes=4,
                refs=StackPostRefs(
                    concepts=["ConnectionPooling"],
                    files=["src/db.py"],
                    designs=["src/db.py"],
                ),
                resolution_type="workaround",
                stale_at="2026-06-20T08:15:00",
            ),
            problem="Connection pool workaround no longer needed.",
            context="After upgrading the database driver.",
            evidence=["Pool exhaustion no longer occurs"],
            attempts=["Tried removing workaround directly"],
            findings=[
                StackFinding(
                    number=1,
                    date=date(2026, 3, 2),
                    author="agent-600",
                    votes=2,
                    accepted=True,
                    body="The workaround can be safely removed.",
                    comments=[
                        "**2026-03-03 agent-500 [upvote]:** Confirmed.",
                    ],
                ),
            ],
        )
        parsed = _roundtrip(original, tmp_path)

        assert parsed.frontmatter == original.frontmatter
        assert parsed.frontmatter.status == "stale"
        assert parsed.frontmatter.stale_at == datetime(2026, 6, 20, 8, 15, 0)
        assert parsed.frontmatter.resolution_type == "workaround"
        assert parsed.problem == original.problem
        assert parsed.context == original.context
        assert parsed.evidence == original.evidence
        assert parsed.attempts == original.attempts
        assert len(parsed.findings) == 1
        assert parsed.findings[0] == original.findings[0]

    def test_roundtrip_stale_at_cleared_after_unstale(self, tmp_path: Path) -> None:
        """Simulates mark_unstale: stale_at cleared to None round-trips correctly."""
        # Start with a stale post
        stale_post = StackPost(
            frontmatter=_make_frontmatter(
                status="stale",
                resolution_type="fix",
                stale_at="2026-06-15T10:00:00",
            ),
            problem="Was stale, now un-staled.",
        )
        parsed_stale = _roundtrip(stale_post, tmp_path)
        assert parsed_stale.frontmatter.stale_at == datetime(2026, 6, 15, 10, 0, 0)

        # Simulate unstale: set status back to resolved and clear stale_at
        unstaled = StackPost(
            frontmatter=_make_frontmatter(
                status="resolved",
                resolution_type="fix",
                stale_at=None,
            ),
            problem="Was stale, now un-staled.",
        )
        text = serialize_stack_post(unstaled)
        path = tmp_path / "ST-001-unstaled.md"
        path.write_text(text, encoding="utf-8")
        parsed_unstaled = parse_stack_post(path)
        assert parsed_unstaled is not None
        assert parsed_unstaled.frontmatter.status == "resolved"
        assert parsed_unstaled.frontmatter.stale_at is None


# ---------------------------------------------------------------------------
# Bug-fix round-trip tests: finding title survives serialize -> parse
# ---------------------------------------------------------------------------


class TestFindingTitleRoundTrip:
    """Finding title survives serialize -> parse round-trips."""

    def test_roundtrip_titled_finding(self, tmp_path: Path) -> None:
        """A finding with a title round-trips with the title preserved."""
        original = StackPost(
            frontmatter=_make_frontmatter(id="ST-050", title="Titled findings test"),
            problem="Testing titled findings in round-trip.",
            findings=[
                StackFinding(
                    number=1,
                    title="R-code coverage gap",
                    date=date(2026, 4, 1),
                    author="agent-200",
                    votes=1,
                    accepted=True,
                    body="The coverage gap was identified here.",
                ),
                StackFinding(
                    number=2,
                    title="Another finding title",
                    date=date(2026, 4, 2),
                    author="agent-300",
                    votes=0,
                    accepted=False,
                    body="Second finding body.",
                ),
            ],
        )
        parsed = _roundtrip(original, tmp_path)

        assert len(parsed.findings) == 2
        assert parsed.findings[0].title == "R-code coverage gap"
        assert parsed.findings[0].body == "The coverage gap was identified here."
        assert parsed.findings[1].title == "Another finding title"
        assert parsed.findings[1].body == "Second finding body."

    def test_roundtrip_untitled_finding(self, tmp_path: Path) -> None:
        """A finding with no title round-trips with empty title."""
        original = StackPost(
            frontmatter=_make_frontmatter(id="ST-051", title="Untitled findings test"),
            problem="Testing untitled findings in round-trip.",
            findings=[
                StackFinding(
                    number=1,
                    title="",
                    date=date(2026, 4, 1),
                    author="agent-200",
                    votes=2,
                    accepted=False,
                    body="Plain finding without a title.",
                ),
            ],
        )
        parsed = _roundtrip(original, tmp_path)

        assert len(parsed.findings) == 1
        assert parsed.findings[0].title == ""
        assert parsed.findings[0].body == "Plain finding without a title."

    def test_roundtrip_mixed_titled_and_untitled(self, tmp_path: Path) -> None:
        """Mix of titled and untitled findings all round-trip correctly."""
        original = StackPost(
            frontmatter=_make_frontmatter(id="ST-053", title="Mixed findings test"),
            problem="Testing mixed titled/untitled findings.",
            findings=[
                StackFinding(
                    number=1,
                    title="Named finding",
                    date=date(2026, 4, 1),
                    author="agent-200",
                    votes=1,
                    accepted=True,
                    body="This one has a title.",
                ),
                StackFinding(
                    number=2,
                    title="",
                    date=date(2026, 4, 2),
                    author="agent-300",
                    votes=0,
                    accepted=False,
                    body="This one has no title.",
                ),
            ],
        )
        parsed = _roundtrip(original, tmp_path)

        assert len(parsed.findings) == 2
        assert parsed.findings[0].title == "Named finding"
        assert parsed.findings[1].title == ""

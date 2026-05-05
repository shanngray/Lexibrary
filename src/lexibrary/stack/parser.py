"""Parser for Stack post files from markdown format with YAML frontmatter."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml

from lexibrary.stack.models import (
    StackFinding,
    StackPost,
    StackPostFrontmatter,
)

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
# Matches ### F<n> with an optional em-dash/colon/hyphen title suffix.
# Group 1: finding number (digits)
# Group 2: optional title text after the separator (may be None)
_FINDING_HEADER_RE = re.compile(r"^###\s+F(\d+)(?:\s*[—\-:]\s*(.+?))?\s*$")
_METADATA_RE = re.compile(
    r"\*\*Date:\*\*\s*(\S+)\s*\|\s*"
    r"\*\*Author:\*\*\s*(\S+)\s*\|\s*"
    r"\*\*Votes:\*\*\s*(-?\d+)"
    r"(?:\s*\|\s*\*\*Accepted:\*\*\s*(true))?"
)


# NOTE: This pattern is intentionally different from wiki.patterns.HTML_COMMENT_RE.
# That pattern strips inline HTML comments from raw text before wikilink extraction
# (multiline, dotall). This pattern strips comment-only lines from rendered output
# (line-anchored, not dotall). They solve different problems.
_HTML_COMMENT_RE = re.compile(r"^\s*<!--.*-->\s*$")


class StackPostValidationError(Exception):
    """Raised by :func:`parse_stack_post_strict` when frontmatter fails validation.

    Carries the human-readable *detail* string extracted from the underlying
    ``yaml.YAMLError`` or Pydantic ``ValidationError`` so callers can surface
    an actionable message without re-catching low-level exceptions.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def parse_stack_post(path: Path) -> StackPost | None:
    """Parse a Stack post file into a StackPost model.

    Returns None if the file doesn't exist, has no valid frontmatter,
    or frontmatter fails validation.  Callers that need a structured error
    on validation failure should use :func:`parse_stack_post_strict` instead.
    """
    try:
        return parse_stack_post_strict(path)
    except StackPostValidationError:
        return None


def parse_stack_post_strict(path: Path) -> StackPost | None:
    """Parse a Stack post file, raising on validation or YAML errors.

    Returns ``None`` only for benign non-parse conditions:

    - The file does not exist.
    - An :class:`OSError` prevented reading the file.
    - The file contains no YAML frontmatter block.

    Raises :class:`StackPostValidationError` for any condition where a
    frontmatter block *was* found but its content is malformed or fails
    Pydantic validation.  The exception message names the field(s),
    the bad value(s), and the allowed values so the user can fix the file.
    """
    if not path.exists():
        return None

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        return None

    # Frontmatter block found — any error from here is a user-fixable problem.
    try:
        data = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError as exc:
        raise StackPostValidationError(f"YAML syntax error in frontmatter: {exc}") from exc

    if not isinstance(data, dict):
        raise StackPostValidationError(
            f"Frontmatter must be a YAML mapping, got {type(data).__name__}"
        )

    try:
        frontmatter = StackPostFrontmatter(**data)
    except (TypeError, ValueError) as exc:
        # Pydantic 2 ValidationError is a subclass of ValueError; TypeError can
        # arise from unexpected keyword arguments.  _format_validation_error
        # extracts the structured error list when the exception is a Pydantic
        # ValidationError; otherwise it falls back to str(exc).
        detail = _format_validation_error(exc)
        raise StackPostValidationError(detail) from exc

    raw_body = text[fm_match.end() :]
    problem, context, evidence, attempts = _extract_body_sections(raw_body)
    findings = _extract_findings(raw_body)

    return StackPost(
        frontmatter=frontmatter,
        problem=problem,
        context=context,
        evidence=evidence,
        attempts=attempts,
        findings=findings,
        raw_body=raw_body,
    )


def _format_validation_error(exc: Exception) -> str:
    """Extract a human-readable detail string from a Pydantic ValidationError.

    Falls back to ``str(exc)`` when the exception is not a Pydantic
    ``ValidationError`` or when the errors list is empty.
    """
    from pydantic import ValidationError  # noqa: PLC0415

    if not isinstance(exc, ValidationError):
        return str(exc)

    errors = exc.errors()
    if not errors:
        return str(exc)

    parts: list[str] = []
    for err in errors:
        loc = " -> ".join(str(part) for part in err.get("loc", ()))
        msg = err.get("msg", "")
        inp = err.get("input", "<unknown>")
        parts.append(f"  field {loc!r}: {msg} (got {inp!r})")

    return "Frontmatter validation failed:\n" + "\n".join(parts)


def _extract_body_sections(body: str) -> tuple[str, str, list[str], list[str]]:
    """Extract body sections: Problem, Context, Evidence, and Attempts.

    Uses order-independent section extraction via a ``current_section``
    state variable.  Sections are identified by their header and collected
    regardless of position.  A ``## Findings`` or ``### F{n}`` header
    terminates all body section extraction.

    HTML comment lines (``<!-- ... -->``) are stripped from extracted content.

    Returns:
        (problem, context, evidence, attempts) tuple.
    """
    lines = body.splitlines()
    problem_lines: list[str] = []
    context_lines: list[str] = []
    evidence_items: list[str] = []
    attempts_items: list[str] = []
    current_section: str | None = None

    for line in lines:
        # ## Findings or ### F{n} terminates body section extraction
        if line.startswith("## Findings") or _FINDING_HEADER_RE.match(line):
            break

        # Check for section headers
        if line.startswith("## Problem"):
            current_section = "problem"
            continue
        if line.startswith("### Context"):
            current_section = "context"
            continue
        if line.startswith("### Evidence"):
            current_section = "evidence"
            continue
        if line.startswith("### Attempts"):
            current_section = "attempts"
            continue
        # Any other ## or ### header ends current section
        if line.startswith("## ") or line.startswith("### "):
            current_section = None
            continue

        # Skip HTML comment lines
        if _HTML_COMMENT_RE.match(line):
            continue

        if current_section == "problem":
            problem_lines.append(line)
        elif current_section == "context":
            context_lines.append(line)
        elif current_section == "evidence":
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                evidence_items.append(stripped[2:])
        elif current_section == "attempts":
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                attempts_items.append(stripped[2:])

    problem = "\n".join(problem_lines).strip()
    context = "\n".join(context_lines).strip()
    return problem, context, evidence_items, attempts_items


def _extract_findings(body: str) -> list[StackFinding]:
    """Extract ### F{n} finding blocks from the body."""
    lines = body.splitlines()
    findings: list[StackFinding] = []

    # Find all finding block start indices
    finding_starts: list[tuple[int, int, str]] = []  # (line_index, finding_number, title)
    for i, line in enumerate(lines):
        m = _FINDING_HEADER_RE.match(line)
        if m:
            finding_title = (m.group(2) or "").strip()
            finding_starts.append((i, int(m.group(1)), finding_title))

    for idx, (start_line, finding_num, finding_title) in enumerate(finding_starts):
        # Determine end of this finding block
        end_line = finding_starts[idx + 1][0] if idx + 1 < len(finding_starts) else len(lines)

        finding_lines = lines[start_line + 1 : end_line]
        finding = _parse_single_finding(finding_num, finding_title, finding_lines)
        if finding is not None:
            findings.append(finding)

    return findings


def _parse_single_finding(number: int, title: str, lines: list[str]) -> StackFinding | None:
    """Parse a single finding block from its content lines."""
    finding_date = date.today()
    author = "unknown"
    votes = 0
    accepted = False
    body_lines: list[str] = []
    comments: list[str] = []
    in_comments = False
    metadata_found = False

    for line in lines:
        # Check for comments section
        if line.strip() == "#### Comments":
            in_comments = True
            continue

        # Check for metadata line (first occurrence only)
        if not metadata_found:
            m = _METADATA_RE.search(line)
            if m:
                try:
                    finding_date = date.fromisoformat(m.group(1))
                except ValueError:
                    finding_date = date.today()
                author = m.group(2)
                votes = int(m.group(3))
                accepted = m.group(4) == "true"
                metadata_found = True
                continue

        if in_comments:
            stripped = line.strip()
            if stripped:
                comments.append(stripped)
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    return StackFinding(
        number=number,
        title=title,
        date=finding_date,
        author=author,
        votes=votes,
        accepted=accepted,
        body=body,
        comments=comments,
    )

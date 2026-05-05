"""Parser for concept file artifacts from markdown format."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from lexibrary.artifacts.concept import ConceptFile, ConceptFileFrontmatter
from lexibrary.wiki.patterns import extract_wikilinks as _extract_wikilinks

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
# Backtick-delimited paths containing "/" and ending with a known extension
_FILE_REF_RE = re.compile(
    r"`([^`]*?/[^`]+\.(?:py|ts|tsx|js|jsx|yaml|yml|toml|md|json|css|html|sql|sh|rs|go))`"
)


class ConceptValidationError(Exception):
    """Raised by :func:`parse_concept_file_strict` when frontmatter fails validation.

    Carries the human-readable *detail* string extracted from the underlying
    ``yaml.YAMLError`` or Pydantic ``ValidationError`` so callers can surface
    an actionable message without re-catching low-level exceptions.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def parse_concept_file(path: Path) -> ConceptFile | None:
    """Parse a concept file into a ConceptFile model.

    Returns None if the file doesn't exist, has no frontmatter, or
    frontmatter fails validation.  Callers that need a structured error
    on validation failure should use :func:`parse_concept_file_strict` instead.
    """
    try:
        return parse_concept_file_strict(path)
    except ConceptValidationError:
        return None


def parse_concept_file_strict(path: Path) -> ConceptFile | None:
    """Parse a concept file, raising on validation or YAML errors.

    Returns ``None`` only for benign non-parse conditions:

    - The file does not exist.
    - An :class:`OSError` prevented reading the file.
    - The file contains no YAML frontmatter block.

    Raises :class:`ConceptValidationError` for any condition where a
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
        raise ConceptValidationError(f"YAML syntax error in frontmatter: {exc}") from exc

    if not isinstance(data, dict):
        raise ConceptValidationError(
            f"Frontmatter must be a YAML mapping, got {type(data).__name__}"
        )

    try:
        frontmatter = ConceptFileFrontmatter(**data)
    except (TypeError, ValueError) as exc:
        detail = _format_validation_error(exc)
        raise ConceptValidationError(detail) from exc

    body = text[fm_match.end() :]

    summary = _extract_summary(body)
    related_concepts = _extract_wikilinks(body)
    linked_files = _FILE_REF_RE.findall(body)
    decision_log = _extract_decision_log(body)

    return ConceptFile(
        frontmatter=frontmatter,
        body=body,
        summary=summary,
        related_concepts=related_concepts,
        linked_files=linked_files,
        decision_log=decision_log,
        file_path=path,
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


def _extract_summary(body: str) -> str:
    """Extract the first non-empty paragraph before any ## heading."""
    lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            break
        lines.append(line)
    # Join and take first non-empty paragraph (split on blank lines)
    text = "\n".join(lines).strip()
    if not text:
        return ""
    paragraphs = re.split(r"\n\s*\n", text)
    for para in paragraphs:
        stripped = para.strip()
        if stripped:
            return stripped
    return ""


def _extract_decision_log(body: str) -> list[str]:
    """Extract bullet items from a ## Decision Log section."""
    in_section = False
    items: list[str] = []
    for line in body.splitlines():
        if line.startswith("## Decision Log"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                items.append(stripped[2:])
    return items

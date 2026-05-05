"""Parser for convention file artifacts from markdown format."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml

from lexibrary.artifacts.convention import ConventionFile, ConventionFileFrontmatter

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


class ConventionValidationError(Exception):
    """Raised by :func:`parse_convention_file_strict` when frontmatter fails validation.

    Carries the human-readable *detail* string extracted from the underlying
    ``yaml.YAMLError`` or Pydantic ``ValidationError`` so callers can surface
    an actionable message without re-catching low-level exceptions.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def extract_rule(body: str) -> str:
    """Extract the first paragraph from the body as the prescriptive rule.

    The rule is the text up to the first blank line. If the body is empty
    or starts with a blank line, the rule is an empty string.
    """
    stripped = body.strip()
    if not stripped:
        return ""

    # Split on the first blank line (double newline)
    parts = re.split(r"\n\s*\n", stripped, maxsplit=1)
    return parts[0].strip()


def parse_convention_file(path: Path) -> ConventionFile | None:
    """Parse a convention file into a ConventionFile model.

    Returns None if the file doesn't exist, has no frontmatter, or
    frontmatter fails validation.  Callers that need a structured error
    on validation failure should use :func:`parse_convention_file_strict` instead.
    """
    try:
        return parse_convention_file_strict(path)
    except ConventionValidationError:
        return None


def parse_convention_file_strict(path: Path) -> ConventionFile | None:
    """Parse a convention file, raising on validation or YAML errors.

    Returns ``None`` only for benign non-parse conditions:

    - The file does not exist.
    - An :class:`OSError` prevented reading the file.
    - The file contains no YAML frontmatter block.

    Raises :class:`ConventionValidationError` for any condition where a
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
        raise ConventionValidationError(f"YAML syntax error in frontmatter: {exc}") from exc

    if not isinstance(data, dict):
        raise ConventionValidationError(
            f"Frontmatter must be a YAML mapping, got {type(data).__name__}"
        )

    try:
        frontmatter = ConventionFileFrontmatter(**data)
    except (TypeError, ValueError) as exc:
        detail = _format_validation_error(exc)
        raise ConventionValidationError(detail) from exc

    body = text[fm_match.end() :]
    rule = extract_rule(body)

    return ConventionFile(
        frontmatter=frontmatter,
        body=body,
        rule=rule,
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

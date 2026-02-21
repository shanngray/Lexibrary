"""Wikilink resolver — maps ``[[wikilinks]]`` to concept files or guardrails."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import get_close_matches

from lexibrarian.artifacts.concept import ConceptFile
from lexibrarian.wiki.index import ConceptIndex

_BRACKET_RE = re.compile(r"^\[\[(.+?)\]\]$")
_GUARDRAIL_RE = re.compile(r"^GR-\d{3,}$", re.IGNORECASE)


@dataclass(frozen=True)
class ResolvedLink:
    """A wikilink that was successfully resolved to a concept or guardrail."""

    raw: str
    target: str
    kind: str  # "concept", "guardrail", or "alias"
    concept: ConceptFile | None = None


@dataclass(frozen=True)
class UnresolvedLink:
    """A wikilink that could not be resolved."""

    raw: str
    suggestions: list[str] = field(default_factory=list)


class WikilinkResolver:
    """Resolves wikilink references against a :class:`ConceptIndex`.

    Resolution chain (first match wins):

    1. Strip ``[[`` / ``]]`` brackets if present.
    2. If the text matches ``GR-NNN`` guardrail pattern, resolve as guardrail.
    3. Exact concept name match (case-insensitive).
    4. Alias match (case-insensitive).
    5. Fuzzy match via :func:`difflib.get_close_matches`.
    6. Unresolved — attach up to 3 suggestions from fuzzy matching.
    """

    def __init__(self, index: ConceptIndex) -> None:
        self._index = index

    def resolve(self, raw: str) -> ResolvedLink | UnresolvedLink:
        """Resolve a single wikilink string.

        *raw* may include ``[[brackets]]`` or be plain text.
        """
        stripped = _strip_brackets(raw)

        # Guardrail pattern (GR-001, GR-042, etc.)
        if _GUARDRAIL_RE.match(stripped):
            return ResolvedLink(
                raw=raw,
                target=stripped.upper(),
                kind="guardrail",
            )

        # Exact name match
        concept = self._find_exact(stripped)
        if concept is not None:
            return ResolvedLink(
                raw=raw,
                target=concept.frontmatter.title,
                kind="concept",
                concept=concept,
            )

        # Alias match
        concept = self._find_alias(stripped)
        if concept is not None:
            return ResolvedLink(
                raw=raw,
                target=concept.frontmatter.title,
                kind="alias",
                concept=concept,
            )

        # Fuzzy match
        all_names = self._all_names_and_aliases()
        close = get_close_matches(stripped.lower(), [n.lower() for n in all_names], n=3, cutoff=0.6)

        if close:
            # Map lowered matches back to original names
            lower_to_orig = {n.lower(): n for n in all_names}
            best = lower_to_orig.get(close[0])
            if best is not None:
                concept = self._index.find(best)
                if concept is not None:
                    return ResolvedLink(
                        raw=raw,
                        target=concept.frontmatter.title,
                        kind="concept",
                        concept=concept,
                    )

            # Return as unresolved with suggestions
            suggestions = [lower_to_orig.get(c, c) for c in close]
            return UnresolvedLink(raw=raw, suggestions=suggestions)

        return UnresolvedLink(raw=raw)

    def resolve_all(self, links: list[str]) -> tuple[list[ResolvedLink], list[UnresolvedLink]]:
        """Resolve a batch of wikilink strings.

        Returns a tuple of (resolved, unresolved) lists.
        """
        resolved: list[ResolvedLink] = []
        unresolved: list[UnresolvedLink] = []
        for link in links:
            result = self.resolve(link)
            if isinstance(result, ResolvedLink):
                resolved.append(result)
            else:
                unresolved.append(result)
        return resolved, unresolved

    def _find_exact(self, name: str) -> ConceptFile | None:
        """Find concept by exact title (case-insensitive)."""
        needle = name.strip().lower()
        for concept in self._iter_concepts():
            if concept.frontmatter.title.strip().lower() == needle:
                return concept
        return None

    def _find_alias(self, name: str) -> ConceptFile | None:
        """Find concept by alias (case-insensitive)."""
        needle = name.strip().lower()
        for concept in self._iter_concepts():
            for alias in concept.frontmatter.aliases:
                if alias.strip().lower() == needle:
                    return concept
        return None

    def _iter_concepts(self) -> list[ConceptFile]:
        """Return all concepts from the index.

        Accesses the internal ``_concepts`` dict directly to avoid
        alias-collision issues with :meth:`ConceptIndex.find`.
        """
        # pylint: disable=protected-access
        return list(self._index._concepts.values())

    def _all_names_and_aliases(self) -> list[str]:
        """Collect all concept names and aliases for fuzzy matching."""
        result: list[str] = []
        for concept in self._iter_concepts():
            result.append(concept.frontmatter.title)
            result.extend(concept.frontmatter.aliases)
        return result


def _strip_brackets(text: str) -> str:
    """Remove ``[[`` / ``]]`` brackets if present."""
    m = _BRACKET_RE.match(text.strip())
    if m:
        return m.group(1)
    return text.strip()

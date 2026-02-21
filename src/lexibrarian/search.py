"""Unified cross-artifact search for concepts, design files, and Stack posts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table


@dataclass
class SearchResults:
    """Container for grouped search results across artifact types."""

    concepts: list[_ConceptResult] = field(default_factory=list)
    design_files: list[_DesignFileResult] = field(default_factory=list)
    stack_posts: list[_StackResult] = field(default_factory=list)

    def has_results(self) -> bool:
        """Return True if any group has results."""
        return bool(self.concepts or self.design_files or self.stack_posts)

    def render(self, console: Console) -> None:
        """Render grouped results with Rich formatting."""
        if self.concepts:
            console.print()
            table = Table(title="Concepts")
            table.add_column("Name", style="cyan")
            table.add_column("Status")
            table.add_column("Tags")
            table.add_column("Summary", max_width=50)
            for c in self.concepts:
                status_style = {
                    "active": "green",
                    "draft": "yellow",
                    "deprecated": "red",
                }.get(c.status, "dim")
                table.add_row(
                    c.name,
                    f"[{status_style}]{c.status}[/{status_style}]",
                    ", ".join(c.tags),
                    c.summary[:50] if c.summary else "",
                )
            console.print(table)

        if self.design_files:
            console.print()
            table = Table(title="Design Files")
            table.add_column("Source", style="cyan")
            table.add_column("Description", max_width=60)
            table.add_column("Tags")
            for d in self.design_files:
                table.add_row(
                    d.source_path,
                    d.description[:60] if d.description else "",
                    ", ".join(d.tags),
                )
            console.print(table)

        if self.stack_posts:
            console.print()
            table = Table(title="Stack")
            table.add_column("ID", style="cyan")
            table.add_column("Status")
            table.add_column("Votes", justify="right")
            table.add_column("Title")
            table.add_column("Tags")
            for s in self.stack_posts:
                status_style = {
                    "open": "green",
                    "resolved": "blue",
                    "outdated": "yellow",
                    "duplicate": "red",
                }.get(s.status, "dim")
                table.add_row(
                    s.post_id,
                    f"[{status_style}]{s.status}[/{status_style}]",
                    str(s.votes),
                    s.title,
                    ", ".join(s.tags),
                )
            console.print(table)


@dataclass
class _ConceptResult:
    name: str
    status: str
    tags: list[str]
    summary: str


@dataclass
class _DesignFileResult:
    source_path: str
    description: str
    tags: list[str]


@dataclass
class _StackResult:
    post_id: str
    title: str
    status: str
    votes: int
    tags: list[str]


def unified_search(
    project_root: Path,
    *,
    query: str | None = None,
    tag: str | None = None,
    scope: str | None = None,
) -> SearchResults:
    """Search across concepts, design files, and Stack posts.

    Args:
        project_root: Absolute path to the project root.
        query: Free-text search query (matches titles, summaries, bodies).
        tag: Filter by tag across all artifact types.
        scope: Filter by file scope path.

    Returns:
        Grouped :class:`SearchResults`.
    """
    results = SearchResults()

    # --- Concepts ---
    results.concepts = _search_concepts(project_root, query=query, tag=tag, scope=scope)

    # --- Design Files ---
    results.design_files = _search_design_files(project_root, query=query, tag=tag, scope=scope)

    # --- Stack Posts ---
    results.stack_posts = _search_stack_posts(project_root, query=query, tag=tag, scope=scope)

    return results


def _search_concepts(
    project_root: Path,
    *,
    query: str | None,
    tag: str | None,
    scope: str | None,
) -> list[_ConceptResult]:
    """Search concepts via ConceptIndex."""
    from lexibrarian.wiki.index import ConceptIndex

    concepts_dir = project_root / ".lexibrary" / "concepts"
    index = ConceptIndex.load(concepts_dir)

    if len(index) == 0:
        return []

    # Scope filter does not apply to concepts (they are not file-scoped)
    if scope is not None:
        return []

    if tag is not None:
        matches = index.by_tag(tag)
    elif query is not None:
        matches = index.search(query)
    else:
        return []

    return [
        _ConceptResult(
            name=c.frontmatter.title,
            status=c.frontmatter.status,
            tags=list(c.frontmatter.tags),
            summary=c.summary,
        )
        for c in matches
    ]


def _search_design_files(
    project_root: Path,
    *,
    query: str | None,
    tag: str | None,
    scope: str | None,
) -> list[_DesignFileResult]:
    """Search design files by scanning YAML frontmatter and tags."""
    from lexibrarian.artifacts.design_file_parser import parse_design_file

    lexibrary_dir = project_root / ".lexibrary"
    if not lexibrary_dir.is_dir():
        return []

    results: list[_DesignFileResult] = []

    # Scan all .md files in .lexibrary/ (excluding concepts/ and stack/)
    for md_path in sorted(lexibrary_dir.rglob("*.md")):
        # Skip non-design-file directories
        rel = md_path.relative_to(lexibrary_dir)
        parts = rel.parts
        if parts and parts[0] in ("concepts", "stack"):
            continue
        # Skip known non-design files
        if md_path.name in ("START_HERE.md", "HANDOFF.md"):
            continue

        design = parse_design_file(md_path)
        if design is None:
            continue

        # Apply scope filter
        if scope is not None and not design.source_path.startswith(scope):
            continue

        # Apply tag filter
        if tag is not None:
            tag_lower = tag.strip().lower()
            if not any(t.lower() == tag_lower for t in design.tags):
                continue

        # Apply free-text query filter
        if query is not None:
            needle = query.strip().lower()
            searchable = (
                design.frontmatter.description.lower()
                + " "
                + design.source_path.lower()
                + " "
                + " ".join(t.lower() for t in design.tags)
            )
            if needle not in searchable:
                continue

        results.append(
            _DesignFileResult(
                source_path=design.source_path,
                description=design.frontmatter.description,
                tags=list(design.tags),
            )
        )

    return results


def _search_stack_posts(
    project_root: Path,
    *,
    query: str | None,
    tag: str | None,
    scope: str | None,
) -> list[_StackResult]:
    """Search Stack posts via StackIndex."""
    from lexibrarian.stack.index import StackIndex

    idx = StackIndex.build(project_root)
    if len(idx) == 0:
        return []

    # Start with all posts or query results
    matches = idx.search(query) if query is not None else list(idx)

    # Apply tag filter
    if tag is not None:
        tag_set = {p.frontmatter.id for p in idx.by_tag(tag)}
        matches = [p for p in matches if p.frontmatter.id in tag_set]

    # Apply scope filter
    if scope is not None:
        scope_set = {p.frontmatter.id for p in idx.by_scope(scope)}
        matches = [p for p in matches if p.frontmatter.id in scope_set]

    return [
        _StackResult(
            post_id=p.frontmatter.id,
            title=p.frontmatter.title,
            status=p.frontmatter.status,
            votes=p.frontmatter.votes,
            tags=list(p.frontmatter.tags),
        )
        for p in matches
    ]

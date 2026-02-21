# search

**Summary:** Unified cross-artifact search across concepts, design files, and Stack posts — powers `lexi search`.

## Interface

| Name | Key Fields / Signature | Purpose |
| --- | --- | --- |
| `SearchResults` | `concepts`, `design_files`, `stack_posts` | Container for grouped search results across artifact types |
| `SearchResults.has_results` | `() -> bool` | True if any group has results |
| `SearchResults.render` | `(console: Console) -> None` | Render grouped results as Rich tables |
| `unified_search` | `(project_root, *, query?, tag?, scope?) -> SearchResults` | Search across all artifact types with optional query/tag/scope filters |

## Internal Functions

| Name | Purpose |
| --- | --- |
| `_search_concepts` | Search concepts via `ConceptIndex`; supports query and tag filters; scope filter returns empty (concepts are not file-scoped) |
| `_search_design_files` | Scan `.lexibrary/*.md` (excluding `concepts/`, `stack/`, `START_HERE.md`, `HANDOFF.md`); filter by scope, tag, and free-text query against description + source_path + tags |
| `_search_stack_posts` | Search Stack posts via `StackIndex`; supports query, tag, and scope filters |

## Dependencies

- `lexibrarian.wiki.index` -- `ConceptIndex` (lazy import)
- `lexibrarian.artifacts.design_file_parser` -- `parse_design_file` (lazy import)
- `lexibrarian.stack.index` -- `StackIndex` (lazy import)

## Dependents

- `lexibrarian.cli` -- `search` command calls `unified_search()`

## Key Concepts

- All three search backends are independent — results are grouped by type, not interleaved
- Design file search scans all `.md` files in `.lexibrary/` but excludes `concepts/` and `stack/` subdirectories
- Concepts are not file-scoped: passing a `scope` filter returns no concept results
- Stack search combines `StackIndex.search()` with `by_tag()` and `by_scope()` filters
- Rich rendering: each result type gets its own table with type-appropriate columns and color-coded status badges

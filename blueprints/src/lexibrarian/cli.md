# cli

**Summary:** Typer app defining all `lexi` CLI subcommands; wires user intent to `init`, `index`, `update`, `lookup`, `describe`, `concepts`, and `stack` operations.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `app` | `typer.Typer` | Root CLI application registered as the `lexi` entry point |
| `stack_app` | `typer.Typer` | Sub-group for `lexi stack *` commands (post, search, answer, vote, accept, view, list) |
| `concept_app` | `typer.Typer` | Sub-group for `lexi concept *` commands (new, link) |
| `init` | `(*, agent: str \| None) -> None` | **Implemented** -- create `.lexibrary/` skeleton via `create_lexibrary_skeleton()` |
| `index` | `(directory: Path = ".", *, recursive: bool) -> None` | **Implemented** -- generate `.aindex` for a directory; `-r` flag triggers bottom-up recursive indexing |
| `update` | `(path: Path \| None) -> None` | **Implemented** -- generate/update design files via archivist pipeline; single file, directory, or full project; regenerates `START_HERE.md` on full project update |
| `lookup` | `(file: Path) -> None` | **Implemented** -- display design file for a source file; checks scope, warns if stale |
| `describe` | `(directory: Path, description: str) -> None` | **Implemented** -- update the billboard description in a directory's `.aindex` file |
| `concepts` | `(topic: str \| None) -> None` | **Implemented** -- list or search concept files in a Rich table |
| `concept_new` | `(name, *, tag) -> None` | **Implemented** -- create a new concept file from template |
| `concept_link` | `(concept_name, source_file) -> None` | **Implemented** -- add a wikilink to a source file's design file |
| `stack_post` | `(*, title, tag, bead, file, concept) -> None` | **Implemented** -- create a new Stack post with auto-assigned ST-NNN ID, slug filename, print path |
| `stack_search` | `(query, *, tag, scope, status, concept) -> None` | **Implemented** -- search Stack posts by query with optional tag/scope/status/concept filters |
| `stack_answer` | `(post_id, *, body, author) -> None` | **Implemented** -- append a new answer to a Stack post |
| `stack_vote` | `(post_id, direction, *, answer, comment, author) -> None` | **Implemented** -- record up/downvote on post or answer; downvotes require --comment |
| `stack_accept` | `(post_id, *, answer_num) -> None` | **Implemented** -- mark answer as accepted, set post status to resolved |
| `stack_view` | `(post_id) -> None` | **Implemented** -- display full post with Rich formatting (Panel header, Markdown body, answers, comments) |
| `stack_list` | `(*, status, tag) -> None` | **Implemented** -- list Stack posts in a Rich table with optional status/tag filters |
| `search` | `(query: str \| None, *, tag, scope) -> None` | **Implemented** -- unified cross-artifact search via `unified_search()`; searches concepts, design files, and Stack posts by query/tag/scope |
| `validate` | `() -> None` | Stub -- run consistency checks |
| `status` | `(path: Path \| None) -> None` | Stub -- show library health |
| `setup` | `(environment, *, update_flag) -> None` | Stub -- install agent environment rules |
| `daemon` | `(path: Path \| None) -> None` | Stub -- start background file watcher |

## Dependencies

- `lexibrarian.exceptions` -- `LexibraryNotFoundError`
- `lexibrarian.init.scaffolder` -- `create_lexibrary_skeleton`
- `lexibrarian.utils.root` -- `find_project_root`
- `lexibrarian.config.loader` -- `load_config` (lazy import)
- `lexibrarian.indexer.orchestrator` -- `index_directory`, `index_recursive` (lazy import)
- `lexibrarian.archivist.pipeline` -- `UpdateStats`, `update_file`, `update_project` (lazy import in `update`)
- `lexibrarian.archivist.service` -- `ArchivistService` (lazy import in `update`)
- `lexibrarian.llm.rate_limiter` -- `RateLimiter` (lazy import in `update`)
- `lexibrarian.artifacts.design_file_parser` -- `parse_design_file_metadata`, `parse_design_file` (lazy imports)
- `lexibrarian.artifacts.design_file_serializer` -- `serialize_design_file` (lazy import in `concept_link`)
- `lexibrarian.artifacts.aindex_parser` -- `parse_aindex` (lazy import in `describe`)
- `lexibrarian.artifacts.aindex_serializer` -- `serialize_aindex` (lazy import in `describe`)
- `lexibrarian.utils.paths` -- `mirror_path`, `aindex_path` (lazy imports)
- `lexibrarian.wiki.index` -- `ConceptIndex` (lazy import in `concepts`, `concept_link`)
- `lexibrarian.wiki.template` -- `render_concept_template`, `concept_file_path` (lazy import in `concept_new`)
- `lexibrarian.stack.template` -- `render_post_template` (lazy import in `stack_post`)
- `lexibrarian.stack.index` -- `StackIndex` (lazy import in `stack_search`, `stack_list`)
- `lexibrarian.stack.mutations` -- `add_answer`, `record_vote`, `accept_answer` (lazy imports)
- `lexibrarian.stack.parser` -- `parse_stack_post` (lazy import in `stack_view`)
- `lexibrarian.search` -- `unified_search` (lazy import in `search`)

## Key Concepts

- `init`, `index`, `update`, `lookup`, `describe`, `concepts`, `concept new`, `concept link`, `search`, and all `stack` commands are fully implemented; `validate`, `status`, `setup`, `daemon` remain stubs
- `_require_project_root()` resolves project root or exits with user-friendly error
- `console` is a module-level `rich.Console` -- no bare `print()`
- `update` uses `asyncio.run()` to drive the async archivist pipeline
- Stack post IDs are auto-assigned by scanning `.lexibrary/stack/ST-*-*.md` files and incrementing
- Stack helpers: `_stack_dir()` creates stack dir if needed, `_next_stack_id()` scans for next ID, `_slugify()` converts title to filename slug, `_find_post_path()` resolves post ID to file path
- All stack commands use lazy imports to keep CLI startup fast

## Dragons

- Stub commands call `_require_project_root()` so they fail gracefully outside a project -- preserve this check when implementing them
- `index` validates that the target directory exists, is a directory, and is within the project root before proceeding
- `update` lazy-imports archivist modules to keep CLI startup fast
- Stack ID auto-assignment uses filesystem scan -- concurrent creation could cause ID collision (mitigated by single-agent use case)
- The `guardrail_app` and `guardrails`/`guardrail_new` commands were removed in Phase 6 and replaced by `stack_app`

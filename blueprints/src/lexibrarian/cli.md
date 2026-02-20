# cli

**Summary:** Typer app defining all `lexi` CLI subcommands; wires user intent to `init`, `index`, `update`, `lookup`, `describe`, and other library operations.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `app` | `typer.Typer` | Root CLI application registered as the `lexi` entry point |
| `guardrail_app` | `typer.Typer` | Sub-group for `lexi guardrail *` commands |
| `init` | `(*, agent: str \| None) -> None` | **Implemented** -- create `.lexibrary/` skeleton via `create_lexibrary_skeleton()` |
| `index` | `(directory: Path = ".", *, recursive: bool) -> None` | **Implemented** -- generate `.aindex` for a directory; `-r` flag triggers bottom-up recursive indexing |
| `update` | `(path: Path \| None) -> None` | **Implemented** -- generate/update design files via archivist pipeline; single file, directory, or full project; regenerates `START_HERE.md` on full project update |
| `lookup` | `(file: Path) -> None` | **Implemented** -- display design file for a source file; checks scope, warns if stale |
| `describe` | `(directory: Path, description: str) -> None` | **Implemented** -- update the billboard description in a directory's `.aindex` file |
| `concepts` | `(topic: str \| None) -> None` | Stub -- list or search concept files |
| `guardrails` | `(*, scope, concept) -> None` | Stub -- search guardrail threads |
| `guardrail_new` | `(*, file, mistake, resolution) -> None` | Stub -- record a new guardrail thread |
| `search` | `(*, tag, scope) -> None` | Stub -- search artifacts by tag |
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
- `lexibrarian.archivist.start_here` -- `generate_start_here` (lazy import in `update`)
- `lexibrarian.llm.rate_limiter` -- `RateLimiter` (lazy import in `update`)
- `lexibrarian.artifacts.design_file_parser` -- `parse_design_file_metadata` (lazy import in `lookup`)
- `lexibrarian.artifacts.aindex_parser` -- `parse_aindex` (lazy import in `describe`)
- `lexibrarian.artifacts.aindex_serializer` -- `serialize_aindex` (lazy import in `describe`)
- `lexibrarian.utils.paths` -- `mirror_path`, `aindex_path` (lazy imports)

## Key Concepts

- `init`, `index`, `update`, `lookup`, `describe` are fully implemented; other commands are stubs calling `_stub()`
- `_require_project_root()` resolves project root or exits with user-friendly error
- `console` is a module-level `rich.Console` -- no bare `print()`
- `update` uses `asyncio.run()` to drive the async archivist pipeline
- `lookup` checks scope_root, warns on staleness (source hash mismatch), displays design file content
- `describe` parses, updates billboard, re-serializes the `.aindex` file

## Dragons

- Stub commands call `_require_project_root()` so they fail gracefully outside a project -- preserve this check when implementing them
- `index` validates that the target directory exists, is a directory, and is within the project root before proceeding
- `update` lazy-imports archivist modules to keep CLI startup fast

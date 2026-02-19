# cli

**Summary:** Typer app defining all `lexi` CLI subcommands; wires user intent to `init`, `index`, `update`, `daemon`, and other library operations.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `app` | `typer.Typer` | Root CLI application registered as the `lexi` entry point |
| `guardrail_app` | `typer.Typer` | Sub-group for `lexi guardrail *` commands |
| `init` | `(*, agent: str \| None) -> None` | **Implemented** — create `.lexibrary/` skeleton via `create_lexibrary_skeleton()` |
| `index` | `(directory: Path = ".", *, recursive: bool) -> None` | **Implemented** — generate `.aindex` for a directory; `-r` flag triggers bottom-up recursive indexing |
| `lookup` | `(file: Path) -> None` | Stub — return design file for a source file |
| `concepts` | `(topic: str \| None) -> None` | Stub — list or search concept files |
| `guardrails` | `(*, scope, concept) -> None` | Stub — search guardrail threads |
| `guardrail_new` | `(*, file, mistake, resolution) -> None` | Stub — record a new guardrail thread |
| `search` | `(*, tag, scope) -> None` | Stub — search artifacts by tag |
| `update` | `(path: Path \| None) -> None` | Stub — re-index changed files |
| `validate` | `() -> None` | Stub — run consistency checks |
| `status` | `(path: Path \| None) -> None` | Stub — show library health |
| `setup` | `(environment, *, update_flag) -> None` | Stub — install agent environment rules |
| `daemon` | `(path: Path \| None) -> None` | Stub — start background file watcher |

## Dependencies

- `lexibrarian.exceptions` — `LexibraryNotFoundError`
- `lexibrarian.init.scaffolder` — `create_lexibrary_skeleton`
- `lexibrarian.utils.root` — `find_project_root`
- `lexibrarian.config.loader` — `load_config` (imported lazily in `index`)
- `lexibrarian.indexer.orchestrator` — `index_directory`, `index_recursive` (imported lazily in `index`)

## Key Concepts

- `init` and `index` are fully implemented; all other commands are stubs calling `_stub()`
- `_require_project_root()` resolves project root or exits with user-friendly error
- `console` is a module-level `rich.Console` — no bare `print()`
- `index` imports its deps lazily (inside the function) to keep startup fast

## Dragons

- Stub commands call `_require_project_root()` so they fail gracefully outside a project — preserve this check when implementing them
- `index` validates that the target directory exists, is a directory, and is within the project root before proceeding

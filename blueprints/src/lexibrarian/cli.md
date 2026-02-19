# cli

**Summary:** Typer app defining all `lexi` CLI subcommands; wires user intent to `init`, `update`, `daemon`, and other library operations.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `app` | `typer.Typer` | Root CLI application registered as the `lexi` entry point |
| `guardrail_app` | `typer.Typer` | Sub-group for `lexi guardrail *` commands |
| `init` | `(*, agent: str | None) -> None` | Create `.lexibrary/` skeleton via `create_lexibrary_skeleton()` |
| `lookup` | `(file: Path) -> None` | Stub — return design file for a source file |
| `index` | `(directory: Path) -> None` | Stub — return or generate `.aindex` for a directory |
| `concepts` | `(topic: str | None) -> None` | Stub — list or search concept files |
| `guardrails` | `(*, scope, concept) -> None` | Stub — search guardrail threads |
| `guardrail_new` | `(*, file, mistake, resolution) -> None` | Stub — record a new guardrail thread |
| `search` | `(*, tag, scope) -> None` | Stub — search artifacts by tag |
| `update` | `(path: Path | None) -> None` | Stub — re-index changed files |
| `validate` | `() -> None` | Stub — run consistency checks |
| `status` | `(path: Path | None) -> None` | Stub — show library health |
| `setup` | `(environment, *, update_flag) -> None` | Stub — install agent environment rules |
| `daemon` | `(path: Path | None) -> None` | Stub — start background file watcher |

## Dependencies

- `lexibrarian.exceptions` — `LexibraryNotFoundError`
- `lexibrarian.init.scaffolder` — `create_lexibrary_skeleton`
- `lexibrarian.utils.root` — `find_project_root`

## Key Concepts

- Only `init` is fully implemented; all other commands are stubs calling `_stub()`
- `_require_project_root()` resolves project root or exits with user-friendly error
- `console` is a module-level `rich.Console` — no bare `print()`

## Dragons

- Stub commands call `_require_project_root()` so they fail gracefully outside a project — do not remove this check when implementing them

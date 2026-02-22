# cli/lexictl_app

**Summary:** Maintenance Typer CLI app (`lexictl`) providing wizard-based project initialization, design file generation, validation, status reporting, and agent rule setup for library management.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `lexictl_app` | `typer.Typer` | Root maintenance CLI application registered as the `lexictl` entry point |
| `init` | `(*, defaults: bool) -> None` | Run the 8-step init wizard via `run_wizard()`; `--defaults` flag accepts all detected values without prompting; re-init guard prevents overwriting existing `.lexibrary/`; non-TTY guard requires `--defaults` |
| `update` | `(path: Path \| None) -> None` | Generate/update design files via archivist pipeline; single file, directory, or full project; regenerates `START_HERE.md` on full project update |
| `validate` | `(*, severity: str \| None, check: str \| None, json_output: bool) -> None` | Run consistency checks with optional severity/check filters; outputs Rich tables or JSON; exits with `report.exit_code()` |
| `status` | `(path: Path \| None, *, quiet: bool) -> None` | Dashboard showing design file counts/staleness, concept counts by status, stack post counts, validation issues summary, last updated timestamp; `--quiet`/`-q` for CI/hooks single-line output |
| `setup` | `(*, update_flag: bool) -> None` | Install or update agent environment rules; `--update` flag required; reads `agent_environment` from config; calls `generate_rules()` and `ensure_iwh_gitignored()` |
| `daemon` | `(path: Path \| None) -> None` | Stub -- start background file watcher |

## Dependencies

- `lexibrarian.cli._shared` -- `console`, `require_project_root`, `stub`
- `lexibrarian.init.wizard` -- `run_wizard` (lazy import in `init`)
- `lexibrarian.init.scaffolder` -- `create_lexibrary_from_wizard` (lazy import in `init`)
- `lexibrarian.archivist.pipeline` -- `UpdateStats`, `update_file`, `update_project` (lazy import in `update`)
- `lexibrarian.archivist.service` -- `ArchivistService` (lazy import in `update`)
- `lexibrarian.config.loader` -- `load_config` (lazy import in `update`, `status`, `setup`)
- `lexibrarian.llm.rate_limiter` -- `RateLimiter` (lazy import in `update`)
- `lexibrarian.validator` -- `AVAILABLE_CHECKS`, `validate_library` (lazy imports in `validate`, `status`)
- `lexibrarian.artifacts.design_file_parser` -- `parse_design_file_metadata` (lazy import in `status`)
- `lexibrarian.stack.parser` -- `parse_stack_post` (lazy import in `status`)
- `lexibrarian.wiki.parser` -- `parse_concept_file` (lazy import in `status`)
- `lexibrarian.init.rules` -- `generate_rules` (lazy import in `setup`)
- `lexibrarian.iwh.gitignore` -- `ensure_iwh_gitignored` (lazy import in `setup`)

## Dependents

- `lexibrarian.cli.__init__` -- re-exports `lexictl_app`
- `pyproject.toml` -- `lexictl` entry point

## Key Concepts

- `init` uses `run_wizard()` + `create_lexibrary_from_wizard()` instead of the old `create_lexibrary_skeleton()`
- `init` does not call `require_project_root()` -- it creates the project root (uses `Path.cwd()` instead)
- `init` has a re-init guard (checks for existing `.lexibrary/`) and a non-TTY guard (requires `--defaults`)
- `update` uses `asyncio.run()` to drive the async archivist pipeline
- `setup` requires `--update` flag; without it shows usage hint; reads `agent_environment` list from config
- `status` quiet mode (`-q`) outputs a single line for CI/hooks integration; prefix is `"lexictl:"` (not `"lexi:"`)
- All heavy imports are lazy (inside command functions) to keep CLI startup fast

## Dragons

- `validate` exits non-zero when errors are found via `report.exit_code()`; `status` mirrors this behavior
- `status` quiet-mode output changes based on whether there are errors, warnings, both, or neither
- `setup` calls `generate_rules()` with `config.agent_environment`; raises `ValueError` for unsupported environments; also calls `ensure_iwh_gitignored()`
- `update` for a directory argument falls through to the full project update path (pipeline respects `scope_root`)

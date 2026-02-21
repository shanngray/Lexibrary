# init/scaffolder

**Summary:** Creates the `.lexibrary/` directory skeleton and `.lexignore` file idempotently -- never overwrites existing files.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `create_lexibrary_skeleton` | `(project_root: Path) -> list[Path]` | Create dirs (`concepts/`, `stack/`), `.gitkeep` files, template files, and `.lexignore`; return list of paths created |
| `START_HERE_PLACEHOLDER` | `str` | Placeholder content for `START_HERE.md` before `lexi update` runs |
| `HANDOFF_PLACEHOLDER` | `str` | Placeholder content for `HANDOFF.md` |

## Dependencies

- `lexibrarian.config.defaults` -- `DEFAULT_PROJECT_CONFIG_TEMPLATE`

## Dependents

- `lexibrarian.cli.init` -- calls `create_lexibrary_skeleton(project_root)`

## Key Concepts

- Idempotent: checks existence before creating each path; returns empty list if skeleton already exists
- Creates: `.lexibrary/`, `concepts/`, `stack/`, `.gitkeep` files, `config.yaml`, `START_HERE.md`, `HANDOFF.md`
- Creates `.lexignore` at project root (empty file for archivist exclusion patterns)

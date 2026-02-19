# init/scaffolder

**Summary:** Creates the `.lexibrary/` directory skeleton idempotently — never overwrites existing files.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `create_lexibrary_skeleton` | `(project_root: Path) -> list[Path]` | Create dirs (`concepts/`, `guardrails/`), `.gitkeep` files, and template files; return list of paths created |
| `START_HERE_PLACEHOLDER` | `str` | Placeholder content for `START_HERE.md` before `lexi update` runs |
| `HANDOFF_PLACEHOLDER` | `str` | Placeholder content for `HANDOFF.md` |

## Dependencies

- `lexibrarian.config.defaults` — `DEFAULT_PROJECT_CONFIG_TEMPLATE`

## Dependents

- `lexibrarian.cli.init` — calls `create_lexibrary_skeleton(project_root)`

## Key Concepts

- Idempotent: checks existence before creating each path; returns empty list if skeleton already exists
- Creates: `.lexibrary/`, `concepts/`, `guardrails/`, `.gitkeep` files, `config.yaml`, `START_HERE.md`, `HANDOFF.md`

# archivist/pipeline

**Summary:** Per-file and project-wide design file generation pipeline -- coordinates change detection, LLM generation, serialization, and parent .aindex refresh.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `UpdateStats` | `@dataclass` | Accumulated counters: `files_scanned`, `files_unchanged`, `files_agent_updated`, `files_updated`, `files_created`, `files_failed`, `aindex_refreshed`, `token_budget_warnings` |
| `FileResult` | `@dataclass` | Public result from `update_file`: `change`, `aindex_refreshed`, `token_budget_exceeded`, `failed` |
| `update_file` | `async (source_path, project_root, config, archivist) -> FileResult` | Generate or update the design file for a single source file |
| `update_project` | `async (project_root, config, archivist, progress_callback?) -> UpdateStats` | Update all design files in the project scope |

## Dependencies

- `lexibrarian.archivist.change_checker` -- `ChangeLevel`, `check_change`
- `lexibrarian.archivist.dependency_extractor` -- `extract_dependencies`
- `lexibrarian.archivist.service` -- `ArchivistService`, `DesignFileRequest`
- `lexibrarian.artifacts.aindex` -- `AIndexEntry`
- `lexibrarian.artifacts.aindex_parser` -- `parse_aindex`
- `lexibrarian.artifacts.aindex_serializer` -- `serialize_aindex`
- `lexibrarian.artifacts.design_file` -- `DesignFile`, `DesignFileFrontmatter`, `StalenessMetadata`
- `lexibrarian.artifacts.design_file_parser` -- `parse_design_file`, `parse_design_file_frontmatter`, `parse_design_file_metadata`, `_FOOTER_RE`
- `lexibrarian.artifacts.design_file_serializer` -- `serialize_design_file`
- `lexibrarian.ast_parser` -- `compute_hashes`, `parse_interface`, `render_skeleton`
- `lexibrarian.config.schema` -- `LexibraryConfig`
- `lexibrarian.ignore` -- `create_ignore_matcher`
- `lexibrarian.utils.languages` -- `detect_language`
- `lexibrarian.utils.paths` -- `LEXIBRARY_DIR`, `aindex_path`, `mirror_path`

## Dependents

- `lexibrarian.cli` -- `update` command calls `update_file` and `update_project`

## Key Concepts

- `update_file` pipeline: scope check, compute hashes, change detection, then branch on `ChangeLevel`:
  - `UNCHANGED` -- early return
  - `AGENT_UPDATED` -- refresh footer hashes only (no LLM call), preserve agent edits
  - Others -- LLM generation via `ArchivistService`, build `DesignFile` model, serialize, write, refresh parent `.aindex`
- `update_project` discovers files via `rglob("*")`, skips `.lexibrary/`, binary, ignored, and oversized files, then processes each sequentially
- Token budget validation: warns if design file exceeds `config.token_budgets.design_file_tokens` but still writes the file
- Parent `.aindex` refresh: updates the child map entry description when a design file is created or updated

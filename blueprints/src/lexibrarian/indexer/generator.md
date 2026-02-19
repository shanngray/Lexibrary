# indexer/generator

**Summary:** Produces `AIndexFile` models from directory contents without I/O side effects — structural descriptions only, no LLM calls.

## Interface

| Name | Signature | Purpose |
| --- | --- | --- |
| `generate_aindex` | `(directory, project_root, ignore_matcher, binary_extensions) -> AIndexFile` | Scan directory, build file/dir entries with structural descriptions, compute staleness hash |

## Dependencies

- `lexibrarian.artifacts.aindex` — `AIndexEntry`, `AIndexFile`
- `lexibrarian.artifacts.aindex_parser` — `parse_aindex` (reads child `.aindex` for subdir descriptions)
- `lexibrarian.artifacts.design_file` — `StalenessMetadata`
- `lexibrarian.ignore.matcher` — `IgnoreMatcher`
- `lexibrarian.utils.languages` — `EXTENSION_MAP`

## Dependents

- `lexibrarian.indexer.orchestrator` — calls `generate_aindex` as first step

## Key Concepts

- File description: `"<Language> source (<N> lines)"` for text; `"Binary file (<ext>)"` for binary
- Subdir description: reads child `.aindex` from `.lexibrary` mirror if available; falls back to filesystem item count
- Billboard: auto-generated sentence from detected languages (e.g. `"Mixed-language directory (Python, TOML)."`)
- Staleness hash: SHA-256 of sorted directory listing (entry names only, not file contents)
- `_GENERATOR_ID = "lexibrarian-v2"` stamped into metadata

# artifacts/aindex

**Summary:** Pydantic 2 models representing a `.aindex` file artifact — the routing table for a directory.

## Interface

| Name | Key Fields | Purpose |
| --- | --- | --- |
| `AIndexEntry` | `name: str`, `description: str`, `is_directory: bool` | One entry (file or subdir) in the index |
| `AIndexFile` | `directory_path`, `billboard`, `entries: list[AIndexEntry]`, `local_conventions: list[str]`, `metadata: StalenessMetadata` | Full `.aindex` model for a directory |

## Dependencies

- `lexibrarian.artifacts.design_file` — `StalenessMetadata`

## Dependents

- `lexibrarian.artifacts.__init__` — re-exports both models

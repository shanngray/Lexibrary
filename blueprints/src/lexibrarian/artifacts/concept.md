# artifacts/concept

**Summary:** Pydantic 2 model for concept file artifacts — cross-cutting design ideas tracked in `.lexibrary/concepts/`.

## Interface

| Name | Key Fields | Purpose |
| --- | --- | --- |
| `ConceptFile` | `name`, `summary`, `linked_files: list[str]`, `tags`, `decision_log`, `wikilinks`, `metadata: StalenessMetadata | None` | Represents one concept document |

## Dependencies

- `lexibrarian.artifacts.design_file` — `StalenessMetadata`

## Dependents

- `lexibrarian.artifacts.__init__` — re-exports

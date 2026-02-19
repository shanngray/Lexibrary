# artifacts/design_file

**Summary:** Pydantic 2 models for design file artifacts and the shared `StalenessMetadata` footer embedded in all generated artifacts.

## Interface

| Name | Key Fields | Purpose |
| --- | --- | --- |
| `StalenessMetadata` | `source`, `source_hash`, `interface_hash`, `generated: datetime`, `generator` | HTML-comment footer tracking artifact provenance; shared by all artifact types |
| `DesignFile` | `source_path`, `summary`, `interface_contract`, `dependencies`, `dependents`, `tests`, `complexity_warning`, `wikilinks`, `tags`, `guardrail_refs`, `metadata` | Full design file for a single source file |

## Dependents

- `lexibrarian.artifacts.__init__` — re-exports both models
- `lexibrarian.artifacts.aindex` — imports `StalenessMetadata`
- `lexibrarian.artifacts.concept` — imports `StalenessMetadata`

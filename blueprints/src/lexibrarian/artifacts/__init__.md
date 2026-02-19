# artifacts

**Summary:** Re-exports all Pydantic 2 data models for Lexibrarian output artifact types.

## Re-exports

`AIndexEntry`, `AIndexFile`, `ConceptFile`, `DesignFile`, `GuardrailThread`, `StalenessMetadata`

## Dependents

- Future artifact generator and parser modules will import from here
- CLI commands (`lookup`, `concepts`, `guardrails`) will consume these models

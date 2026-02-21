# unified-search Specification

## Purpose
TBD - created by archiving change the-stack. Update Purpose after archive.
## Requirements
### Requirement: Unified search command
`lexi search <query> [--tag <t>] [--scope <path>]` SHALL search across concepts (via `ConceptIndex`), design files (via YAML frontmatter scan), and Stack posts (via `StackIndex`). Results SHALL be grouped under `── Concepts ──`, `── Design Files ──`, and `── Stack ──` headers. Groups with no matches SHALL be omitted.

#### Scenario: Search by tag across all types
- **WHEN** running `lexi search --tag auth` and matching artifacts exist in concepts, design files, and Stack posts
- **THEN** results SHALL be grouped by type with matches from all three artifact types

#### Scenario: Free-text search
- **WHEN** running `lexi search "timezone"`
- **THEN** the search SHALL match titles/summaries/bodies across all artifact types

#### Scenario: Search with no results
- **WHEN** running `lexi search "nonexistent-query"`
- **THEN** the output SHALL indicate no results were found

#### Scenario: Search omits empty groups
- **WHEN** running `lexi search --tag auth` and no Stack posts match
- **THEN** the `── Stack ──` group SHALL be omitted from output

### Requirement: Design file tag search
The unified search SHALL scan design file YAML frontmatter `tags` fields for tag-based queries. For free-text queries, it SHALL match against the `description` field in frontmatter.

#### Scenario: Match design file by tag
- **WHEN** `lexi search --tag security` is run and a design file has `tags: [security, auth]`
- **THEN** the design file SHALL appear in the `── Design Files ──` group

#### Scenario: Match design file by description
- **WHEN** `lexi search "authentication"` is run and a design file has `description: "Handles authentication flow"`
- **THEN** the design file SHALL appear in results

### Requirement: Concept search integration
The unified search SHALL use the existing `ConceptIndex` for concept searches. Tag queries SHALL use `ConceptIndex.by_tag()`. Free-text queries SHALL use `ConceptIndex.search()`.

#### Scenario: Concept search via unified command
- **WHEN** `lexi search "JWT"` is run and a concept named "JWTTokens" exists
- **THEN** the concept SHALL appear in the `── Concepts ──` group


## ADDED Requirements

### Requirement: Design hash re-check before write
The `update_file()` function SHALL re-check the design file's `design_hash` after LLM generation completes and before writing the result. If the hash has changed (indicating an agent edited the file during the LLM call), the LLM output SHALL be discarded.

#### Scenario: No agent edit during LLM call
- **WHEN** `update_file()` completes LLM generation
- **AND** the design file's `design_hash` matches the hash recorded before the LLM call
- **THEN** the LLM output SHALL be written normally

#### Scenario: Agent edited during LLM call
- **WHEN** `update_file()` completes LLM generation
- **AND** the design file's `design_hash` differs from the hash recorded before the LLM call
- **THEN** the LLM output SHALL be discarded
- **AND** the function SHALL return `FileResult(change=ChangeLevel.AGENT_UPDATED, aindex_refreshed=False)`
- **AND** an info-level log message SHALL indicate the discard reason

#### Scenario: Design file did not exist before LLM call
- **WHEN** `update_file()` completes LLM generation for a new file (no prior design file)
- **THEN** the re-check SHALL be skipped (no previous `design_hash` to compare against)
- **AND** the LLM output SHALL be written normally

#### Scenario: Design file has no design_hash metadata
- **WHEN** `update_file()` completes LLM generation
- **AND** the pre-existing design file has no `design_hash` in its metadata
- **THEN** the re-check SHALL be skipped
- **AND** the LLM output SHALL be written normally

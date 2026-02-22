# conflict-detection Specification

## Purpose
TBD - created by archiving change update-triggers. Update Purpose after archive.
## Requirements
### Requirement: Conflict marker detection utility
The system SHALL provide a `has_conflict_markers(source_path)` function in `utils/conflict.py` that checks whether a source file contains git merge conflict markers.

#### Scenario: Clean file
- **WHEN** `has_conflict_markers()` is called on a file without conflict markers
- **THEN** the function SHALL return `False`

#### Scenario: File with conflict markers
- **WHEN** `has_conflict_markers()` is called on a file with lines starting with `<<<<<<<`
- **THEN** the function SHALL return `True`

#### Scenario: Conflict markers not at start of line
- **WHEN** a file contains `<<<<<<<` in the middle of a line (not at the start)
- **THEN** the function SHALL return `False`

#### Scenario: Non-existent file
- **WHEN** `has_conflict_markers()` is called on a file that does not exist
- **THEN** the function SHALL return `False` (not raise an exception)

#### Scenario: Binary content tolerance
- **WHEN** `has_conflict_markers()` is called on a file with binary content
- **THEN** the function SHALL not crash (uses `errors="replace"` on open)

### Requirement: Pipeline skips conflicted files
The `update_file()` function SHALL check for conflict markers before LLM generation and skip files with unresolved merge conflicts.

#### Scenario: Source file has conflict markers
- **WHEN** `update_file()` processes a source file that has conflict markers
- **THEN** the function SHALL return `FileResult(failed=True)` without invoking the LLM
- **AND** a warning SHALL be logged indicating the file was skipped due to merge conflicts

#### Scenario: Source file is clean
- **WHEN** `update_file()` processes a source file without conflict markers
- **THEN** processing SHALL continue normally (no change to existing behavior)


## ADDED Requirements

### Requirement: update_file safety mechanisms
The `update_file()` function SHALL include conflict marker detection and design hash re-check before writing LLM-generated output.

#### Scenario: Conflict marker check before LLM call
- **WHEN** `update_file()` detects a change that requires LLM generation
- **THEN** it SHALL call `has_conflict_markers()` on the source file before reading content
- **AND** if conflict markers are found, it SHALL return `FileResult(failed=True)` with a warning log

#### Scenario: Design hash re-check before write
- **WHEN** `update_file()` completes LLM generation
- **THEN** it SHALL re-read the design file's `design_hash` and compare against the pre-LLM hash
- **AND** if they differ, it SHALL discard the LLM output

### Requirement: Atomic writes for all .lexibrary/ output
All `Path.write_text()` calls in `pipeline.py` that write to `.lexibrary/` SHALL use `atomic_write()`.

#### Scenario: Design file write
- **WHEN** `update_file()` writes a generated design file
- **THEN** it SHALL use `atomic_write()` instead of `design_path.write_text()`

#### Scenario: Footer refresh write
- **WHEN** `_refresh_footer_hashes()` writes an updated design file
- **THEN** it SHALL use `atomic_write()` instead of `design_path.write_text()`

#### Scenario: Aindex file write
- **WHEN** `_refresh_parent_aindex()` writes an updated `.aindex` file
- **THEN** it SHALL use `atomic_write()` instead of `aindex_file_path.write_text()`

### Requirement: Batch update function
The pipeline SHALL provide an `update_files()` function for processing a specific list of source files (see `changed-only-pipeline` spec for detailed requirements).

#### Scenario: Batch update available
- **WHEN** `update_files()` is called with a list of file paths
- **THEN** each file SHALL be processed through the existing `update_file()` pipeline
- **AND** `START_HERE.md` SHALL NOT be regenerated

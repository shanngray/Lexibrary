## ADDED Requirements

### Requirement: Atomic file write utility
The system SHALL provide an `atomic_write(target, content, encoding)` function in `utils/atomic.py` that writes content to a target path atomically using temp-file + `os.replace()`.

#### Scenario: Write to new file
- **WHEN** `atomic_write()` is called with a target path that does not exist
- **THEN** the file SHALL be created with the specified content and encoding

#### Scenario: Overwrite existing file
- **WHEN** `atomic_write()` is called with a target path that already exists
- **THEN** the existing file SHALL be replaced atomically with the new content
- **AND** readers SHALL never see a partially-written file

#### Scenario: Parent directories do not exist
- **WHEN** `atomic_write()` is called with a target whose parent directories do not exist
- **THEN** the parent directories SHALL be created before writing

#### Scenario: Write failure cleanup
- **WHEN** a write failure occurs (e.g., disk full, permission error)
- **THEN** the temp file SHALL be cleaned up
- **AND** the original file (if it existed) SHALL remain unchanged
- **AND** the original exception SHALL be re-raised

#### Scenario: Temp file in same directory
- **WHEN** `atomic_write()` creates a temp file
- **THEN** the temp file SHALL be created in the same directory as the target path
- **AND** this ensures `os.replace()` operates on the same filesystem

### Requirement: Pipeline adopts atomic writes
All `Path.write_text()` calls in `archivist/pipeline.py` that write to `.lexibrary/` SHALL be replaced with `atomic_write()`.

#### Scenario: Design file write uses atomic write
- **WHEN** `update_file()` writes a design file after LLM generation
- **THEN** the write SHALL use `atomic_write()` instead of `design_path.write_text()`

#### Scenario: Footer refresh uses atomic write
- **WHEN** `_refresh_footer_hashes()` writes an updated design file
- **THEN** the write SHALL use `atomic_write()` instead of `design_path.write_text()`

#### Scenario: Aindex refresh uses atomic write
- **WHEN** `_refresh_parent_aindex()` writes an updated `.aindex` file
- **THEN** the write SHALL use `atomic_write()` instead of `aindex_file_path.write_text()`

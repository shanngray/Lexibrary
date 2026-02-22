## ADDED Requirements

### Requirement: Batch file update function
The system SHALL provide an `update_files(file_paths, project_root, config, archivist, progress_callback)` function in `archivist/pipeline.py` that processes a specific list of source files.

#### Scenario: Process list of changed files
- **WHEN** `update_files()` is called with a list of file paths
- **THEN** each file SHALL be processed through `update_file()` sequentially
- **AND** accumulated `UpdateStats` SHALL be returned

#### Scenario: Skip deleted files
- **WHEN** `update_files()` encounters a file path that does not exist (deleted in commit)
- **THEN** the file SHALL be silently skipped

#### Scenario: Skip binary files
- **WHEN** `update_files()` encounters a file with a binary extension
- **THEN** the file SHALL be skipped

#### Scenario: Skip ignored files
- **WHEN** `update_files()` encounters a file matching ignore patterns
- **THEN** the file SHALL be skipped

#### Scenario: Skip .lexibrary contents
- **WHEN** `update_files()` encounters a file inside the `.lexibrary/` directory
- **THEN** the file SHALL be skipped

#### Scenario: No START_HERE regeneration
- **WHEN** `update_files()` completes processing all files
- **THEN** `START_HERE.md` SHALL NOT be regenerated (that is a `update_project()` concern)

#### Scenario: Error handling per file
- **WHEN** `update_files()` encounters an unexpected error processing a file
- **THEN** the error SHALL be logged
- **AND** `files_failed` SHALL be incremented
- **AND** processing SHALL continue with the remaining files

### Requirement: CLI --changed-only flag
The `lexictl update` command SHALL accept a `--changed-only` option that takes a list of file paths.

#### Scenario: Update only specified files
- **WHEN** `lexictl update --changed-only file1.py file2.py` is run
- **THEN** only `file1.py` and `file2.py` SHALL be processed via `update_files()`

#### Scenario: Mutual exclusivity with path argument
- **WHEN** both `path` argument and `--changed-only` option are provided
- **THEN** the command SHALL exit with an error indicating they are mutually exclusive

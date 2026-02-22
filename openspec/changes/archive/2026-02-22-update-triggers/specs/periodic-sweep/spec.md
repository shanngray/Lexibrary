## ADDED Requirements

### Requirement: Sweep skip-if-unchanged
The periodic sweep SHALL check whether any files have changed before running a full project update.

#### Scenario: No changes since last sweep
- **WHEN** a periodic sweep is triggered
- **AND** `sweep_skip_if_unchanged` is `True` in config
- **AND** no files in `scope_root` have `mtime` newer than the last sweep timestamp
- **THEN** the sweep SHALL be skipped entirely
- **AND** a debug-level log message SHALL be recorded

#### Scenario: Changes detected
- **WHEN** a periodic sweep is triggered
- **AND** at least one file in `scope_root` has `mtime` newer than the last sweep timestamp
- **THEN** the full sweep SHALL proceed via `update_project()`

#### Scenario: First sweep always runs
- **WHEN** a periodic sweep is triggered
- **AND** no previous sweep has been recorded (first run)
- **THEN** the sweep SHALL always run

#### Scenario: .lexibrary directory excluded from change scan
- **WHEN** the change scanner walks `scope_root` for modified files
- **THEN** files inside `.lexibrary/` SHALL be excluded from the scan

#### Scenario: Skip-if-unchanged disabled
- **WHEN** `sweep_skip_if_unchanged` is `False` in config
- **THEN** every scheduled sweep SHALL run regardless of file modification times

### Requirement: Sweep uses archivist pipeline
The sweep callback SHALL use `update_project()` from the archivist pipeline.

#### Scenario: Sweep calls update_project
- **WHEN** a sweep is triggered and changes are detected
- **THEN** the sweep SHALL call `asyncio.run(update_project(...))` with the current config and a freshly created `ArchivistService`

### Requirement: Change detection uses os.scandir stat walk
The change detection for sweep-skip-if-unchanged SHALL use `os.scandir()` recursive stat walk, not hashing.

#### Scenario: Stat walk performance
- **WHEN** `_has_changes()` scans for modified files
- **THEN** it SHALL use `os.scandir()` to check `st_mtime` values
- **AND** it SHALL return early on the first file with `mtime` newer than the last sweep
- **AND** it SHALL NOT read file contents or compute hashes

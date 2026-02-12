## ADDED Requirements

### Requirement: Bottom-up directory discovery
The system SHALL discover all directories under a root path, sorted deepest-first (bottom-up ordering). Ignored directories SHALL be pruned during traversal so their contents are never visited.

#### Scenario: Discover directories in bottom-up order
- **WHEN** `discover_directories_bottom_up()` is called on a project tree with nested directories
- **THEN** the returned list SHALL contain all non-ignored directories with deeper directories appearing before shallower ones

#### Scenario: Prune ignored directories
- **WHEN** a directory matches the `IgnoreMatcher` (e.g., `.git/`, `node_modules/`)
- **THEN** that directory and all its descendants SHALL be excluded from the result

#### Scenario: Root directory included
- **WHEN** `discover_directories_bottom_up()` is called
- **THEN** the root directory itself SHALL appear in the result (as the last entry, being the shallowest)

### Requirement: Directory file listing
The system SHALL list files in a single directory, separating them into indexable files and skipped files. Ignored files SHALL be excluded entirely. Files with known binary extensions SHALL be placed in the skipped list. Files that cannot be stat'd SHALL be placed in the skipped list.

#### Scenario: Separate indexable and skipped files
- **WHEN** `list_directory_files()` is called on a directory containing `.py` and `.png` files
- **THEN** `.py` files SHALL appear in the indexable list and `.png` files SHALL appear in the skipped list

#### Scenario: Ignored files excluded entirely
- **WHEN** a file matches the `IgnoreMatcher`
- **THEN** it SHALL not appear in either the indexable or skipped lists

#### Scenario: Empty directory
- **WHEN** `list_directory_files()` is called on an empty directory
- **THEN** both lists SHALL be empty

#### Scenario: Permission denied
- **WHEN** a directory cannot be listed due to `PermissionError`
- **THEN** both lists SHALL be empty (no error raised)

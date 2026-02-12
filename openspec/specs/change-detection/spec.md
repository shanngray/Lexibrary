# change-detection Specification

## Purpose
TBD - created by archiving change crawler-engine. Update Purpose after archive.
## Requirements
### Requirement: Hash-based change detection
The `ChangeDetector` SHALL detect file changes by comparing SHA-256 hashes. A file SHALL be considered changed if it has no cached entry or if its current hash differs from the cached hash.

#### Scenario: New file detected as changed
- **WHEN** `has_changed()` is called for a file with no cached entry
- **THEN** it SHALL return `True`

#### Scenario: Unchanged file detected as not changed
- **WHEN** `has_changed()` is called for a file whose current SHA-256 hash matches the cached hash
- **THEN** it SHALL return `False`

#### Scenario: Modified file detected as changed
- **WHEN** `has_changed()` is called for a file whose current SHA-256 hash differs from the cached hash
- **THEN** it SHALL return `True`

### Requirement: Cache persistence
The `ChangeDetector` SHALL persist its state to a JSON file at the configured cache path. The cache SHALL include a version field for forward compatibility. The cache SHALL only be written to disk when dirty (i.e., when entries have been added or modified).

#### Scenario: Save and load roundtrip
- **WHEN** entries are added via `update()`, saved via `save()`, and a new `ChangeDetector` loads from the same path
- **THEN** all previously cached entries SHALL be available with correct hash, tokens, summary, and timestamp

#### Scenario: No-op save when not dirty
- **WHEN** `save()` is called without any updates
- **THEN** the cache file SHALL not be written

#### Scenario: Corrupted cache handled gracefully
- **WHEN** the cache file contains invalid JSON or an incompatible version
- **THEN** the `ChangeDetector` SHALL start with an empty cache (no error raised)

#### Scenario: Missing cache file
- **WHEN** the cache file does not exist
- **THEN** `load()` SHALL be a no-op and the detector SHALL start with an empty cache

### Requirement: Cache maintenance
The `ChangeDetector` SHALL support pruning entries for deleted files and clearing all entries for full re-crawl.

#### Scenario: Prune deleted files
- **WHEN** `prune_deleted()` is called with a set of existing file paths
- **THEN** cache entries for files not in the set SHALL be removed

#### Scenario: Clear all entries
- **WHEN** `clear()` is called
- **THEN** all cached entries SHALL be removed and the cache SHALL be marked dirty

### Requirement: Cache entry data model
Each cache entry (`FileState`) SHALL store the file's SHA-256 hash, token count, summary text, and last-indexed timestamp in ISO 8601 format.

#### Scenario: Update stores all fields
- **WHEN** `update()` is called with a file path, hash, token count, and summary
- **THEN** the cached `FileState` SHALL contain all provided values plus an ISO 8601 `last_indexed` timestamp


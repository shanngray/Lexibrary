# aindex-write-locks Specification

## Purpose
TBD - created by archiving change update-triggers. Update Purpose after archive.
## Requirements
### Requirement: Per-directory write lock manager
The system SHALL provide a `DirectoryLockManager` class in `utils/locks.py` that provides per-directory `threading.Lock` instances for serialising `.aindex` writes.

#### Scenario: Same directory returns same lock
- **WHEN** `get_lock()` is called twice with the same directory path
- **THEN** the same `threading.Lock` instance SHALL be returned

#### Scenario: Different directories return different locks
- **WHEN** `get_lock()` is called with two different directory paths
- **THEN** different `threading.Lock` instances SHALL be returned

#### Scenario: Lock is a threading Lock
- **WHEN** `get_lock()` returns a lock
- **THEN** it SHALL be an instance of `threading.Lock`

#### Scenario: Thread-safe lock creation
- **WHEN** multiple threads call `get_lock()` concurrently for the same directory
- **THEN** all threads SHALL receive the same lock instance (no duplicate creation)

### Requirement: Sequential MVP compatibility
Under the sequential MVP processing model (D-025), the `DirectoryLockManager` locks SHALL be effectively no-ops but ensure correctness when async processing is added later.

#### Scenario: No-op under sequential processing
- **WHEN** files are processed sequentially (current MVP)
- **THEN** lock acquisition SHALL never block (no contention)


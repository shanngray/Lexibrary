# interface-hashing Specification

## Purpose
TBD - created by archiving change ast-parser. Update Purpose after archive.
## Requirements
### Requirement: parse_interface function
The system SHALL provide a `parse_interface(file_path: Path) -> InterfaceSkeleton | None` function that extracts the public interface from a source file. It SHALL return None if the file extension has no registered grammar, the grammar package is not installed, or the file cannot be read.

#### Scenario: Python file parsed successfully
- **WHEN** calling `parse_interface()` on a valid Python file
- **THEN** it returns an InterfaceSkeleton with the file's public interface

#### Scenario: Unsupported extension returns None
- **WHEN** calling `parse_interface()` on a `.rs` file
- **THEN** it returns None without emitting a warning

#### Scenario: Missing grammar returns None with warning
- **WHEN** calling `parse_interface()` on a `.py` file with tree-sitter-python not installed
- **THEN** it returns None and emits a warning

### Requirement: hash_interface function
The system SHALL provide a `hash_interface(skeleton: InterfaceSkeleton) -> str` function that renders the skeleton to canonical text and returns its SHA-256 hex digest.

#### Scenario: Hash is a valid SHA-256 hex string
- **WHEN** calling `hash_interface()` on any skeleton
- **THEN** it returns a 64-character hexadecimal string

#### Scenario: Same skeleton produces same hash
- **WHEN** calling `hash_interface()` twice on identical skeletons
- **THEN** both calls return the same hash

#### Scenario: Different skeletons produce different hashes
- **WHEN** calling `hash_interface()` on two skeletons that differ in function signatures
- **THEN** the hashes are different

### Requirement: compute_hashes convenience function
The system SHALL provide a `compute_hashes(file_path: Path) -> tuple[str, str | None]` function that returns (content_hash, interface_hash). The content_hash is always available (SHA-256 of full file). The interface_hash is None if no grammar is available.

#### Scenario: File with grammar support
- **WHEN** calling `compute_hashes()` on a Python file with grammars installed
- **THEN** it returns a tuple of (content_hash, interface_hash) where both are 64-char hex strings

#### Scenario: File without grammar support
- **WHEN** calling `compute_hashes()` on a `.txt` file
- **THEN** it returns (content_hash, None)

### Requirement: Hash stability across body-only changes
The interface hash SHALL NOT change when only function/method bodies are modified without changing signatures.

#### Scenario: Body change does not affect interface hash
- **WHEN** computing the interface hash of a file, then modifying a function body (not signature), then recomputing
- **THEN** the interface hash is identical before and after

### Requirement: Hash sensitivity to signature changes
The interface hash SHALL change when any public signature changes (function name, parameter, return type, class name, base class, constant name/type).

#### Scenario: Adding a parameter changes the hash
- **WHEN** computing the interface hash, then adding a parameter to a public function, then recomputing
- **THEN** the interface hash is different

### Requirement: Hash insensitivity to declaration order
The interface hash SHALL NOT change when declarations are reordered in the source file without changing their content.

#### Scenario: Reordering functions does not change hash
- **WHEN** computing the interface hash, then swapping the order of two function definitions, then recomputing
- **THEN** the interface hash is identical


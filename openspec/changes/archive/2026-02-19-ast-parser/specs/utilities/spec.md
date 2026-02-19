## MODIFIED Requirements

### Requirement: File hashing
The system SHALL compute SHA-256 hashes of file contents for integrity checking. Hashing SHALL read files in chunks to handle large files efficiently. The system SHALL additionally provide a `hash_string(text: str) -> str` function that computes the SHA-256 hex digest of a UTF-8 encoded string.

#### Scenario: Hash is computed for small file
- **WHEN** calling `hash_file(path)` on a small text file with known content
- **THEN** it returns a 64-character hexadecimal string (SHA-256 digest)

#### Scenario: Same file content produces same hash
- **WHEN** calling `hash_file()` twice on the same file
- **THEN** both calls return identical hash strings

#### Scenario: Different file content produces different hash
- **WHEN** calling `hash_file()` on two files with different content
- **THEN** the hashes are different

#### Scenario: Large files are hashed in chunks
- **WHEN** calling `hash_file()` on a file larger than the chunk size (8192 bytes by default)
- **THEN** it reads and processes the file in chunks, returning the correct SHA-256 hash

#### Scenario: String hashing produces valid SHA-256
- **WHEN** calling `hash_string("hello world")`
- **THEN** it returns a 64-character hexadecimal SHA-256 digest of the UTF-8 encoded string

#### Scenario: Same string produces same hash
- **WHEN** calling `hash_string()` twice with the same text
- **THEN** both calls return identical hash strings

#### Scenario: Empty string produces valid hash
- **WHEN** calling `hash_string("")`
- **THEN** it returns the SHA-256 hash of an empty byte string (a valid 64-char hex digest)

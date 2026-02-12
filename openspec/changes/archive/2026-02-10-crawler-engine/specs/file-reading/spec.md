## ADDED Requirements

### Requirement: Binary file detection
The system SHALL detect binary files by reading the first 8192 bytes and checking for null byte (`\x00`) presence. Files containing null bytes SHALL be classified as binary. Files that cannot be read SHALL be treated as binary.

#### Scenario: Text file detected as non-binary
- **WHEN** a file contains no null bytes in its first 8192 bytes
- **THEN** `is_binary_file()` SHALL return `False`

#### Scenario: Binary file detected by null bytes
- **WHEN** a file contains one or more null bytes in its first 8192 bytes
- **THEN** `is_binary_file()` SHALL return `True`

#### Scenario: Unreadable file treated as binary
- **WHEN** a file cannot be opened due to an `OSError`
- **THEN** `is_binary_file()` SHALL return `True`

### Requirement: File reading for indexing
The system SHALL read text files for LLM summarization, returning a `FileContent` dataclass with `path`, `content`, `encoding`, `size_bytes`, and `is_truncated` fields. Binary or unreadable files SHALL return `None`.

#### Scenario: Read a normal text file
- **WHEN** `read_file_for_indexing()` is called on a UTF-8 text file within the size limit
- **THEN** it SHALL return a `FileContent` with the full content, `encoding="utf-8"`, and `is_truncated=False`

#### Scenario: Read a file exceeding max size
- **WHEN** `read_file_for_indexing()` is called on a text file larger than `max_size_kb`
- **THEN** it SHALL return a `FileContent` with content truncated to `max_size_kb * 1024` bytes and `is_truncated=True`

#### Scenario: Read a binary file
- **WHEN** `read_file_for_indexing()` is called on a binary file
- **THEN** it SHALL return `None`

#### Scenario: Read a Latin-1 encoded file
- **WHEN** a file fails UTF-8 decoding but succeeds with Latin-1
- **THEN** it SHALL return a `FileContent` with `encoding="latin-1"` and the decoded content

#### Scenario: Read an undecodable file
- **WHEN** a file fails both UTF-8 and Latin-1 decoding
- **THEN** it SHALL return `None`

## ADDED Requirements

### Requirement: Gitignore discovery and parsing
The system SHALL find all `.gitignore` files in a project tree, parse them using the "gitwildmatch" dialect, and return them sorted by directory depth.

#### Scenario: Single .gitignore is found and parsed
- **WHEN** calling `load_gitignore_specs(root)` on a project with one `.gitignore` at the root
- **THEN** it returns a list with one (directory, PathSpec) tuple containing the root directory and parsed patterns

#### Scenario: Hierarchical .gitignore files are found
- **WHEN** calling `load_gitignore_specs(root)` on a project with `.gitignore` at root and in subdirectories
- **THEN** it returns all files sorted by depth (root first), enabling hierarchical override behavior

#### Scenario: Invalid .gitignore patterns are handled
- **WHEN** a `.gitignore` file contains invalid patterns
- **THEN** pathspec parses them without crashing (pathspec is lenient)

### Requirement: Config pattern matching
The system SHALL create a PathSpec from config-defined ignore patterns (e.g., ".aindex", "node_modules/", "*.lock").

#### Scenario: Config patterns are compiled into a PathSpec
- **WHEN** creating a PathSpec from config.ignore.additional_patterns
- **THEN** it successfully matches relative paths against those patterns

#### Scenario: Config patterns match common files and directories
- **WHEN** testing paths like ".aindex", "node_modules/foo", "file.lock" against config patterns
- **THEN** they are correctly identified as matching

### Requirement: Combined ignore matching
The system SHALL provide a single `is_ignored(path)` method that checks config patterns first (cheap), then .gitignore specs in the correct hierarchical order.

#### Scenario: Path matching config pattern returns true
- **WHEN** calling `is_ignored(path)` where path matches a config pattern
- **THEN** it returns True immediately without checking .gitignore

#### Scenario: Path matching .gitignore pattern returns true
- **WHEN** calling `is_ignored(path)` where path matches a .gitignore spec but not config patterns
- **THEN** it returns True

#### Scenario: Path matching no patterns returns false
- **WHEN** calling `is_ignored(path)` where path matches neither config nor .gitignore patterns
- **THEN** it returns False

#### Scenario: Hierarchical .gitignore overrides are respected
- **WHEN** a subdirectory has a .gitignore that negates (!) a pattern from parent .gitignore
- **THEN** the most specific .gitignore (deepest directory) takes precedence

#### Scenario: Relative path comparison is correct
- **WHEN** checking if a path like `/full/path/to/file` is ignored
- **THEN** it is converted to relative path (relative to root) before matching, and matching works correctly

### Requirement: Directory pruning for crawlers
The system SHALL provide a `should_descend(directory)` method that enables crawlers to skip entire directory trees without traversing their contents.

#### Scenario: Ignored directory is not descended
- **WHEN** calling `should_descend(directory)` on a directory matching an ignore pattern
- **THEN** it returns False, signaling crawler to skip this directory

#### Scenario: Non-ignored directory is descended
- **WHEN** calling `should_descend(directory)` on a directory not matching any ignore pattern
- **THEN** it returns True, signaling crawler to traverse its contents

### Requirement: Factory function for matcher creation
The system SHALL provide `create_ignore_matcher(config, root)` that assembles an IgnoreMatcher from configuration and project .gitignore files.

#### Scenario: Matcher respects config.ignore.use_gitignore flag
- **WHEN** config.ignore.use_gitignore is False
- **THEN** `create_ignore_matcher()` does not load any .gitignore files

#### Scenario: Matcher respects config.ignore.use_gitignore flag when true
- **WHEN** config.ignore.use_gitignore is True
- **THEN** `create_ignore_matcher()` discovers and loads all .gitignore files

#### Scenario: Matcher combines gitignore and config patterns
- **WHEN** calling `is_ignored()` on the returned matcher
- **THEN** it checks both .gitignore patterns and config patterns correctly

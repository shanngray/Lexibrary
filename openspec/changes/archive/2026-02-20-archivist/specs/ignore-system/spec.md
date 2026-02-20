## MODIFIED Requirements

### Requirement: Factory function for matcher creation
`create_ignore_matcher(config, root)` assembles IgnoreMatcher from config, `.gitignore` files, and `.lexignore` file. The `IgnoreMatcher` constructor SHALL accept a `lexignore_patterns: list[str]` parameter. The factory SHALL load `.lexignore` from the project root (if it exists) and pass its patterns alongside `.gitignore` and config patterns. Respects `config.ignore.use_gitignore` flag.

#### Scenario: Matcher created with all three layers
- **WHEN** `create_ignore_matcher()` is called and `.gitignore`, `.lexignore`, and config patterns all exist
- **THEN** the IgnoreMatcher SHALL combine patterns from all three sources

#### Scenario: Matcher created without .lexignore
- **WHEN** `create_ignore_matcher()` is called and no `.lexignore` exists
- **THEN** the IgnoreMatcher SHALL use only `.gitignore` and config patterns without error

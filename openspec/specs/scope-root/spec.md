# scope-root Specification

## Purpose
TBD - created by archiving change archivist. Update Purpose after archive.
## Requirements
### Requirement: Scope root configuration
The system SHALL support a `scope_root` field in project config (default: `"."`, project root). The value SHALL be a path relative to the project root.

#### Scenario: Default scope root
- **WHEN** no `scope_root` is configured
- **THEN** the default SHALL be `"."` (project root — all files get design files)

#### Scenario: Custom scope root
- **WHEN** `scope_root` is set to `"src/"`
- **THEN** only files under `src/` SHALL be eligible for design file generation

### Requirement: Design file generation respects scope root
Files within `scope_root` SHALL receive design files when `lexi update` runs. Files outside `scope_root` SHALL NOT receive design files.

#### Scenario: File within scope gets design file
- **WHEN** `lexi update` runs and a file is within `scope_root`
- **THEN** a design file SHALL be generated at the corresponding mirror path

#### Scenario: File outside scope skipped
- **WHEN** `lexi update` encounters a file outside `scope_root`
- **THEN** the file SHALL be skipped (no design file generated)

### Requirement: Files outside scope appear in .aindex
Files outside `scope_root` SHALL still appear in `.aindex` Child Map entries (directory listings) so agents can see they exist.

#### Scenario: Out-of-scope file in directory listing
- **WHEN** a directory contains files both inside and outside `scope_root`
- **THEN** the `.aindex` Child Map SHALL list all files, but only in-scope files get design file descriptions

### Requirement: lexi lookup indicates out-of-scope files
When `lexi lookup` is called for a file outside `scope_root`, the system SHALL print a message indicating the file is outside scope.

#### Scenario: Lookup outside scope
- **WHEN** `lexi lookup` is called for a file outside `scope_root`
- **THEN** the system SHALL print "file is outside scope_root" and exit


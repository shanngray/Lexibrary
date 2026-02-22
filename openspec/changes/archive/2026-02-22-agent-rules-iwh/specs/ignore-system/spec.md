## MODIFIED Requirements

### Requirement: Config pattern matching
The system SHALL create a PathSpec from config-defined ignore patterns. The default `additional_patterns` list SHALL NOT include `.lexibrary/HANDOFF.md` (removed — HANDOFF.md replaced by IWH).

#### Scenario: Config patterns are compiled into a PathSpec
- **WHEN** creating a PathSpec from config.ignore.additional_patterns
- **THEN** it successfully matches relative paths against those patterns

#### Scenario: Default patterns do not include HANDOFF.md
- **WHEN** inspecting the default `IgnoreConfig.additional_patterns`
- **THEN** the list SHALL NOT contain `.lexibrary/HANDOFF.md`

#### Scenario: Config patterns match common files and directories
- **WHEN** testing paths like ".aindex", "node_modules/foo", "file.lock" against config patterns
- **THEN** they are correctly identified as matching

## ADDED Requirements

### Requirement: DaemonConfig schema
The `DaemonConfig` Pydantic model SHALL have the following fields with updated defaults:

- `debounce_seconds: float = 2.0` (unchanged)
- `sweep_interval_seconds: int = 3600` (changed from 300)
- `sweep_skip_if_unchanged: bool = True` (new)
- `git_suppression_seconds: int = 5` (new)
- `watchdog_enabled: bool = False` (new, replaces `enabled`)
- `log_level: str = "info"` (new)

The `enabled: bool = True` field SHALL be removed. The `extra="ignore"` config ensures existing configs with `daemon.enabled` are silently ignored.

#### Scenario: Default DaemonConfig values
- **WHEN** a `DaemonConfig` is created with no arguments
- **THEN** `debounce_seconds` SHALL be `2.0`
- **AND** `sweep_interval_seconds` SHALL be `3600`
- **AND** `sweep_skip_if_unchanged` SHALL be `True`
- **AND** `git_suppression_seconds` SHALL be `5`
- **AND** `watchdog_enabled` SHALL be `False`
- **AND** `log_level` SHALL be `"info"`

#### Scenario: Old enabled field silently ignored
- **WHEN** a `DaemonConfig` is created from YAML containing `enabled: true`
- **THEN** the field SHALL be silently ignored due to `extra="ignore"`
- **AND** no error SHALL be raised

### Requirement: Default config template updated
The `DEFAULT_PROJECT_CONFIG_TEMPLATE` in `config/defaults.py` SHALL reflect the new `DaemonConfig` fields.

#### Scenario: Template contains new daemon fields
- **WHEN** the default config template is rendered
- **THEN** it SHALL include `sweep_skip_if_unchanged: true`
- **AND** it SHALL include `git_suppression_seconds: 5`
- **AND** it SHALL include `watchdog_enabled: false`
- **AND** it SHALL include `log_level: info`
- **AND** it SHALL include `sweep_interval_seconds: 3600`
- **AND** it SHALL NOT include `enabled: true`

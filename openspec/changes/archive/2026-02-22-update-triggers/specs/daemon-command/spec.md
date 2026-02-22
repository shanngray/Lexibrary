## ADDED Requirements

### Requirement: lexictl daemon command replaces stub
The `lexictl daemon` command SHALL be replaced from a stub to a working (but deprecated) command that manages the watchdog daemon.

#### Scenario: Start daemon
- **WHEN** `lexictl daemon start` is run
- **THEN** `DaemonService.run_watchdog()` SHALL be invoked

#### Scenario: Start without watchdog_enabled
- **WHEN** `lexictl daemon start` is run
- **AND** `daemon.watchdog_enabled` is `False` in config
- **THEN** a message SHALL indicate watchdog mode is disabled
- **AND** the command SHALL suggest using `lexictl sweep --watch` instead

#### Scenario: Stop daemon
- **WHEN** `lexictl daemon stop` is run
- **THEN** the PID file SHALL be read
- **AND** SIGTERM SHALL be sent to the daemon process

#### Scenario: Stop with no running daemon
- **WHEN** `lexictl daemon stop` is run
- **AND** no PID file exists
- **THEN** a message SHALL indicate no daemon is running

#### Scenario: Status check
- **WHEN** `lexictl daemon status` is run
- **AND** a PID file exists and the process is running
- **THEN** the daemon SHALL be reported as running with its PID

#### Scenario: Status with stale PID
- **WHEN** `lexictl daemon status` is run
- **AND** a PID file exists but the process is not running
- **THEN** a message SHALL indicate a stale PID file
- **AND** the PID file SHALL be cleaned up

#### Scenario: Default action is start
- **WHEN** `lexictl daemon` is run without an action argument
- **THEN** the default action SHALL be `start`

#### Scenario: Unknown action
- **WHEN** `lexictl daemon foo` is run with an unrecognised action
- **THEN** the command SHALL exit with an error and show valid actions

## ADDED Requirements

### Requirement: Scheduled full crawl
The system SHALL provide a `PeriodicSweep` that triggers a full crawl callback at regular intervals defined by `sweep_interval_seconds` from config, as a safety net for file system events that may be missed by the watcher.

#### Scenario: Sweep fires after configured interval
- **WHEN** the periodic sweep is started with a configured interval
- **THEN** the callback fires after the interval elapses

#### Scenario: Sweep reschedules after completion
- **WHEN** a sweep callback completes (successfully or with an error)
- **THEN** the next sweep is scheduled to fire after another full interval

### Requirement: Sweep stop
The system SHALL support stopping the periodic sweep, preventing any further scheduled callbacks from firing.

#### Scenario: Stop prevents future sweeps
- **WHEN** `stop()` is called on an active periodic sweep
- **THEN** no further sweep callbacks fire

#### Scenario: Stop cancels pending timer
- **WHEN** `stop()` is called while a timer is pending
- **THEN** the pending timer is cancelled immediately

### Requirement: Error isolation
The system SHALL catch and log exceptions raised by the sweep callback without crashing the daemon or preventing future sweep cycles.

#### Scenario: Sweep callback exception is contained
- **WHEN** the sweep callback raises an exception
- **THEN** the exception is logged and the next sweep is still scheduled

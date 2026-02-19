## ADDED Requirements

### Requirement: Event coalescing with configurable delay
The system SHALL provide a `Debouncer` that collects directory change notifications and fires a single callback after a configurable quiet period (`debounce_seconds` from config). Each new notification resets the timer.

#### Scenario: Callback fires after quiet period
- **WHEN** a single directory notification is received and no further notifications arrive within `debounce_seconds`
- **THEN** the callback fires once with a set containing that directory

#### Scenario: Rapid events reset the timer
- **WHEN** multiple notifications arrive in rapid succession (each within `debounce_seconds` of the previous)
- **THEN** the callback fires only once, after `debounce_seconds` of quiet following the last notification

### Requirement: Directory accumulation
The system SHALL accumulate all unique directories from notifications received during the debounce window and pass the complete set to the callback.

#### Scenario: Multiple directories accumulated
- **WHEN** notifications for directories A, B, and C arrive before the debounce timer fires
- **THEN** the callback receives a set containing all three directories {A, B, C}

#### Scenario: Duplicate directories deduplicated
- **WHEN** the same directory is notified multiple times during one debounce window
- **THEN** the callback receives a set containing that directory only once

### Requirement: Thread safety
The system SHALL be safe to call from multiple watchdog threads concurrently without data corruption or race conditions.

#### Scenario: Concurrent notifications from multiple threads
- **WHEN** multiple threads call `notify()` simultaneously
- **THEN** all directories are correctly accumulated without data loss or exceptions

### Requirement: Cancellation
The system SHALL support cancelling any pending debounce timer, discarding accumulated directories without firing the callback.

#### Scenario: Cancel prevents callback
- **WHEN** notifications have been received but `cancel()` is called before the timer fires
- **THEN** the callback is NOT invoked and the pending directory set is cleared

### Requirement: Error isolation
The system SHALL catch and log exceptions raised by the callback without crashing the daemon or preventing future debounce cycles.

#### Scenario: Callback exception is contained
- **WHEN** the callback raises an exception during execution
- **THEN** the exception is logged and the debouncer remains operational for future events

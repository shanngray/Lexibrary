## MODIFIED Requirements

### Requirement: Daemon command
The system SHALL provide a `daemon` command with a `--foreground` flag that starts the `DaemonService`. The command SHALL resolve the project root, load configuration, and pass them to `DaemonService.start()`. When invoked without `--foreground`, it SHALL print a message indicating that background mode is not yet implemented.

#### Scenario: Daemon command with --foreground flag
- **WHEN** running `lexi daemon --foreground`
- **THEN** the `DaemonService` is created with the resolved project root and config, and `start(foreground=True)` is called

#### Scenario: Daemon command without --foreground flag
- **WHEN** running `lexi daemon`
- **THEN** a message is printed indicating that background mode is not yet supported and suggesting `--foreground`

#### Scenario: Daemon command with path argument
- **WHEN** running `lexi daemon --foreground /some/path`
- **THEN** the daemon starts watching the specified path

#### Scenario: Daemon command has help text
- **WHEN** running `lexi daemon --help`
- **THEN** the help text says "Start the background daemon."

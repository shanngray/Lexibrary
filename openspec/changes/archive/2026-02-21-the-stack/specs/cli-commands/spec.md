## MODIFIED Requirements

### Requirement: Rich console output
All CLI commands SHALL use `rich.console.Console` for output. No command SHALL use `typer.echo()` or bare `print()`.

#### Scenario: Output uses Rich formatting
- **WHEN** any CLI command produces output
- **THEN** the output is rendered through a Rich Console instance (supporting colors, tables, panels, and progress bars)

#### Scenario: Stack commands use Rich output
- **WHEN** any `lexi stack` sub-command produces output
- **THEN** the output is rendered through the same Rich Console instance

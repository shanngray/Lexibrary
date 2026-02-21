## ADDED Requirements

### Requirement: Validate command runs library checks
The `lexi validate` command SHALL run all validation checks via `validate_library()` and display the results using Rich rendering. It SHALL exit with code 0 (clean), 1 (errors found), or 2 (warnings only, no errors).

#### Scenario: Validate clean library exits 0
- **WHEN** running `lexi validate` on a library with no issues
- **THEN** the output shows "Summary: 0 errors, 0 warnings, 0 info" and exit code is 0

#### Scenario: Validate with errors exits 1
- **WHEN** running `lexi validate` on a library with broken wikilinks
- **THEN** the output shows the errors grouped under "Errors" and exit code is 1

#### Scenario: Validate with only warnings exits 2
- **WHEN** running `lexi validate` on a library with stale design files but no broken references
- **THEN** the output shows warnings grouped under "Warnings" and exit code is 2

### Requirement: Validate supports severity filter
The `lexi validate --severity <level>` option SHALL filter results to only show issues at or above the given severity level (error > warning > info).

#### Scenario: Severity filter hides info
- **WHEN** running `lexi validate --severity warning`
- **THEN** only error and warning issues are displayed; info issues are excluded

#### Scenario: Severity filter shows errors only
- **WHEN** running `lexi validate --severity error`
- **THEN** only error issues are displayed

### Requirement: Validate supports single check mode
The `lexi validate --check <name>` option SHALL run only the named check function.

#### Scenario: Single check mode
- **WHEN** running `lexi validate --check hash_freshness`
- **THEN** only the hash freshness check runs and its results are displayed

#### Scenario: Invalid check name
- **WHEN** running `lexi validate --check nonexistent`
- **THEN** an error message lists the available check names and exits with code 1

### Requirement: Validate supports JSON output
The `lexi validate --json` option SHALL output the validation report as valid JSON to stdout, suitable for programmatic consumption.

#### Scenario: JSON output is valid
- **WHEN** running `lexi validate --json`
- **THEN** stdout contains valid JSON with "issues" and "summary" keys

#### Scenario: JSON output with severity filter
- **WHEN** running `lexi validate --json --severity warning`
- **THEN** the JSON output only contains issues at warning or error severity

## MODIFIED Requirements

### Requirement: Status command shows project state
The `lexi status` command SHALL display a compact health dashboard showing: artifact counts by type (design files with stale count, concepts by status, Stack posts by status), issue counts by severity (from lightweight validation — errors and warnings only), and the last update timestamp as relative time. It SHALL exit with code 0 (clean), 1 (errors), or 2 (warnings only). It SHALL accept a `--quiet` flag for single-line output suitable for hooks.

#### Scenario: Status shows artifact counts
- **WHEN** running `lexi status` on a project with 47 design files, 15 concepts, and 8 Stack posts
- **THEN** the output shows file, concept, and Stack counts with breakdowns

#### Scenario: Status shows issue summary
- **WHEN** running `lexi status` on a project with 0 errors and 3 warnings
- **THEN** the output includes "Issues: 0 errors, 3 warnings"

#### Scenario: Status quiet mode healthy
- **WHEN** running `lexi status --quiet` on a healthy library
- **THEN** the single-line output is "lexi: library healthy" and exit code is 0

#### Scenario: Status quiet mode with warnings
- **WHEN** running `lexi status --quiet` on a library with 3 warnings
- **THEN** the single-line output is "lexi: 3 warnings — run `lexi validate`" and exit code is 2

#### Scenario: Status exits with same codes as validate
- **WHEN** the library has errors
- **THEN** `lexi status` exits with code 1

## MODIFIED Requirements

### Requirement: Lookup command returns design file
`lexi lookup <file>` SHALL return the design file content for a source file, followed by an `## Applicable Conventions` section listing inherited Local Conventions from parent `.aindex` files.
- SHALL check scope: if file is outside `scope_root`, print message and exit
- SHALL compute mirror path and read the design file
- If design file exists → print its content via Rich Console
- If design file doesn't exist → suggest running `lexi update <file>`
- SHALL check staleness: if source_hash differs from current file hash, print warning before content
- SHALL walk from the file's parent directory up to `scope_root`, parsing each `.aindex` for `local_conventions`
- If any conventions are found → append an `## Applicable Conventions` section grouped by source directory
- If no conventions exist → no extra section appended

#### Scenario: Lookup existing design file
- **WHEN** `lexi lookup src/foo.py` is run and a design file exists
- **THEN** the design file content SHALL be printed

#### Scenario: Lookup missing design file
- **WHEN** `lexi lookup src/foo.py` is run and no design file exists
- **THEN** the system SHALL suggest running `lexi update src/foo.py`

#### Scenario: Lookup shows staleness warning
- **WHEN** `lexi lookup src/foo.py` is run and the source file has changed since the design file was generated
- **THEN** a staleness warning SHALL be displayed before the content

#### Scenario: Lookup outside scope_root
- **WHEN** `lexi lookup scripts/deploy.sh` is run and `scripts/` is outside scope_root
- **THEN** the system SHALL print a message indicating the file is outside scope_root

#### Scenario: Lookup shows inherited conventions
- **WHEN** `lexi lookup src/payments/processor.py` is run and `src/payments/.aindex` and `src/.aindex` both have Local Conventions
- **THEN** the output includes an "## Applicable Conventions" section with conventions from both directories

#### Scenario: Lookup with no conventions
- **WHEN** `lexi lookup src/utils/helpers.py` is run and no parent `.aindex` files have Local Conventions
- **THEN** no extra conventions section is appended

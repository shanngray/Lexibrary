## ADDED Requirements

### Requirement: Index command generates .aindex for a directory
The `lexi index` command SHALL accept a `directory` argument (default `.`) and a `-r`/`--recursive` boolean flag (default `False`). It SHALL require an initialized `.lexibrary/` directory to be present (walk up from CWD to find it), and generate `.aindex` files via the indexer module.

Without `--recursive`: generates a single `.aindex` for the specified directory.
With `--recursive`: generates `.aindex` files for all directories in the tree bottom-up.

On completion, the command SHALL print a summary via `rich.console.Console` showing directories indexed, files found, and any errors.

#### Scenario: Index single directory writes .aindex
- **WHEN** running `lexi index src/` in a project with an initialized `.lexibrary/`
- **THEN** a `.aindex` file SHALL be written at `.lexibrary/src/.aindex` and the command exits with code 0

#### Scenario: Index recursive indexes all directories
- **WHEN** running `lexi index -r .`
- **THEN** `.aindex` files SHALL be written for all directories in the project tree (bottom-up) and the command exits with code 0

#### Scenario: Index fails without .lexibrary/
- **WHEN** running `lexi index src/` in a directory tree with no `.lexibrary/`
- **THEN** the command SHALL print an error message and exit with a non-zero code

#### Scenario: Index fails for nonexistent directory
- **WHEN** running `lexi index nonexistent/`
- **THEN** the command SHALL print an error message and exit with a non-zero code

#### Scenario: Index fails for directory outside project root
- **WHEN** running `lexi index /tmp/other/`
- **THEN** the command SHALL print an error message indicating the directory is outside the project root

#### Scenario: Index displays progress for recursive mode
- **WHEN** running `lexi index -r .` on a multi-directory project
- **THEN** Rich progress output SHALL be displayed during indexing

#### Scenario: Index displays summary on completion
- **WHEN** `lexi index` or `lexi index -r` completes
- **THEN** the output SHALL include a count of directories indexed and files found

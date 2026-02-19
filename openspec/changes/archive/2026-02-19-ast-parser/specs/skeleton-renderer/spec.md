## ADDED Requirements

### Requirement: Deterministic canonical rendering
The system SHALL render an InterfaceSkeleton into a deterministic canonical text string suitable for hashing. The same skeleton SHALL always produce the exact same text output.

#### Scenario: Same skeleton produces same output
- **WHEN** rendering the same InterfaceSkeleton twice
- **THEN** both outputs are byte-identical

#### Scenario: Reordered declarations produce same output
- **WHEN** rendering two skeletons that differ only in declaration order (e.g., functions listed in different order)
- **THEN** both outputs are identical (due to alphabetical sorting)

### Requirement: Alphabetical sorting
The system SHALL sort all lists alphabetically by name before rendering: constants, functions, classes, methods within classes, class_variables within classes, and exports.

#### Scenario: Functions are sorted
- **WHEN** rendering a skeleton with functions named "zebra", "alpha", "middle"
- **THEN** the output lists them in order: alpha, middle, zebra

#### Scenario: Methods within a class are sorted
- **WHEN** rendering a class with methods named "save", "delete", "create"
- **THEN** the methods appear in order: create, delete, save

### Requirement: Version prefix
The system SHALL prefix the canonical text with `skeleton:v1\n` as the first line. This enables future format changes without silently invalidating all existing hashes.

#### Scenario: Output starts with version prefix
- **WHEN** rendering any InterfaceSkeleton
- **THEN** the first line of the output is exactly `skeleton:v1`

### Requirement: Section ordering
The system SHALL render sections in a fixed order: constants, functions, classes, exports.

#### Scenario: Sections appear in correct order
- **WHEN** rendering a skeleton with all section types populated
- **THEN** constants appear first, then functions, then classes, then exports

### Requirement: Compact line format
The system SHALL use a compact, one-line-per-declaration format. No file paths, no line numbers, no comments, no trailing whitespace.

#### Scenario: Constant rendering
- **WHEN** rendering a ConstantSig with name="MAX_RETRIES" and type_annotation="int"
- **THEN** the output line is `const:MAX_RETRIES:int`

#### Scenario: Function rendering
- **WHEN** rendering a FunctionSig with name="authenticate", params (username:str, password:str), return_type="bool"
- **THEN** the output line is `func:authenticate(username:str,password:str)->bool`

#### Scenario: Class rendering with methods
- **WHEN** rendering a ClassSig with name="AuthService", base "BaseService", and a method "login"
- **THEN** the output includes `class:AuthService(BaseService)` followed by indented method lines

#### Scenario: Export rendering
- **WHEN** rendering an export "authenticate"
- **THEN** the output line is `export:authenticate`

### Requirement: No file path or metadata in rendered text
The system SHALL NOT include the file_path, language, or any other metadata in the rendered canonical text. Only the structural interface is rendered.

#### Scenario: File path is excluded
- **WHEN** rendering an InterfaceSkeleton with file_path="src/auth.py"
- **THEN** the string "src/auth.py" does not appear in the output

### Requirement: Empty skeleton produces minimal output
The system SHALL produce a valid (non-empty) output for an empty skeleton, containing at minimum the version prefix.

#### Scenario: Empty skeleton rendering
- **WHEN** rendering an InterfaceSkeleton with no constants, functions, classes, or exports
- **THEN** the output is exactly `skeleton:v1\n`

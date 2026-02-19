## ADDED Requirements

### Requirement: Extract function declarations
The system SHALL extract top-level function declarations from JavaScript source files, capturing: function name, parameter names (without type annotations), and whether the function is async.

#### Scenario: Simple function
- **WHEN** parsing `function processData(input) { ... }`
- **THEN** the skeleton contains a FunctionSig with name="processData", one parameter with type_annotation=None

#### Scenario: Async function
- **WHEN** parsing `async function fetchData(url) { ... }`
- **THEN** the skeleton contains a FunctionSig with is_async=True

### Requirement: Extract arrow functions assigned to constants
The system SHALL extract top-level arrow functions assigned to `const` declarations as function signatures.

#### Scenario: Arrow function const
- **WHEN** parsing `const handler = (req, res) => { ... }`
- **THEN** the skeleton contains a FunctionSig with name="handler" and two parameters

#### Scenario: Async arrow function
- **WHEN** parsing `const fetchData = async (url) => { ... }`
- **THEN** the skeleton contains a FunctionSig with name="fetchData" and is_async=True

### Requirement: Extract class declarations
The system SHALL extract class declarations including: class name, base class (extends), and public methods.

#### Scenario: Class with methods
- **WHEN** parsing `class UserService { constructor(db) { ... } getUser(id) { ... } }`
- **THEN** the skeleton contains a ClassSig with name="UserService" and methods including "constructor" and "getUser"

#### Scenario: Class with extends
- **WHEN** parsing `class Admin extends User { ... }`
- **THEN** the skeleton contains a ClassSig with bases=["User"]

### Requirement: Extract export statements
The system SHALL extract ES module exports (`export`, `export default`) and populate the skeleton's exports list. CommonJS `module.exports` SHALL also be detected.

#### Scenario: Named export
- **WHEN** parsing `export function greet() { ... }`
- **THEN** "greet" appears in the skeleton's exports list

#### Scenario: Default export
- **WHEN** parsing `export default class App { ... }`
- **THEN** "App" appears in the skeleton's exports list

#### Scenario: module.exports object
- **WHEN** parsing `module.exports = { foo, bar }`
- **THEN** "foo" and "bar" appear in the skeleton's exports list

### Requirement: No type annotations
The system SHALL set all type-related fields to None for JavaScript files since JavaScript has no native type annotation syntax.

#### Scenario: All type fields are None
- **WHEN** parsing any JavaScript function
- **THEN** parameter type_annotation, return_type, and constant type_annotation are all None

### Requirement: Handle JSX files
The system SHALL parse `.jsx` files using the same JavaScript grammar. JSX elements in function bodies SHALL be ignored.

#### Scenario: JSX component file
- **WHEN** parsing a `.jsx` file with a function component returning JSX
- **THEN** the function signature is extracted but JSX content is not in the skeleton

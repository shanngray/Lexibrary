## ADDED Requirements

### Requirement: Extract function declarations
The system SHALL extract top-level function declarations from TypeScript source files, capturing: function name, parameter names with type annotations, return type, and whether the function is async.

#### Scenario: Typed function
- **WHEN** parsing a file containing `function greet(name: string): string { ... }`
- **THEN** the skeleton contains a FunctionSig with name="greet", parameter type_annotation="string", return_type="string"

#### Scenario: Async function
- **WHEN** parsing a file containing `async function fetchData(url: string): Promise<Response> { ... }`
- **THEN** the skeleton contains a FunctionSig with is_async=True and return_type="Promise<Response>"

### Requirement: Extract class declarations
The system SHALL extract class declarations including: class name, base classes (extends), implemented interfaces, and public methods with full signatures.

#### Scenario: Class with extends and implements
- **WHEN** parsing `class UserService extends BaseService implements IUserService { ... }`
- **THEN** the skeleton contains a ClassSig with appropriate bases

#### Scenario: Constructor is extracted
- **WHEN** parsing a class with a `constructor(...)` method
- **THEN** the skeleton includes a FunctionSig named "constructor" with is_method=True

### Requirement: Extract interface declarations
The system SHALL extract TypeScript interface declarations, treating them as class-like structures with methods and properties but no implementation.

#### Scenario: Interface with methods
- **WHEN** parsing `interface IUserService { getUser(id: string): User; deleteUser(id: string): void; }`
- **THEN** the skeleton contains a ClassSig-like entry with the interface name and method signatures

### Requirement: Extract type alias declarations
The system SHALL extract type alias declarations as constants with the alias name.

#### Scenario: Simple type alias
- **WHEN** parsing `type UserId = string;`
- **THEN** the skeleton contains a ConstantSig with name="UserId", type_annotation="string"

#### Scenario: Complex type alias
- **WHEN** parsing `type Result<T> = Success<T> | Error;`
- **THEN** the skeleton contains a ConstantSig with name="Result"

### Requirement: Extract enum declarations
The system SHALL extract enum declarations as class-like structures.

#### Scenario: Simple enum
- **WHEN** parsing `enum Status { Active, Inactive, Pending }`
- **THEN** the skeleton contains an entry for the enum with name="Status"

### Requirement: Extract export statements
The system SHALL extract explicit export declarations (`export`, `export default`) and populate the skeleton's exports list.

#### Scenario: Named export
- **WHEN** parsing `export function greet() { ... }`
- **THEN** "greet" appears in the skeleton's exports list

#### Scenario: Default export
- **WHEN** parsing `export default class App { ... }`
- **THEN** "App" appears in the skeleton's exports list

### Requirement: Extract module-level constants
The system SHALL extract module-level `const` and `let` declarations with type annotations.

#### Scenario: Typed const declaration
- **WHEN** parsing `const MAX_RETRIES: number = 3;`
- **THEN** the skeleton contains a ConstantSig with name="MAX_RETRIES", type_annotation="number"

### Requirement: Handle TSX files
The system SHALL parse `.tsx` files using the TSX sub-grammar. JSX elements in function bodies SHALL be ignored (bodies are never parsed).

#### Scenario: TSX component file
- **WHEN** parsing a `.tsx` file with a function component returning JSX
- **THEN** the function signature is extracted but JSX content is not included in the skeleton

### Requirement: Handle generic type parameters
The system SHALL capture generic type parameters in function and class signatures where present.

#### Scenario: Generic function
- **WHEN** parsing `function identity<T>(value: T): T { ... }`
- **THEN** the function signature captures the generic type parameter information

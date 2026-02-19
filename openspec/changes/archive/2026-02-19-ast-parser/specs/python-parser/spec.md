## ADDED Requirements

### Requirement: Extract top-level functions
The system SHALL extract top-level function definitions from Python source files, capturing: function name, parameter names with type annotations and defaults, return type annotation, and whether the function is async.

#### Scenario: Simple function with typed parameters
- **WHEN** parsing a file containing `def authenticate(username: str, password: str) -> bool:`
- **THEN** the skeleton contains a FunctionSig with name="authenticate", two typed parameters, and return_type="bool"

#### Scenario: Async function
- **WHEN** parsing a file containing `async def fetch_data(url: str) -> bytes:`
- **THEN** the skeleton contains a FunctionSig with is_async=True

#### Scenario: Function with default parameters
- **WHEN** parsing a file containing `def retry(attempts: int = 3, delay: float = 1.0) -> None:`
- **THEN** the parameters have default values "3" and "1.0" as strings

#### Scenario: Function without type annotations
- **WHEN** parsing a file containing `def process(data):`
- **THEN** the parameter's type_annotation is None and return_type is None

### Requirement: Extract class definitions
The system SHALL extract top-level class definitions including: class name, base classes, and public methods (with full signature details).

#### Scenario: Class with base classes
- **WHEN** parsing a file containing `class AuthService(BaseService, Configurable):`
- **THEN** the skeleton contains a ClassSig with bases=["BaseService", "Configurable"]

#### Scenario: Class methods are extracted
- **WHEN** parsing a class with public methods
- **THEN** each public method appears as a FunctionSig with is_method=True

### Requirement: Detect structural method modifiers
The system SHALL detect `staticmethod`, `classmethod`, and `property` modifiers on class methods and set the corresponding boolean flags on FunctionSig. Detection SHALL use tree-sitter node structure, not decorator text.

#### Scenario: Static method detection
- **WHEN** parsing a class method decorated with `@staticmethod`
- **THEN** the FunctionSig has is_static=True

#### Scenario: Class method detection
- **WHEN** parsing a class method decorated with `@classmethod`
- **THEN** the FunctionSig has is_class_method=True

#### Scenario: Property detection
- **WHEN** parsing a class method decorated with `@property`
- **THEN** the FunctionSig has is_property=True

### Requirement: Exclude private symbols
The system SHALL exclude functions and methods whose names start with `_` from the skeleton, EXCEPT for `__init__` and `__new__` which SHALL always be included.

#### Scenario: Private function is excluded
- **WHEN** parsing a file containing `def _internal_helper():`
- **THEN** the skeleton does not include this function

#### Scenario: __init__ is included
- **WHEN** parsing a class with an `__init__` method
- **THEN** the skeleton includes the `__init__` method

#### Scenario: __new__ is included
- **WHEN** parsing a class with a `__new__` method
- **THEN** the skeleton includes the `__new__` method

#### Scenario: Other dunder methods are excluded
- **WHEN** parsing a class with `__repr__` and `__str__` methods
- **THEN** the skeleton does not include these methods

### Requirement: Extract module-level constants
The system SHALL extract module-level constants, identified by UPPER_CASE naming convention or the presence of a type annotation on the assignment.

#### Scenario: UPPER_CASE constant
- **WHEN** parsing a file containing `MAX_RETRIES = 3`
- **THEN** the skeleton contains a ConstantSig with name="MAX_RETRIES"

#### Scenario: Type-annotated constant
- **WHEN** parsing a file containing `timeout: float = 30.0`
- **THEN** the skeleton contains a ConstantSig with name="timeout", type_annotation="float"

#### Scenario: Regular assignment is excluded
- **WHEN** parsing a file containing `result = compute()`
- **THEN** the skeleton does not include this as a constant

### Requirement: Extract __all__ exports
The system SHALL extract the value of `__all__` when assigned as a literal list or tuple of strings. Dynamic `__all__` modifications SHALL be ignored.

#### Scenario: Literal __all__ list
- **WHEN** parsing a file containing `__all__ = ["Foo", "Bar"]`
- **THEN** the skeleton's exports field contains ["Bar", "Foo"] (sorted)

#### Scenario: Dynamic __all__ is ignored
- **WHEN** parsing a file containing `__all__ = get_exports()`
- **THEN** the skeleton's exports field is empty

### Requirement: Handle syntax errors gracefully
The system SHALL produce a partial InterfaceSkeleton from files with syntax errors, extracting whatever tree-sitter can parse. It SHALL NOT raise an exception.

#### Scenario: File with syntax error
- **WHEN** parsing a Python file with a syntax error midway through
- **THEN** the parser returns an InterfaceSkeleton with whatever could be extracted before/around the error

### Requirement: Extract only top-level and class-level declarations
The system SHALL only extract declarations at the module level and immediately inside class bodies. Nested functions, nested classes, and declarations inside function bodies SHALL be excluded.

#### Scenario: Nested function is excluded
- **WHEN** parsing a file where a function is defined inside another function
- **THEN** only the outer function appears in the skeleton

# ast-models Specification

## Purpose
TBD - created by archiving change ast-parser. Update Purpose after archive.
## Requirements
### Requirement: ParameterSig model
The system SHALL provide a `ParameterSig` Pydantic model representing a function/method parameter with fields: `name` (str, required), `type_annotation` (str | None, default None), `default` (str | None, default None). The `default` field SHALL store the string representation of the default value.

#### Scenario: Parameter with all fields
- **WHEN** creating a `ParameterSig(name="timeout", type_annotation="float", default="30.0")`
- **THEN** all three fields are accessible and the model validates successfully

#### Scenario: Parameter with name only
- **WHEN** creating a `ParameterSig(name="args")`
- **THEN** `type_annotation` is None and `default` is None

#### Scenario: Parameter model serialises to dict
- **WHEN** calling `.model_dump()` on a ParameterSig
- **THEN** it returns a dict with keys `name`, `type_annotation`, `default`

### Requirement: ConstantSig model
The system SHALL provide a `ConstantSig` Pydantic model representing a module-level constant or exported variable with fields: `name` (str, required), `type_annotation` (str | None, default None).

#### Scenario: Constant with type annotation
- **WHEN** creating a `ConstantSig(name="MAX_RETRIES", type_annotation="int")`
- **THEN** both fields are accessible

#### Scenario: Constant without type annotation
- **WHEN** creating a `ConstantSig(name="DEFAULT_TIMEOUT")`
- **THEN** `type_annotation` is None

### Requirement: FunctionSig model
The system SHALL provide a `FunctionSig` Pydantic model representing a function or method signature with fields: `name` (str), `parameters` (list[ParameterSig], default []), `return_type` (str | None, default None), `is_async` (bool, default False), `is_method` (bool, default False), `is_static` (bool, default False), `is_class_method` (bool, default False), `is_property` (bool, default False).

#### Scenario: Simple function signature
- **WHEN** creating a `FunctionSig(name="process")`
- **THEN** all boolean flags default to False, parameters is empty, return_type is None

#### Scenario: Async method with parameters
- **WHEN** creating a `FunctionSig(name="fetch", is_async=True, is_method=True, parameters=[ParameterSig(name="self"), ParameterSig(name="url", type_annotation="str")], return_type="Response")`
- **THEN** `is_async` is True, `is_method` is True, and parameters and return_type are set

### Requirement: ClassSig model
The system SHALL provide a `ClassSig` Pydantic model representing a class signature with fields: `name` (str), `bases` (list[str], default []), `methods` (list[FunctionSig], default []), `class_variables` (list[ConstantSig], default []).

#### Scenario: Class with bases and methods
- **WHEN** creating a `ClassSig(name="AuthService", bases=["BaseService"], methods=[FunctionSig(name="login", is_method=True)])`
- **THEN** all fields are accessible and the model validates

#### Scenario: Empty class
- **WHEN** creating a `ClassSig(name="EmptyMixin")`
- **THEN** `bases`, `methods`, and `class_variables` are all empty lists

### Requirement: InterfaceSkeleton model
The system SHALL provide an `InterfaceSkeleton` Pydantic model representing the complete public interface of a source file with fields: `file_path` (str), `language` (str), `constants` (list[ConstantSig], default []), `functions` (list[FunctionSig], default []), `classes` (list[ClassSig], default []), `exports` (list[str], default []).

#### Scenario: Complete skeleton with all sections
- **WHEN** creating an InterfaceSkeleton with constants, functions, classes, and exports
- **THEN** all fields are accessible and the model validates

#### Scenario: Empty skeleton for empty file
- **WHEN** creating an `InterfaceSkeleton(file_path="empty.py", language="python")`
- **THEN** constants, functions, classes, and exports are all empty lists


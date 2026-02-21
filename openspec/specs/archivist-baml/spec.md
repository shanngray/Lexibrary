# archivist-baml Specification

## Purpose
TBD - created by archiving change archivist. Update Purpose after archive.
## Requirements
### Requirement: DesignFileOutput BAML type
The system SHALL define a `DesignFileOutput` type in `baml_src/types.baml` with fields:
- `summary` (string) — single sentence description
- `interface_contract` (string) — fenced code block content for the interface contract section
- `dependencies` (DesignFileDependency[]) — list of dependency path + description pairs
- `tests` (string?) — test file path or description, nullable
- `complexity_warning` (string?) — prose warning, nullable
- `wikilinks` (string[]) — list of concept names for wikilink references
- `tags` (string[]) — 3-7 short lowercase labels

#### Scenario: BAML type generation
- **WHEN** `baml-cli generate` is run
- **THEN** the Python `baml_client` SHALL include a `DesignFileOutput` class with all specified fields

### Requirement: DesignFileDependency BAML type
The system SHALL define a `DesignFileDependency` type in `baml_src/types.baml` with fields:
- `path` (string) — relative file path within the project
- `description` (string) — brief description of the dependency relationship

#### Scenario: Dependency type available
- **WHEN** `baml-cli generate` is run
- **THEN** the Python `baml_client` SHALL include a `DesignFileDependency` class

### Requirement: StartHereOutput BAML type
The system SHALL define a `StartHereOutput` type in `baml_src/types.baml` with fields:
- `topology` (string) — Mermaid diagram or ASCII tree of top-level structure
- `ontology` (string) — 5-15 key domain terms with one-line definitions
- `navigation_by_intent` (string) — task-oriented routing table
- `convention_index` (string) — compact list of convention names with descriptions
- `navigation_protocol` (string) — 3-5 bullet instructions on using the library

#### Scenario: StartHere type available
- **WHEN** `baml-cli generate` is run
- **THEN** the Python `baml_client` SHALL include a `StartHereOutput` class

### Requirement: ArchivistGenerateDesignFile BAML function
The system SHALL define an `ArchivistGenerateDesignFile` function in `baml_src/archivist_design_file.baml` accepting:
- `source_path` (string)
- `source_content` (string)
- `interface_skeleton` (string?) — nullable for non-code files
- `language` (string?) — nullable for non-code files
- `existing_design_file` (string?) — nullable for new files
- `available_concepts` (string[]?) — nullable list of known concept names for wikilink suggestions

The function SHALL return `DesignFileOutput`. The prompt SHALL instruct the LLM to:
- Describe *why*, not *what*
- Keep `summary` to a single sentence
- Flag edge cases and non-obvious behaviour
- Extract dependencies from actual import paths observed in source
- Suggest 3-7 short lowercase tags
- When updating, preserve relevant human/agent-added context
- When `available_concepts` is provided, prefer suggesting wikilinks from the available list rather than inventing new concept names. Only suggest concepts that are genuinely relevant to the source file.

#### Scenario: Generate design file for new Python file
- **WHEN** `ArchivistGenerateDesignFile` is called with a Python source file and interface skeleton
- **THEN** it SHALL return a DesignFileOutput with populated summary, interface_contract, and dependencies

#### Scenario: Generate design file for non-code file
- **WHEN** `ArchivistGenerateDesignFile` is called with a YAML file (no interface skeleton, no language)
- **THEN** it SHALL return a DesignFileOutput with prose interface_contract and empty dependencies

#### Scenario: Generate with available concepts
- **WHEN** `ArchivistGenerateDesignFile` is called with `available_concepts=["JWT Auth", "Rate Limiting"]` and the source file relates to authentication
- **THEN** the `wikilinks` field in the output SHALL prefer `"JWT Auth"` over inventing a new name

#### Scenario: Generate without available concepts
- **WHEN** `ArchivistGenerateDesignFile` is called with `available_concepts=null`
- **THEN** the function SHALL still return wikilinks based on the LLM's own judgment (backward compatible)

### Requirement: ArchivistGenerateStartHere BAML function
The system SHALL define an `ArchivistGenerateStartHere` function in `baml_src/archivist_start_here.baml` accepting:
- `project_name` (string)
- `directory_tree` (string)
- `aindex_summaries` (string)
- `existing_start_here` (string?) — nullable for first generation

The function SHALL return `StartHereOutput`. The prompt SHALL instruct the LLM to keep total output under 500-800 tokens.

#### Scenario: Generate START_HERE for project
- **WHEN** `ArchivistGenerateStartHere` is called with project topology
- **THEN** it SHALL return a StartHereOutput with all five sections populated

### Requirement: Per-provider Archivist BAML clients
The system SHALL define named BAML clients in `baml_src/clients.baml`:
- `AnthropicArchivist` — provider anthropic, model claude-sonnet-4-6, max_tokens 1500
- `OpenAIArchivist` — provider openai, model configurable, max_completion_tokens 1500

Both clients SHALL use `retry_policy DefaultRetry` and read API keys from environment variables.

#### Scenario: Anthropic client configuration
- **WHEN** the BAML Anthropic client is used
- **THEN** it SHALL use `env.ANTHROPIC_API_KEY` and `max_tokens: 1500`

#### Scenario: OpenAI client configuration
- **WHEN** the BAML OpenAI client is used
- **THEN** it SHALL use `env.OPENAI_API_KEY` and `max_completion_tokens: 1500`

### Requirement: Runtime client routing via ClientRegistry
The system SHALL use BAML's `ClientRegistry` Python API to override which client an Archivist function uses at runtime, based on `LLMConfig.provider` configuration. If `ClientRegistry` does not support per-call override, the fallback SHALL be defining functions with a default client and using environment variables for provider switching.

#### Scenario: Route to Anthropic provider
- **WHEN** `LLMConfig.provider` is `"anthropic"`
- **THEN** Archivist BAML calls SHALL use the `AnthropicArchivist` client

#### Scenario: Route to OpenAI provider
- **WHEN** `LLMConfig.provider` is `"openai"`
- **THEN** Archivist BAML calls SHALL use the `OpenAIArchivist` client


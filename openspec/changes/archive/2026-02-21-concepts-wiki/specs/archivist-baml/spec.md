## MODIFIED Requirements

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

## MODIFIED Requirements

### Requirement: Single file summarization via LLMService
The system SHALL provide an `LLMService.summarize_file()` async method that accepts a `FileSummaryRequest` and returns a `FileSummaryResult` with a non-empty summary. The method SHALL catch specific API error types and return descriptive fallback summaries rather than raising, except for authentication errors which SHALL raise `LLMError`.

#### Scenario: Successful single file summarization
- **WHEN** calling `summarize_file()` with a valid `FileSummaryRequest` containing path, content, and language
- **THEN** it returns a `FileSummaryResult` with the file's path and a non-empty summary string

#### Scenario: LLM error produces fallback summary
- **WHEN** calling `summarize_file()` and the LLM call raises an exception
- **THEN** it returns a `FileSummaryResult` with summary "Summary unavailable (error)" and does not raise

#### Scenario: Timeout produces specific fallback
- **WHEN** calling `summarize_file()` and the LLM call times out
- **THEN** it returns a `FileSummaryResult` with summary `"Summary unavailable (timeout)"` and logs a warning

#### Scenario: Auth error escalates
- **WHEN** calling `summarize_file()` and the LLM call receives a 401 or 403 response
- **THEN** it SHALL raise `LLMError` with a message containing "Check your API key"

### Requirement: Batch file summarization via LLMService
The system SHALL provide an `LLMService.summarize_files_batch()` async method that accepts a list of `FileSummaryRequest` objects and returns one `FileSummaryResult` per input. The method SHALL catch API errors and return fallback summaries for the entire batch, except for authentication errors which SHALL raise `LLMError`.

#### Scenario: Successful batch summarization
- **WHEN** calling `summarize_files_batch()` with a list of `FileSummaryRequest` objects
- **THEN** it returns a list of `FileSummaryResult` objects with the same count as the input, each with a non-empty summary

#### Scenario: Empty batch returns empty list
- **WHEN** calling `summarize_files_batch()` with an empty list
- **THEN** it returns an empty list without making any LLM calls

#### Scenario: Batch LLM error produces fallback summaries
- **WHEN** calling `summarize_files_batch()` and the LLM call raises an exception
- **THEN** it returns fallback `FileSummaryResult` objects for all inputs with summary "Summary unavailable (error)"

### Requirement: Directory summarization via LLMService
The system SHALL provide an `LLMService.summarize_directory()` async method that accepts a `DirectorySummaryRequest` and returns a summary string. The method SHALL catch API errors and return a fallback, except for authentication errors which SHALL raise `LLMError`.

#### Scenario: Successful directory summarization
- **WHEN** calling `summarize_directory()` with a `DirectorySummaryRequest` containing directory path, file_list, and subdir_list
- **THEN** it returns a non-empty string summarizing the directory's purpose

#### Scenario: Directory LLM error produces fallback
- **WHEN** calling `summarize_directory()` and the LLM call raises an exception
- **THEN** it returns "Summary unavailable." and does not raise

## ADDED Requirements

### Requirement: Token counter protocol
The system SHALL define a `TokenCounter` protocol with three methods: `count(text: str) -> int`, `count_file(path: Path) -> int`, and a `name` property returning a human-readable string.

#### Scenario: Count text tokens
- **WHEN** a backend receives text via `count(text)`
- **THEN** it returns a non-negative integer representing the token count

#### Scenario: Count file tokens
- **WHEN** a backend receives a file path via `count_file(path)`
- **THEN** it reads the file and returns the token count

#### Scenario: Backend identifies itself
- **WHEN** caller accesses the `name` property
- **THEN** it returns a descriptive string like "tiktoken (cl100k_base)" or "approximate (chars/4)"

### Requirement: Tiktoken backend
The system SHALL provide a `TiktokenCounter` backend using OpenAI's tiktoken library with configurable encoding model.

#### Scenario: Count with cl100k_base encoding
- **WHEN** `TiktokenCounter(model="cl100k_base")` counts "Hello, world!"
- **THEN** it returns the exact BPE token count for that encoding

#### Scenario: Count file with tiktoken
- **WHEN** `TiktokenCounter` counts a UTF-8 file
- **THEN** it reads the file content and returns accurate token count

#### Scenario: Handle encoding errors gracefully
- **WHEN** file contains invalid UTF-8 bytes
- **THEN** system replaces invalid bytes and continues counting without crashing

### Requirement: Anthropic API backend
The system SHALL provide an `AnthropicCounter` backend that calls the Anthropic `count_tokens` API with configurable model name.

#### Scenario: Count via API
- **WHEN** `AnthropicCounter(model="claude-sonnet-4-5-20250514")` counts text
- **THEN** it calls the Anthropic API and returns the `input_tokens` count

#### Scenario: Use API key from environment
- **WHEN** `AnthropicCounter` is instantiated
- **THEN** it reads `ANTHROPIC_API_KEY` from environment variables

#### Scenario: Network call per count
- **WHEN** caller invokes `count()` or `count_file()`
- **THEN** backend makes a network request to Anthropic API

### Requirement: Approximate fallback backend
The system SHALL provide an `ApproximateCounter` backend that estimates tokens as `len(text) / 4` with no external dependencies.

#### Scenario: Approximate token count
- **WHEN** `ApproximateCounter` counts 100 characters
- **THEN** it returns 25 tokens

#### Scenario: Minimum one token
- **WHEN** `ApproximateCounter` counts an empty or very short string
- **THEN** it returns at least 1 token

#### Scenario: No external dependencies
- **WHEN** `ApproximateCounter` is imported
- **THEN** it requires no third-party libraries (tiktoken, anthropic, etc.)

### Requirement: Factory function
The system SHALL provide a `create_tokenizer(config: TokenizerConfig)` factory function that instantiates the appropriate backend.

#### Scenario: Create tiktoken backend
- **WHEN** `create_tokenizer(TokenizerConfig(backend="tiktoken", model="cl100k_base"))` is called
- **THEN** it returns a `TiktokenCounter` instance with cl100k_base encoding

#### Scenario: Create anthropic backend
- **WHEN** `create_tokenizer(TokenizerConfig(backend="anthropic_api", model="claude-sonnet-4-5-20250514"))` is called
- **THEN** it returns an `AnthropicCounter` instance with the specified model

#### Scenario: Create approximate backend
- **WHEN** `create_tokenizer(TokenizerConfig(backend="approximate"))` is called
- **THEN** it returns an `ApproximateCounter` instance

#### Scenario: Unknown backend raises error
- **WHEN** `create_tokenizer(TokenizerConfig(backend="unknown"))` is called
- **THEN** it raises a `ValueError` with a descriptive message

#### Scenario: Lazy import of backends
- **WHEN** factory creates a backend
- **THEN** it imports the backend module only when needed (not at factory import time)

### Requirement: Encoding error tolerance
The system SHALL handle files with mixed or invalid encodings gracefully without crashing.

#### Scenario: Replace invalid bytes
- **WHEN** any backend reads a file with `encoding="utf-8", errors="replace"`
- **THEN** invalid byte sequences are replaced with the replacement character and counting proceeds

#### Scenario: Count continues after encoding error
- **WHEN** a file contains a mix of valid and invalid UTF-8
- **THEN** the backend returns a token count for the replaced content

### Requirement: Backend name reporting
Each backend SHALL expose its configuration via the `name` property for debugging and logging.

#### Scenario: Tiktoken reports model
- **WHEN** `TiktokenCounter(model="cl100k_base").name` is accessed
- **THEN** it returns a string containing "tiktoken" and "cl100k_base"

#### Scenario: Anthropic reports model
- **WHEN** `AnthropicCounter(model="claude-sonnet-4-5-20250514").name` is accessed
- **THEN** it returns a string containing "anthropic" and the model name

#### Scenario: Approximate reports method
- **WHEN** `ApproximateCounter().name` is accessed
- **THEN** it returns a string containing "approximate" and "chars/4"

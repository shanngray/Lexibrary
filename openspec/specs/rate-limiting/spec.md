# rate-limiting Specification

## Purpose
TBD - created by archiving change llm-integration-baml. Update Purpose after archive.
## Requirements
### Requirement: Async token-bucket rate limiter
The system SHALL provide a `RateLimiter` class that enforces a configurable requests-per-minute limit using a token-bucket algorithm with async support.

#### Scenario: First acquire is immediate
- **WHEN** calling `acquire()` on a freshly created `RateLimiter`
- **THEN** it returns without any delay

#### Scenario: Rapid calls are throttled
- **WHEN** calling `acquire()` twice in rapid succession on a `RateLimiter` with a configured interval
- **THEN** the second call waits at least the configured interval before returning

#### Scenario: Concurrent acquires are serialized
- **WHEN** multiple coroutines call `acquire()` concurrently
- **THEN** each call is serialized via an async lock and each respects the minimum interval from the previous call

### Requirement: Rate limiter configurable RPM
The system SHALL accept a `requests_per_minute` parameter that determines the minimum interval between requests as `60 / requests_per_minute` seconds.

#### Scenario: Default rate limit
- **WHEN** creating a `RateLimiter` with no arguments
- **THEN** it defaults to 50 requests per minute (1.2 second interval)

#### Scenario: Custom rate limit
- **WHEN** creating a `RateLimiter` with `requests_per_minute=120`
- **THEN** the minimum interval between requests is 0.5 seconds

### Requirement: LLM service integrates rate limiter
The system SHALL pass all LLM calls through the rate limiter's `acquire()` method before making the actual API call.

#### Scenario: Single file summarization is rate-limited
- **WHEN** calling `LLMService.summarize_file()`
- **THEN** it calls `rate_limiter.acquire()` before invoking the BAML client function

#### Scenario: Batch summarization is rate-limited
- **WHEN** calling `LLMService.summarize_files_batch()`
- **THEN** it calls `rate_limiter.acquire()` before invoking the BAML batch function

#### Scenario: Directory summarization is rate-limited
- **WHEN** calling `LLMService.summarize_directory()`
- **THEN** it calls `rate_limiter.acquire()` before invoking the BAML directory function


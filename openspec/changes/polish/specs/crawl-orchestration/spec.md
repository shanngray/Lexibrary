## MODIFIED Requirements

### Requirement: Full bottom-up crawl
The `full_crawl()` function SHALL orchestrate a complete bottom-up crawl of the project tree. It SHALL discover directories deepest-first, process each directory (read files, detect changes, summarize via LLM, generate `.aindex`), and return a `CrawlStats` summary. The crawl SHALL handle file system errors gracefully, skipping affected files or directories and continuing with the rest.

#### Scenario: Crawl produces .aindex files in every directory
- **WHEN** `full_crawl()` is called on a project tree with multiple directories
- **THEN** a `.aindex` file SHALL exist in every non-ignored directory after the crawl completes

#### Scenario: Bottom-up processing order
- **WHEN** `full_crawl()` processes directories
- **THEN** child directories SHALL be processed before their parent directories, ensuring child `.aindex` summaries are available when the parent is indexed

#### Scenario: Permission denied on file skips gracefully
- **WHEN** a file raises `PermissionError` during read
- **THEN** the crawler SHALL skip the file, log a warning, include it in `.aindex` with description `"Permission denied"`, and increment `CrawlStats.errors`

#### Scenario: File deleted during crawl skips gracefully
- **WHEN** a file raises `FileNotFoundError` during read (deleted between discovery and read)
- **THEN** the crawler SHALL skip the file, log a warning, and not include it in `.aindex`

#### Scenario: Write failure on iandex continues crawl
- **WHEN** writing a `.aindex` file raises `OSError`
- **THEN** the crawler SHALL log an error, increment `CrawlStats.errors`, and continue processing remaining directories

#### Scenario: LLMError aborts the crawl
- **WHEN** the LLM service raises `LLMError` (e.g., auth failure)
- **THEN** the crawl SHALL stop and the `LLMError` SHALL propagate to the CLI for user-friendly display

### Requirement: File categorization during crawl
The crawl engine SHALL categorize files into: changed (needs LLM summarization), cached (reuse summary), and skipped (binary/unreadable, listed with generic description and `tokens=0`).

#### Scenario: Binary files listed with generic description
- **WHEN** a file has a known binary extension (e.g., `.png`)
- **THEN** it SHALL appear in the `.aindex` with `tokens=0` and a description like `"Binary file (png)"`

#### Scenario: Cached files reuse summary
- **WHEN** a file has not changed since the last crawl
- **THEN** its `FileEntry` SHALL use the cached token count and summary

#### Scenario: Broken symlink skipped
- **WHEN** `stat()` fails on a symlink target
- **THEN** the crawler SHALL skip the file and log a debug message

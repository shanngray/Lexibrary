## ADDED Requirements

### Requirement: Full bottom-up crawl
The `full_crawl()` function SHALL orchestrate a complete bottom-up crawl of the project tree. It SHALL discover directories deepest-first, process each directory (read files, detect changes, summarize via LLM, generate `.aindex`), and return a `CrawlStats` summary.

#### Scenario: Crawl produces .aindex files in every directory
- **WHEN** `full_crawl()` is called on a project tree with multiple directories
- **THEN** a `.aindex` file SHALL exist in every non-ignored directory after the crawl completes

#### Scenario: Bottom-up processing order
- **WHEN** `full_crawl()` processes directories
- **THEN** child directories SHALL be processed before their parent directories, ensuring child `.aindex` summaries are available when the parent is indexed

### Requirement: Incremental crawling
The crawl engine SHALL use the `ChangeDetector` to skip unchanged files. Unchanged files SHALL reuse their cached summaries without making LLM calls. Changed files SHALL be re-read, re-tokenized, and re-summarized via the LLM.

#### Scenario: Second crawl uses cache
- **WHEN** `full_crawl()` is run a second time on the same project without file changes
- **THEN** no file summarization LLM calls SHALL be made (only directory summarization calls)

#### Scenario: Modified file re-summarized
- **WHEN** a file has been modified between crawl runs
- **THEN** that file SHALL be re-read and re-summarized via the LLM

### Requirement: File categorization during crawl
The crawl engine SHALL categorize files into: changed (needs LLM summarization), cached (reuse summary), and skipped (binary/unreadable, listed with generic description and `tokens=0`).

#### Scenario: Binary files listed with generic description
- **WHEN** a file has a known binary extension (e.g., `.png`)
- **THEN** it SHALL appear in the `.aindex` with `tokens=0` and a description like `"Binary file (png)"`

#### Scenario: Cached files reuse summary
- **WHEN** a file has not changed since the last crawl
- **THEN** its `FileEntry` SHALL use the cached token count and summary

### Requirement: Batch and individual LLM summarization
The crawl engine SHALL batch small files (under 2048 characters) into grouped LLM calls using `summarize_files_batch()`. Files at or above 2048 characters SHALL use individual `summarize_file()` calls. Batches SHALL respect the `max_files_per_llm_batch` config.

#### Scenario: Small files batched together
- **WHEN** multiple changed files have content under 2048 characters
- **THEN** they SHALL be sent to the LLM in batch calls of up to `max_files_per_llm_batch` files

#### Scenario: Large file summarized individually
- **WHEN** a changed file has content at or above 2048 characters
- **THEN** it SHALL be summarized via an individual LLM call

### Requirement: Directory summarization
The crawl engine SHALL generate a directory summary via the LLM by passing the list of file entries and subdirectory entries. Subdirectory descriptions SHALL be read from their child `.aindex` files.

#### Scenario: Directory summary includes child summaries
- **WHEN** a directory contains subdirectories with `.aindex` files
- **THEN** the directory summary request SHALL include those subdirectory descriptions

#### Scenario: Unindexed child directory
- **WHEN** a child directory has no `.aindex` file
- **THEN** it SHALL appear in the summary request with description `"(not yet indexed)"`

### Requirement: Dry-run mode
The `full_crawl()` function SHALL support a `dry_run` parameter. When `True`, the crawl SHALL compute stats but SHALL NOT write any `.aindex` files or persist the cache.

#### Scenario: Dry run produces stats without side effects
- **WHEN** `full_crawl()` is called with `dry_run=True`
- **THEN** it SHALL return valid `CrawlStats` but no `.aindex` files SHALL be created and the cache SHALL not be saved

### Requirement: Crawl statistics
`full_crawl()` SHALL return a `CrawlStats` dataclass with counts for: `directories_indexed`, `files_summarized`, `files_cached`, `files_skipped`, `llm_calls`, and `errors`.

#### Scenario: Stats accurately reflect crawl activity
- **WHEN** a crawl processes 3 directories, summarizes 5 files, caches 2, skips 1 binary, and makes 4 LLM calls
- **THEN** `CrawlStats` SHALL report those exact counts

### Requirement: Progress callback
The `full_crawl()` function SHALL accept an optional `progress_callback` callable that is invoked for each directory processed, receiving the current index (1-based), total count, and directory name.

#### Scenario: Progress callback invoked per directory
- **WHEN** `full_crawl()` is called with a `progress_callback`
- **THEN** the callback SHALL be called once per directory with `(current, total, dir_name)`

### Requirement: Cache saved after crawl
After a non-dry-run crawl completes, the `ChangeDetector` cache SHALL be saved to disk.

#### Scenario: Cache persisted after crawl
- **WHEN** `full_crawl()` completes with `dry_run=False`
- **THEN** `change_detector.save()` SHALL have been called

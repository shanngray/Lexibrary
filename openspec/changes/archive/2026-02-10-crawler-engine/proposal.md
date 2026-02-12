## Why

Phases 1-4 built all prerequisite components (config, ignore, tokenizer, indexer, LLM service) but there is no orchestrator to tie them together. Without the crawler engine, `lexi crawl` cannot produce `.aindex` files — the core deliverable of the entire tool.

## What Changes

- Add `src/lexibrarian/crawler/file_reader.py` — binary detection and size-limited file reading for LLM summarization
- Add `src/lexibrarian/crawler/discovery.py` — bottom-up directory traversal with ignore-pattern filtering
- Add `src/lexibrarian/crawler/change_detector.py` — SHA-256 hash-based change detection with JSON cache persistence
- Add `src/lexibrarian/crawler/engine.py` — main crawl orchestrator wiring discovery, file reader, change detector, tokenizer, LLM service, and indexer
- Update `src/lexibrarian/crawler/__init__.py` — export `full_crawl` and `CrawlStats`
- Add `binary_extensions` field to `CrawlConfig` (the plan references it but it's missing from the current schema)
- Add comprehensive tests for all crawler components

## Capabilities

### New Capabilities

- `file-reading`: Binary detection and size-limited text file reading for LLM consumption
- `directory-discovery`: Bottom-up directory traversal with ignore-pattern filtering
- `change-detection`: SHA-256 hash-based incremental change detection with persistent JSON cache
- `crawl-orchestration`: Main crawl engine that coordinates all components to produce `.aindex` files for an entire project tree

### Modified Capabilities

- `config-system`: Add `binary_extensions` list to `CrawlConfig` for known binary file extensions

## Impact

- **New files**: 4 modules in `src/lexibrarian/crawler/`, 4 test modules in `tests/test_crawler/`
- **Modified files**: `src/lexibrarian/config/schema.py` (add `binary_extensions`), `src/lexibrarian/config/defaults.py` (add default binary extensions), `src/lexibrarian/crawler/__init__.py` (exports)
- **Dependencies**: No new external dependencies — uses only existing project modules and stdlib
- **Phase**: Phase 5 (depends on Phases 1-4 being complete)

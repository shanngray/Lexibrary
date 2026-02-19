# Dependency Checklist & Parallelism Analysis

## Phase Dependency Graph

```
Phase 1: Foundation
├──→ Phase 2: Token Counting        (needs config schema)
├──→ Phase 3: .aindex Format        (needs config schema)
├──→ Phase 4: LLM Integration       (needs config schema)
│
│    [Phases 2, 3, 4 can run IN PARALLEL — they are independent of each other]
│
└──→ Phase 5: Crawler Engine        (needs ALL of 1, 2, 3, 4)
     │
     └──→ Phase 6: CLI Commands     (needs 1, 5; daemon cmd needs 7)
          │
          └──→ Phase 7: Daemon      (needs 1, 5, 6)
               │
               └──→ Phase 8: Polish (needs ALL of 1-7)
```

## Dependency Matrix

| Phase | Depends on | Provides to | Can parallel with |
|-------|-----------|-------------|-------------------|
| **1. Foundation** | — | 2, 3, 4, 5, 6, 7, 8 | Nothing (must be first) |
| **2. Token Counting** | 1 | 5 | **3, 4** |
| **3. .aindex Format** | 1 | 5 | **2, 4** |
| **4. LLM Integration** | 1 | 5 | **2, 3** |
| **5. Crawler Engine** | 1, 2, 3, 4 | 6, 7 | Nothing (convergence point) |
| **6. CLI Commands** | 1, 5 | 7 | Nothing |
| **7. Daemon** | 1, 5, 6 | 8 | Nothing |
| **8. Polish** | 1-7 | — | Nothing (must be last) |

## Optimal Execution Order

```
Time ──────────────────────────────────────────────────→

│ Phase 1 │ Phase 2 ─┐
│         │ Phase 3 ─┼──→ Phase 5 ──→ Phase 6 ──→ Phase 7 ──→ Phase 8
│         │ Phase 4 ─┘
│         │          │
│         │ PARALLEL │
```

### Sequential path (critical path):
**1 → {2,3,4} → 5 → 6 → 7 → 8**

The critical path length is **6 steps** (counting the parallel group as 1).
The longest parallel branch is Phase 4 (BAML setup is the most complex of 2/3/4).

---

## Detailed Dependencies Per Phase

### Phase 1: Foundation
**Depends on:** Nothing
**Produces:**
- `pyproject.toml` with all dependencies declared → needed by everything
- `config/schema.py` (Pydantic models) → consumed by Phase 2 (`TokenizerConfig`), Phase 4 (`LLMConfig`), Phase 5 (`CrawlConfig`, `IgnoreConfig`)
- `config/loader.py` → consumed by Phase 5, 6
- `ignore/matcher.py` (`IgnoreMatcher`) → consumed by Phase 5, 7
- `utils/hashing.py` (`hash_file`) → consumed by Phase 5
- `utils/paths.py` (`find_project_root`) → consumed by Phase 6
- `utils/logging.py` (`setup_logging`) → consumed by Phase 6, 7
- `cli.py` (skeleton) → replaced in Phase 6
- `__init__.py`, `__main__.py` → needed by everything

### Phase 2: Token Counting
**Depends on:**
- `config/schema.py` → `TokenizerConfig` model (from Phase 1)
**Produces:**
- `tokenizer/base.py` → `TokenCounter` Protocol → consumed by Phase 5 engine
- `tokenizer/factory.py` → `create_tokenizer()` → consumed by Phase 5, 6

### Phase 3: .aindex Format
**Depends on:**
- `config/schema.py` → `OutputConfig` model (from Phase 1)
**Produces:**
- `indexer/__init__.py` → `IandexData`, `FileEntry`, `DirEntry` dataclasses → consumed by Phase 5 engine
- `indexer/generator.py` → `generate_iandex()` → consumed by Phase 5 engine
- `indexer/writer.py` → `write_iandex()` → consumed by Phase 5 engine
- `indexer/parser.py` → `parse_iandex()`, `get_cached_file_entries()` → consumed by Phase 5 engine

### Phase 4: LLM Integration
**Depends on:**
- `config/schema.py` → `LLMConfig` model (from Phase 1)
**Produces:**
- `baml_src/*.baml` → BAML prompt definitions
- `baml_client/` → generated Python client → consumed by Phase 5 engine via `llm/service.py`
- `llm/service.py` → `LLMService` → consumed by Phase 5 engine
- `llm/factory.py` → `create_llm_service()` → consumed by Phase 5, 6
- `llm/rate_limiter.py` → `RateLimiter` → consumed by `LLMService`
- `utils/languages.py` → `detect_language()` → consumed by Phase 5 engine

### Phase 5: Crawler Engine
**Depends on:**
- Phase 1: `config/*`, `ignore/matcher.py`, `utils/hashing.py`
- Phase 2: `tokenizer/base.py`, `tokenizer/factory.py`
- Phase 3: `indexer/*` (all: dataclasses, generator, writer, parser)
- Phase 4: `llm/service.py`, `llm/factory.py`, `utils/languages.py`
**Produces:**
- `crawler/engine.py` → `full_crawl()`, `CrawlStats` → consumed by Phase 6, 7
- `crawler/discovery.py` → `discover_directories_bottom_up()` → consumed by engine
- `crawler/change_detector.py` → `ChangeDetector` → consumed by Phase 6, 7
- `crawler/file_reader.py` → `read_file_for_indexing()` → consumed by engine

### Phase 6: CLI Commands
**Depends on:**
- Phase 1: `cli.py` skeleton, `config/loader.py`, `config/defaults.py`, `utils/logging.py`, `utils/paths.py`
- Phase 5: `crawler/engine.py` (for `crawl` command), `crawler/change_detector.py` (for `status` command)
- Phase 7: `daemon/service.py` (for `daemon` command — can stub initially)
**Produces:**
- Full `cli.py` → consumed by users and Phase 7 (daemon command entry point)

### Phase 7: Daemon
**Depends on:**
- Phase 1: `config/*`, `ignore/matcher.py`, `utils/logging.py`
- Phase 5: `crawler/engine.py` (for re-indexing), `crawler/change_detector.py`
- Phase 6: `cli.py` (daemon command wired up)
**Produces:**
- `daemon/service.py` → `DaemonService` → consumed by CLI daemon command
- `daemon/watcher.py`, `daemon/debouncer.py`, `daemon/scheduler.py` → consumed by `DaemonService`

### Phase 8: Polish
**Depends on:** Everything (Phases 1-7)
**Produces:** Hardened, tested, documented release

---

## Parallelism Opportunities

### Maximum parallelism: 3 streams after Phase 1

After Phase 1 completes, three independent workstreams can proceed simultaneously:

| Stream A | Stream B | Stream C |
|----------|----------|----------|
| Phase 2: Token Counting | Phase 3: .aindex Format | Phase 4: LLM Integration |
| ~1 day | ~1 day | ~2-3 days |

**Stream C (Phase 4)** is the longest parallel branch and determines when Phase 5 can start.

### No parallelism after the convergence point

Phases 5, 6, 7, and 8 are sequential. Each depends on the previous.

### Partial parallelism within Phase 6

The `daemon` CLI command in Phase 6 depends on Phase 7. Two options:
1. **Stub it:** Add a placeholder "not yet implemented" for the daemon command in Phase 6, then replace it in Phase 7. (This is the approach in the plan.)
2. **Swap 6 and 7:** Build daemon first, then CLI. But this loses the ability to test other commands early.

Option 1 (stub) is recommended.

---

## Implementation Schedule Summary

| Step | Phase(s) | Parallel? | Cumulative |
|------|----------|-----------|------------|
| 1 | Phase 1: Foundation | No | Phase 1 done |
| 2 | Phases 2 + 3 + 4 | **Yes (3-way parallel)** | Phases 1-4 done |
| 3 | Phase 5: Crawler Engine | No | Phases 1-5 done |
| 4 | Phase 6: CLI Commands | No | Phases 1-6 done |
| 5 | Phase 7: Daemon | No | Phases 1-7 done |
| 6 | Phase 8: Polish | No | All done |

---

## Risk Notes

1. **Phase 4 (BAML) is the riskiest parallel branch.** BAML's `baml-py` version and client registry API may have changed. Budget extra time for debugging the code generation and runtime client switching.

2. **Phase 5 is the integration bottleneck.** It consumes everything from Phases 1-4. Any interface mismatches will surface here. Keep interfaces clean and well-typed to minimize integration pain.

3. **Phase 7 (Daemon) is hardest to test.** Threading, timing, and file system events are inherently flaky in tests. Keep test intervals very short and use mocks aggressively.

4. **Phase 8 may reveal issues in earlier phases.** Budget time for going back and fixing bugs found during end-to-end testing.

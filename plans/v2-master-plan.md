# Lexibrarian v2 — Master Implementation Plan

**Reference:** `lexibrary-overview.md` (the authoritative design document)
**Previous plans:** `plans/archive/v1/` (original aindex-only approach)

---

## Strategic Decision: Restructure, Not Scrap

The v1 codebase built a solid foundation of reusable infrastructure. The new vision is substantially richer — design files, wikilinks, concepts, guardrails, START_HERE.md — but the core plumbing survives.

### Keep As-Is

| Module | Reason |
|--------|--------|
| `utils/hashing.py` | SHA-256 hashing directly reusable; two-tier hashing extends it |
| `ignore/` | gitignore + pathspec matching is unchanged; extended in Phase 4 to load `.lexignore` |
| `tokenizer/` | Token counting still needed for budget validation |
| `llm/rate_limiter.py` | Token-bucket logic is provider-agnostic |
| `daemon/watcher.py`, `debouncer.py`, `scheduler.py` | Watchdog infrastructure is correct; rewire triggers only |

### Rewrite / Redesign

| Module | What Changes |
|--------|--------------|
| `cli.py` | Entirely new command surface (`lookup`, `index`, `concepts`, `guardrails`, `update`, `validate`, `setup`, `describe`) |
| `config/schema.py` | Two-tier YAML config (`~/.config/` global + `.lexibrary/config.yaml` project) |
| `config/loader.py` | Walk up to find `.lexibrary/` instead of `lexibrary.toml` |
| `crawler/engine.py` | Now orchestrates design files + .aindex, not just .aindex |
| `crawler/change_detector.py` | Add interface hash tier alongside content hash |
| `indexer/generator.py` | Generate design files + .aindex (two separate artifact types) |
| `baml_src/` | New Archivist prompt; old summarise prompts retired |
| `llm/factory.py`, `llm/service.py` | Wire to new BAML functions |

### New Modules

| Module | Purpose |
|--------|---------|
| `src/lexibrarian/ast_parser/` | Tree-sitter multi-language AST + interface extraction |
| `src/lexibrarian/artifacts/` | Pydantic models for design files, .aindex, concepts, guardrails |
| `src/lexibrarian/archivist/` | Orchestrate AST → skeleton → LLM → design file pipeline |
| `src/lexibrarian/knowledge_graph/` | Wikilink parsing, resolution, concept file management |
| `src/lexibrarian/guardrails/` | Guardrail thread CRUD + search |
| `src/lexibrarian/init/` | Project init + agent environment rule generation |
| `src/lexibrarian/validator/` | Consistency checks (links, token bounds, bidirectional deps) |

---

## New `.lexibrary/` Output Structure

```
project-root/
  .lexignore             # Lexibrarian-specific ignore patterns (gitignore format)
  .lexibrary/
    config.yaml          # project config (version controlled)
    START_HERE.md        # bootloader — agent entry point (< 2KB)
    HANDOFF.md           # session relay — agent-to-agent post-it (< 100 tokens)
    concepts/            # concept files (cross-cutting knowledge)
      Authentication.md
      MoneyHandling.md
    guardrails/          # guardrail threads (recorded mistakes + fixes)
      GR-001-timezone-naive-datetimes.md
    src/                 # design file mirror tree (1:1 within scope_root)
      auth/
        .aindex
        login.py.md      # design file with YAML frontmatter + markdown body + metadata footer
      api/
        .aindex
        user_controller.py.md
```

Config lives at `.lexibrary/config.yaml` (project) and `~/.config/lexibrarian/config.yaml` (global).
Project root is found by walking upward from CWD to locate `.lexibrary/`.

### Ignore System

Three-layer ignore: `.gitignore` + `.lexignore` + `config.ignore.additional_patterns`. A `.lexignore` file at the project root follows gitignore format and specifies files that exist in git but shouldn't get design files (generated code, vendored deps, data files).

### Scope Root

`scope_root` in config (default: `.`, project root) controls which files get design files. Files outside `scope_root` appear in `.aindex` directory listings but don't get design files.

---

## Phase Overview

| Phase | Name | Produces | Key Dependency |
|-------|------|----------|----------------|
| 1 | Foundation Reset | CLI skeleton, config system, project structure | — |
| 2 | Directory Indexes | `.aindex` files in `.lexibrary/` mirror tree | Phase 1 |
| 3 | AST Parser | Interface skeletons, two-tier hashing | Phase 1 |
| 4 | Archivist | Design files, START_HERE.md, `lexi update` / `lexi lookup` | Phase 3 |
| 5 | Knowledge Graph | Concept files, wikilink resolution | Phase 4 |
| 6 | Guardrail Forum | Guardrail threads, `lexi guardrail new` / `lexi guardrails` | Phase 4 |
| 7 | Validation & Search | `lexi validate`, `lexi status`, `lexi search` | Phases 4, 5, 6 |
| 8 | Agent Setup | `lexi setup`, env rules for Claude/Cursor/Codex | Phase 7 |
| 9 | Daemon & CI | Auto-update on file change, git hooks | Phase 4 |
| 10 | Query Index | SQLite optimisation (optional) | Phase 7 |

**Critical path:** 1 → 3 → 4 → 7 → 8

**Parallelisable pairs:**
- Phase 2 (.aindex) can run alongside Phase 3 (AST)
- Phase 5 (Knowledge Graph) and Phase 6 (Guardrails) can run in parallel once Phase 4 is complete

---

## Phase 1 — Foundation Reset

**Goal:** A working `lexi` binary with the new command surface, new config system, and the `.lexibrary/` directory structure. Nothing generates content yet — stubs return "not implemented."

### What Phase 1 Must Settle

Before writing any further phase, the foundation establishes the decisions everything else builds on:

1. **Config schema** — two-tier YAML, Pydantic 2 models, sensible defaults
2. **Artifact data models** — Pydantic types for each artifact (design file, .aindex, concept, guardrail). These are the shared vocabulary all later phases write and read.
3. **Root resolution** — walk upward from CWD to find `.lexibrary/`; graceful error if not found
4. **Project init** — `lexi init` creates the correct directory skeleton
5. **CLI skeleton** — all commands registered with proper help text; non-implemented commands return a clear message

### Reuse Assessment in Phase 1

- **Keep `ignore/`** entirely; wire it to new config path
- **Keep `tokenizer/`** entirely; it's called later for token budget checks
- **Keep `utils/hashing.py`** entirely
- **Retire `indexer/`** temporarily — rewrite it per-phase as artifact formats stabilise
- **Retire old `config/schema.py`** — new schema is structurally different

### What to Watch Out For

- The old root-finding logic looks for `lexibrary.toml`; update it to look for `.lexibrary/`
- Config format changes from TOML → YAML; existing `pyproject.toml` tooling is unaffected
- `pathspec` pattern name stays `"gitignore"` (not `"gitwildmatch"`) — existing `ignore/` code is correct
- `from __future__ import annotations` in every module — enforce from the start

---

## Phase 2 — Directory Indexes (`.aindex`)

**Goal:** `lexi index <directory>` produces `.aindex` files inside the `.lexibrary/` mirror tree.

This is the closest phase to existing v1 behaviour but output location and content format evolve:
- Files land in `.lexibrary/<mirrored-path>/.aindex`, not in the source tree
- Format gains a **Local Conventions** section
- Child Map table format is the same as v1

### Key Dependency

Needs Phase 1's artifact data models and config system.

### What to Watch Out For

- Mirror path construction: `src/auth/` → `.lexibrary/src/auth/.aindex`
- Local Conventions inheritance: when generating, collect parent `.aindex` Local Conventions up the tree and make them available (agents may not traverse top-down)
- `.aindex` files themselves must appear in the ignore list so they don't get indexed

---

## Phase 3 — AST Parser & Two-Tier Hashing

**Goal:** Given a source file, produce a structured interface skeleton (function signatures, class names, public API) and compute both a content hash and an interface hash.

### New Dependency

**Tree-sitter** (`tree-sitter>=0.21.0`, plus language grammars). This is the only significant new dep not in v1. Start with Python + TypeScript; expand per demand.

### Two-Tier Hashing

Extends `utils/hashing.py`:
- **Content hash** (SHA-256 of full file) — "has anything changed?"
- **Interface hash** (SHA-256 of extracted public signatures) — "has the public API changed?"

Interface hash prevents expensive LLM regeneration when only internal implementation details changed.

### What to Watch Out For

- Tree-sitter grammars are installed separately from the Python binding; the init sequence needs to handle missing grammars gracefully
- Files with unrecognised extensions fall back to content-only (no interface hash)
- The interface skeleton should be deterministic (same input → same hash) — avoid including line numbers or comments in the hashed representation

---

## Phase 4 — Archivist: LLM-Powered Design Files

**Goal:** `lexi update [<path>]` generates or refreshes design files as a **fallback** when agents haven't updated them directly. `lexi lookup <file>` returns the design file. START_HERE.md generation. `lexi describe` for directory descriptions.

This is the core value proposition of Lexibrarian.

### Agent-First Authoring Model

Agents writing code are the best authors of design files (they have full context). The Archivist LLM is the safety net for files agents missed. `lexi update` detects whether an agent already updated a design file and skips LLM regeneration if so.

### Design File Format

Design files have three sections:
- **YAML frontmatter** (agent-editable): `description` (single sentence, propagates to `.aindex`), `updated_by` (archivist or agent)
- **Markdown body** (agent-editable): Interface Contract, Dependencies, Dependents, Tests, Complexity Warning, Wikilinks, Tags, Guardrails
- **HTML comment footer** (machine-managed): source_hash, interface_hash, design_hash, generated, generator

The `design_hash` field (hash of frontmatter + body, excluding footer) enables detecting agent edits without comparing full file content.

### Pipeline

```
Source file
  ↓  Phase 3: AST parser
Interface skeleton + content hash + interface hash
  ↓  Compare against existing design file footer
Changed?
  ├─ No → skip (up to date)
  ├─ Agent already updated design file → refresh footer hashes only (no LLM)
  ├─ Non-code file (no interface) → full Archivist LLM generation (CONTENT_CHANGED)
  ├─ Interface unchanged → lightweight LLM description update (CONTENT_ONLY)
  └─ Interface changed → full Archivist LLM generation (INTERFACE_CHANGED)
        ↓  BAML Archivist prompt
        ↓  LLM fills: summary, intent, constraints, edge cases, wikilinks, tags
        ↓  YAML frontmatter + markdown body + metadata footer
Design file written to .lexibrary/<path>.md
  ↓  Refresh parent .aindex Child Map entry with frontmatter description
```

### `.aindex` Integration

- File descriptions in `.aindex` Child Map are pulled from design file YAML frontmatter `description` field (with structural fallback when no design file exists)
- Directory descriptions (`.aindex` billboard) are written once and not auto-updated; `lexi describe <dir> "..."` command available for manual updates
- `lexi update` on a single file also refreshes the parent directory's `.aindex` entry

### `.lexignore` and Scope Root

- New `.lexignore` file (gitignore format) layered on top of `.gitignore` + config patterns
- `scope_root` config (default: project root) limits which files get design files; files outside scope still appear in `.aindex`

### BAML Changes

Retire `SummarizeFile`, `SummarizeFilesBatch`, `SummarizeDirectory`. Add:
- `ArchivistGenerateDesignFile(source_path, source_content, skeleton?, language?, existing?) → DesignFileOutput`
- `ArchivistGenerateStartHere(project_name, directory_tree, aindex_summaries, existing?) → StartHereOutput`

Config-driven LLM client routing via BAML `ClientRegistry` (spike needed to verify API).

### Staleness Metadata

Every generated artifact gets a footer:

```markdown
<!-- lexibrarian:meta
source: src/services/auth_service.py
source_hash: a3f2b8c1
interface_hash: 7e2d4f90
design_hash: c4d5e6f7
generated: 2026-01-15T10:30:00Z
generator: lexibrarian v0.2.0
-->
```

### What to Watch Out For

- **Agent-first model requires Phase 8 (agent environment rules) to be effective.** Before Phase 8, `lexi update` is the primary path. Phase 8 rules must be explicit about the workflow order: agents update design files *first* (directly), then `lexi update` runs as a safety net. If rules say "run `lexi update` after making changes" without emphasising direct design file editing, agents will reach for `lexi update` as the primary path — defeating the agent-first model and incurring unnecessary LLM costs.
- Design file generation is async and LLM-expensive; rate limiter from v1 applies
- Token budget validation runs after generation: flag if design file exceeds config target
- `lexi lookup` must handle the case where no design file exists yet (offer to generate)
- START_HERE.md is a special case: generated from project topology, not a single file
- `.aindex` refresh on single file update requires read-modify-write of parent `.aindex`
- Footer-less design files (agent-authored from scratch before Archivist runs) must be treated as `AGENT_UPDATED`, not `NEW_FILE` — otherwise agent work gets overwritten by LLM regeneration (D-026)
- First-run `lexi update` on a large project is slow (sequential LLM calls, 10–30 min for 300+ files). Set expectations via progress bar and documentation. Design async architecture for future concurrency from the start (D-025)

---

## Phase 5 — Concepts Wiki

**Goal:** `lexi concepts [<topic>]` lists or searches concept files. Wikilinks in design files resolve to concept files. `[[ConceptName]]` in any artifact can be followed.

### Wikilink Resolution

A wikilink `[[Authentication]]` resolves to `.lexibrary/concepts/Authentication.md`. The resolver must:
1. Check `concepts/` directory for an exact match
2. Fall back to fuzzy match (case-insensitive, normalised)
3. Return an unresolved link error if not found (surfaced by `lexi validate`)

### What to Watch Out For

- Wikilinks also appear in guardrail threads (Phase 6) — build the resolver as a shared utility
- Concept files themselves contain wikilinks to other concepts; cycle detection is needed
- Tags in concept files feed the `lexi search --tag` command (Phase 7) — design the tag storage format here

---

## Phase 6 — Guardrail Forum

**Goal:** `lexi guardrail new` creates a thread. `lexi guardrails [--scope <path>] [--concept <name>]` searches threads. Design files gain a Guardrails cross-reference section.

### Thread Numbering

Auto-assign `GR-NNN` IDs by scanning existing threads at creation time. Pad to 3 digits.

### Append-Only Enforcement

Guardrail threads are append-only at the application level. The CLI never offers an edit command. This is a soft constraint (users can edit files directly) — documented clearly in the thread format, not enforced by a lock mechanism.

### What to Watch Out For

- Thread search needs to scan all guardrail files for scope/concept matches. Phase 7's query index (if adopted) will accelerate this — for now, accept O(n) scan.
- `lexi validate` (Phase 7) must flag guardrails referencing source files that no longer exist

---

## Phase 7 — Validation & Search

**Goal:** `lexi validate` runs all consistency checks. `lexi status` shows library health. `lexi search --tag <t>` finds artifacts by tag.

### Validation Checks (in order)

1. **Link resolution** — all `[[wikilinks]]` resolve to existing concept files or guardrail threads
2. **Token bounds** — all generated artifacts within their configured size targets
3. **Bidirectional consistency** — if A lists B as dependency, B's dependents include A
4. **File existence** — all referenced source files and test paths still exist
5. **Hash freshness** — no artifacts have stale `source_hash` values (not yet updated)
6. **Guardrail references** — guardrail threads only reference existing files/concepts

### Status Output

`lexi status` shows:
- Total artifacts: N design files, M .aindex files, K concept files, J guardrail threads
- Stale artifacts: X files need updating
- Unresolved links: Y broken wikilinks
- Token budget violations: Z oversized artifacts
- Last update: timestamp

### What to Watch Out For

- Validation is the first command that touches every artifact — it will surface design choices made in earlier phases. Plan for iteration.
- `lexi search --tag` with Option A (files only) means scanning all markdown frontmatter. Acceptable for < 500 files; flag as slow if it approaches that.

---

## Phase 8 — Agent Environment Auto-Setup

**Goal:** `lexi setup <env> [--update]` writes agent-specific configuration files that tell the agent how to use the library.

### Supported Environments (MVP)

| Environment | Files Written |
|-------------|--------------|
| `claude` | `CLAUDE.md`, `.claude/commands/lexi-*.md` |
| `cursor` | `.cursor/rules/lexibrarian.mdc`, `.cursor/skills/lexi.md` |
| `codex` | `AGENTS.md` section |

### Rule Content

The rules must instruct the agent to:
- Read `START_HERE.md` + `HANDOFF.md` at session start
- Run `lexi lookup <file>` before editing a file
- Run `lexi concepts <topic>` before architectural decisions
- Run `lexi guardrail new` after hitting a novel error
- Run `lexi update` after making changes
- Rewrite `HANDOFF.md` before session end

### What to Watch Out For

- `--update` must not clobber user customisations added after initial setup. Detect user-added sections and preserve them (comment-delimited regions).
- Environment detection: `lexi init [--agent <env>]` can auto-detect or prompt; `lexi setup` is the explicit override

---

## Phase 9 — Daemon & CI Integration

**Goal:** `lexi daemon` watches for file changes and runs `lexi update` incrementally. Git hook and CI step generation.

### Reuse from v1

The `daemon/watcher.py`, `debouncer.py`, and `scheduler.py` modules from v1 are reused. The only change: instead of triggering a full crawl, trigger `lexi update <changed-file>` for each debounced event.

### New Triggers

| Trigger | Config | Notes |
|---------|--------|-------|
| Daemon | `trigger_mode: daemon` | Default; watchdog + debounce |
| CLI | `lexi update` | Manual; always available |
| Git hook | `lexi setup --hooks` | Writes `.git/hooks/post-commit` |
| CI | `lexi update && lexi validate` | Document as pipeline step |

### What to Watch Out For

- The daemon must not trigger on `.lexibrary/` changes (avoid infinite loops)
- PID file management from v1 daemon applies unchanged

---

## Phase 10 — Query Index (Future / Optional)

**Start with Option A (files-only).** Layer SQLite underneath if performance becomes an issue.

Design principle: all CLI commands keep the same interface regardless of backend. The query backend is a private implementation detail.

### Trigger for Adopting Option B

Empirical: if `lexi validate` or `lexi search` takes > 2 seconds on a real project, add the index.

---

## New Dependencies to Add

| Package | Phase | Reason |
|---------|-------|--------|
| `tree-sitter>=0.21.0,<1.0.0` | 3 | AST parsing |
| `tree-sitter-python>=0.21.0` | 3 | Python grammar |
| `tree-sitter-typescript>=0.21.0` | 3 | TypeScript/JS grammar |
| `PyYAML>=6.0.0,<7.0.0` | 1 | Config format (replaces TOML) |

**Retire when safe:**
- `tiktoken` (if token budget validation moves to approximate counting)
- `anthropic` direct SDK (kept for tokenizer backend; BAML handles LLM calls)

---

## Test Strategy

Each phase ships with tests before moving to the next:
- Unit tests: pure functions (hashing, wikilink parsing, schema validation)
- Integration tests: `tmp_path`-based fixtures simulating real project trees
- Snapshot tests: generated artifact content checked against expected output
- CLI tests: `typer.testing.CliRunner` for command surface

The `tests/fixtures/sample_project/` from v1 should be extended to include a multi-language sample project that exercises Tree-sitter grammars.

---

## Open Questions (Decide in Phase 1)

1. **Config file name:** `.lexibrary/config.yaml` (YAML) — confirm, since v1 used `lexibrary.toml` (TOML)
2. **Mapping strategy config:** Confirm glob-pattern approach in config for 1:1 / grouped / abridged / skipped
3. **Tree-sitter grammar installation:** Bundled in the package or installed on demand? (Leaning: on demand, with a clear error message)
4. **baml-py version:** Current pin is `0.218.0`; check if it needs to bump for new prompt patterns
5. **`lexi init` vs `lexi setup`:** `init` creates `.lexibrary/`; `setup` configures agent environment — keep distinct

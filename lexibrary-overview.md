# Lexibrarian: Architecture Overview

A library of a codebase that agents can use to quickly understand it and navigate it. Written by agents, for agents.

The fundamental constraint of AI coding today is **context window efficiency vs. knowledge retrieval**. We treat the codebase not as raw text but as a **queryable semantic database** — moving from "reading the whole book" to "checking the index."

---

## Principles

- **Agent-first** — every design decision optimises for machine consumption. Human readability is a bonus, not a goal.
- **CLI is the product surface** — all interaction happens through a single `lexi` command that agents invoke directly. No GUI, no web UI.
- **Installed once, initialised per-project** — `pipx install lexibrarian` (or `uv tool install`) puts `lexi` on PATH globally; `lexi init` sets up each project individually. Lexibrarian is a dev tool like a linter, never a project dependency.
- **Zero infrastructure** — no external services, no servers, no Docker. Source of truth is always files in the repo: markdown, YAML, wikilinks. A local file-based query index may accelerate lookups at scale (see §7a — two options under consideration).
- **Context is tiered** — cheap overview always loaded, detail loaded on demand, heavy context loaded only when explicitly needed.

---

## 1. The Bootloader: `START_HERE.md`

The single entry point for any agent entering the project.
**Size target:** < 2KB.

Contains no code. It is a high-level routing protocol:

- **Project Topology** — Mermaid diagram (preferred — structured and agent-parseable) or ASCII tree of the repository structure and high-level architecture. Format is configurable.
- **Project Ontology** — key domain terms and their definitions (ensures agents use correct search terms and understand business semantics).
- **Navigation by Intent** — task-oriented routing table. Agents think in tasks, not directories: *"I need to change how users authenticate"* → `[[Authentication]]`. *"I need to add an API endpoint"* → `.lexibrary/backend/api/.aindex`. Maps common agent goals directly to entry points in the library.
- **Navigation Protocol** — instructions on how to use the library (e.g., "always check the `.aindex` of a directory before reading its files").
- **Convention Index** — a compact list of convention/decision names with one-line descriptions. When an agent needs detail, it follows the wikilink. This keeps the bootloader tiny but makes the agent aware of what exists.
**Note:** `START_HERE.md` deliberately excludes work-in-progress state. Current focus is tracked in a separate `HANDOFF.md` file (see below).

### `HANDOFF.md` — the session relay

A separate, standalone file that acts as a **post-it note passed from one agent session to the next**. Lives at `.lexibrary/HANDOFF.md`.

**Why a separate file, not a section in `START_HERE.md`?**

- "Active Context" sections inside larger documents suffer from accumulation rot — agents append but never prune, and the section drifts from "current focus" to "history of everything."
- A standalone file is a discrete artifact with its own lifecycle. Agents can be told "always read `HANDOFF.md` first" and "always rewrite `HANDOFF.md` before handing off." Clear, atomic responsibility.
- It's cheap to nuke and rewrite. You'd never nuke `START_HERE.md`, but `HANDOFF.md` should be overwritten entirely on every handoff.

**Format (strict, ~5–8 lines max):**

```markdown
# Handoff

**Task:** [one line — what is being done]
**Status:** [one line — where things stand right now]
**Next step:** [one line — what the next agent should do first]
**Key files:** [2–3 file paths most relevant to the work]
**Watch out:** [one line — any gotcha the next agent needs to know]
```

**Key rules:**

1. **Overwrite, never append** — each agent session writes a fresh `HANDOFF.md`. No history accumulates. If history matters, it belongs in a guardrail thread or a commit message.
2. **Mandatory read/write** — agent environment rules (Section 8) enforce: read `HANDOFF.md` at session start, rewrite it before session end.
3. **Token-budgeted** — `lexi validate` flags it if it exceeds its target size, same as any other artifact.

---

## 2. Design Files (Shadow Files)

**Purpose:** Explain the *intent* of code, not just the syntax.

### Hybrid mirroring (configurable)

The default is a **1-to-1 mirror structure** — deterministic and unambiguous. If an agent is looking at `src/auth/login.py`, it can algorithmically predict the design file is at `.lexibrary/src/auth/login.py.md`. No search needed.

However, not every file warrants a full design file. Lexibrarian supports configurable controls for how files are mapped:

| Strategy | When to use | Example |
|----------|------------|---------|
| **1:1 per file** | Core domain models, services, controllers | `auth_service.py` → `auth_service.py.md` |
| **Grouped per directory** | Utility/helper files, config files | `utils/*.py` → `utils/_group.md` |
| **Abridged** | Simple files with minimal logic | Shortened template, interface-only |
| **Skipped** | Generated files, lockfiles, build output | Migrations, `package-lock.json` |
| **Reference from source** | Test files | Tests documented in their source file's design file |

These strategies are configured in `.lexibrary/config.yaml` via glob patterns. The default is 1:1 for everything; users tune from there.

### Content of a design file

- **Summary** — one sentence on what this module does.
- **Interface Contract** — inputs (arguments) and outputs (return types / side effects). Crucial for preventing hallucinations.
- **Dependencies** — what external services or local modules this file touches.
- **Dependents** — what depends on this file (reverse links).
- **Tests** — reference to where tests for this file live.
- **Complexity Warning** — flagged note if the file contains legacy code or dragons.
- **Wikilinks** — `[[ConceptName]]` tags linking to relevant concepts, conventions, or decisions.
- **Tags** — lightweight labels for search and filtering (e.g., `auth`, `security`, `jwt`). Complements wikilinks — tags enable `lexi search --tag auth` without requiring graph traversal.
- **Purpose / Future Direction** — why this exists and where it's headed (future direction could also be tracked as issues via Beads).

### Auto-generation

Use AST parsing (Tree-sitter) to auto-generate the skeleton of design files (function signatures, class names, interface contracts). An LLM fills in descriptions only when the code actually changes, as determined by change detection.

### Dependents: reverse-index discovery

The "Dependents" field (what uses this file) requires a project-wide reverse-dependency index. This is built during `lexi update` as a two-pass process:

1. **Forward pass** — collect all dependencies from every file's AST imports.
2. **Reverse pass** — invert the dependency map to produce dependents for each file.

The reverse index is cached and updated incrementally when files change. Without this explicit mechanism, the dependents field will always be stale or incomplete.

---

## 3. Directory Indexes: Recursive Routing

Every directory in the library contains an `.aindex` file enabling agents to traverse the codebase tree without loading leaf nodes.

- **Billboard** — explains the purpose of the directory (e.g., "All React components related to User Settings").
- **Child Map** — a 3-column table (`Name`, `Type`, `Description`) listing every file and subdirectory. Files listed before directories, each group sorted alphabetically. No token count column — token budgets are validated at the artifact level, not per-entry.
- **Local Conventions** *(optional)* — scoped conventions and contextual warnings that apply within this directory. Things an agent should know *given where it's working right now*, but that aren't universally true across the project.

### Local Conventions: conditional conventions

Many important guidelines are scoped, not universal: "use `Decimal` for money in this module," "migration from sync to async in progress here," "tests require a specific fixture." These don't belong in `START_HERE.md` (too specific) or in individual design files (they apply to a scope, not a single file).

The `.aindex` is the right home because agents already read it when entering a directory. Placing scoped conventions there means agents see them at exactly the right time — when they enter the scope.

```markdown
## Local Conventions
- All monetary values use `Decimal`, never `float` — see [[MoneyHandling]]
- Tests in this directory require the `payments` fixture — `conftest.py` has details
- Migration in progress from sync to async — check [[AsyncMigration]] before adding new endpoints
```

**Inheritance:** Local Conventions sections inherit downward. If `.lexibrary/src/.aindex` says "use UTC everywhere" and `.lexibrary/src/payments/.aindex` says "use Decimal for money," an agent in `src/payments/` sees both — it sees its current `.aindex` plus any parent `.aindex` Local Conventions sections it traversed to get there. This matches the existing navigation model. NOTE: If the agent has jumped to a subdirectory rather than traversing the directory tree, it will only see the Local Conventions for the current directory, not the parent directories.

**Population:** Local Conventions are initially empty. They are intended to be populated by agents (via a future CLI command or guardrail-like workflow) or by humans editing `.aindex` files directly. **Open question:** How should `lexi update` preserve agent/human-authored Local Conventions when regenerating the `.aindex` file? The convention content must survive regeneration — either by parsing and re-injecting it, or by treating Local Conventions as a separate section that regeneration never touches.

**Agent workflow:**

1. Reads `.lexibrary/START_HERE.md` → sees `.lexibrary/backend/`
2. Reads `.lexibrary/backend/.aindex` → sees `.lexibrary/backend/api/`
3. Reads `.lexibrary/backend/api/.aindex` → finds `user_controller.py.md`
4. Reads the design file

The agent finds specific logic without ever loading irrelevant frontend code or database migrations.

---

## 4. Knowledge Graph: Wikilinks

**Purpose:** Link disconnected concepts that live in different files, directories, or even repos.

Implementation is **wikilinks in markdown** — no graph database, no infrastructure. `[[Authentication]]` in a design file tells the agent there's a concept file to follow if it needs more context.

### Concept files

A `concepts/` directory containing one file per cross-cutting concept:

```
.lexibrary/concepts/Authentication.md
  - Frontend Login Form → .lexibrary/frontend/components/LoginForm.tsx.md
  - Backend Auth Middleware → .lexibrary/backend/middleware/auth.py.md
  - DB User Table → .lexibrary/db/migrations/users.sql.md
```

Concept files also include **tags** for searchability (e.g., `auth`, `security`, `cross-cutting`) and a **decision log** section for recording key architectural choices related to the concept.

### Why wikilinks over a graph database?

- **Zero infrastructure** — just files and `[[links]]`. Agents already understand wikilinks from training data (Obsidian, Notion, etc.).
- **Agents can follow them** — see `[[Authentication]]`, look up `.lexibrary/concepts/Authentication.md`, done. It's just file navigation.
- **Upgrade path is clear** — if graph queries are ever needed ("what's 2 hops from Authentication?"), build an adjacency list from the wikilinks at index time. The wikilinks *are* the edges.

---

## 5. Handling Abstractions, Conventions, and Design Decisions

The hardest problem. Abstractions don't live in files — they span the codebase. A file-centric library misses them entirely unless we handle them explicitly.

### Tier 1: Concept files (loaded on demand via wikilinks)

The `concepts/` directory entries. When a design file mentions `[[RepositoryPattern]]`, the agent pulls in `concepts/RepositoryPattern.md` which explains the pattern, why it was chosen, the interface contract, and exceptions.

### Tier 2: Convention index (loaded at session start)

A compact list in `START_HERE.md` that names every convention with a one-line description. Cheap to load (< 1KB). Tells the agent *what exists*. When it needs detail, it follows the wikilink.

### Tier 3: Decision records / ADRs (loaded on demand)

For "why did we choose X over Y" questions. These are linked from concept files and are heavy — never loaded by default, only when an agent is about to make a decision in that space.

### Context loading strategy

| Tier | When loaded | Example |
|------|------------|---------|
| Always | Session start | `START_HERE.md` + `HANDOFF.md` (topology, conventions, current task) |
| On directory entry | Agent enters a directory | That directory's `.aindex` (including Local Conventions section) |
| On file touch | Agent reads/edits a file | That file's design file (includes wikilinks) |
| On demand | Agent follows a wikilink | Concept files, decision records |

This keeps base context tiny but makes full knowledge accessible. The agent environment rules (see section 8) tell agents *when* to pull each tier.

### Token budgets (configurable defaults)

Each artifact type has a target token size. These are configurable in `.lexibrary/config.yaml` — the defaults below are starting points to be tuned per project:

| Artifact | Default target | Rationale |
|----------|---------------|-----------|
| `START_HERE.md` | ~500–800 tokens | Must fit in a single context load. If it's bigger, it's doing too much. |
| `HANDOFF.md` | ~50–100 tokens | A post-it note, not a document. 5–8 lines max. Overwritten each session. |
| Design file (1:1) | ~200–400 tokens | Agent should be able to load 3–5 without significant context burn. |
| Design file (abridged) | ~50–100 tokens | Interface-only skeleton for simple files. |
| `.aindex` file | ~100–200 tokens | Routing tables, not documentation. |
| Concept file | ~200–400 tokens | Comparable to a design file. Decision logs may push larger. |
| Guardrail thread | Unbounded (append-only) | Evidence accumulates. Search filters keep retrieval scoped. |

The LLM generation step validates output against these targets. If a design file exceeds its budget, the generator flags the source file as potentially over-scoped — a useful architectural signal.

---

## 6. The Guardrail Forum

Guardrails are a standalone system — a **mini Stack Overflow embedded in the codebase**. Their purpose is to record real issues that previous agents encountered so new agents know what not to try.

### Why a forum, not just a field in design files?

- Issues often span multiple files — a guardrail about timezone handling touches `utils/`, `models/`, `api/`, and `tests/`.
- Guardrails need discussion-like structure: the problem, attempted solutions that failed, the actual fix.
- Agents need to *search* guardrails across the codebase ("has anyone hit a timezone issue before?"), not just see ones scoped to a single file.

### Structure: threads not entries

Each guardrail is a **thread**, structured like a Stack Overflow Q&A:

```
guardrails/
  GR-001-timezone-naive-datetimes.md
  GR-002-circular-import-services.md
  ...
```

**Thread format:**

```markdown
# GR-001: Timezone-naive datetimes cause silent data corruption

**Status:** active
**Scope:** [[DateHandling]], `src/models/event.py`, `src/api/events.py`
**Reported by:** agent-session-abc123
**Date:** 2026-01-15

## Problem
Using `datetime.now()` anywhere in this codebase produces timezone-naive
datetimes that silently corrupt data when compared against the DB (which
stores UTC).

## Failed approaches
- Wrapping individual call sites with `timezone.now()` — missed call sites
  cause intermittent bugs.

## Resolution
All datetime creation must go through `utils/time.py:now()` which enforces
UTC. The linter rule `TZ001` catches bare `datetime.now()` calls.

## Evidence
- Test failure: `tests/test_events.py::test_event_overlap` (fixed in commit abc123)
- Linter rule: `.ruff.toml` rule `TZ001`
```

### Key rules

1. **Append-only** — agents can add threads and add follow-up entries to existing threads. They cannot delete or edit previous entries.
2. **Evidence required** — every thread must cite a specific error, test failure, or observable behaviour. No speculation. If an agent can't cite evidence, the guardrail gets flagged as unverified.
3. **Scoped via wikilinks** — guardrail threads link to concepts and files using `[[wikilinks]]` and file paths. Design files link back with a guardrails section listing relevant thread IDs.
4. **Searchable via CLI** — `lexi guardrails --scope src/auth/` returns all threads touching that path. `lexi guardrails --concept Authentication` returns all threads tagged with that concept.
5. **Prunable** — during re-indexing, guardrails that reference code/patterns that no longer exist get flagged for review. Stale guardrails are worse than no guardrails.

### Cross-linking with design files

Design files include a lightweight guardrails reference section:

```markdown
## Guardrails
- [[GR-001]] Timezone-naive datetimes — use `utils/time.py:now()`
- [[GR-002]] Circular imports — see service layer conventions
```

This keeps design files slim while making the guardrail discoverable at the point of relevance.

---

## 7. Change Detection

**SHA-256 content hashing** is the primary change detection mechanism.

### Why SHA-256 over git diff?

- **Works outside git** — if someone drops Lexibrarian on a non-git project, hashes still work.
- **Catches uncommitted changes** — `git diff` only covers committed changes. SHA-256 on the working tree catches saves that haven't been committed yet, which is the common case when an agent is mid-session.
- **Cheap and deterministic** — hash the file, compare to stored hash, done. No need to keep old copies or compute diffs just to know *whether* something changed.

### Two-tier hashing

| Tier | What's hashed | Triggers |
|------|--------------|----------|
| Content hash | Full file content (SHA-256) | "Has anything changed at all?" — triggers analysis |
| Interface hash | AST public signatures only | "Has the public API changed?" — triggers design file rewrite |

Internal refactors that don't change the public interface get a lighter touch (update the description, leave the interface contract alone). Signature changes trigger a full design file regeneration.

### The update engine

1. **Trigger** — file save detected by daemon (watchdog + debounce) or manual `lexi update` invocation.
2. **Detection** — SHA-256 content hash compared to stored hash. If unchanged, skip.
3. **Analysis** — if content changed, check interface hash:
   - **Interface unchanged** — lightweight description update only.
   - **Interface changed** — full design file regeneration via AST parse + LLM.
4. **Action** — the Archivist (specialised LLM prompt) reads the diff, reads the existing design file, rewrites it. Updates the `.aindex` if files were added/deleted.
5. **Commit** — updated library files committed alongside code changes (or on next commit).

### Update triggers (configurable)

The update engine supports multiple trigger modes, configured in `.lexibrary/config.yaml`:

| Trigger | Mode | When to use |
|---------|------|-------------|
| **Daemon** | watchdog + debounce | During active development — real-time updates as files are saved |
| **CLI** | `lexi update [<path>]` | Manual invocation — on demand or scripted |
| **CI/CD** | Git hook or pipeline step | On commit/PR — validates and regenerates as part of the development workflow |
| **Scheduled** | Periodic full rebuild | Weekly/nightly — catches drift, reconciles the knowledge graph |

Default is daemon + CLI. CI/CD integration is configured per-project. All modes use the same detection and generation pipeline.

### Staleness metadata

Every generated artifact includes a metadata footer for change tracking:

```markdown
<!-- lexibrarian:meta
source: src/services/auth_service.py
source_hash: a3f2b8c1
interface_hash: 7e2d4f90
generated: 2026-01-15T10:30:00Z
generator: lexibrarian v0.1.0
-->
```

A staleness check compares `source_hash` against the current file. If they diverge and no update has run, the artifact is flagged:

```markdown
> ⚠️ This doc may be outdated. Source file changed since last update.
```

### Validation pipeline

Post-generation checks ensure library consistency:

1. **Link resolution** — all `[[wikilinks]]` resolve to existing concept files or guardrail threads.
2. **Token bounds** — generated artifacts are within their configured size targets.
3. **Bidirectional consistency** — if file A lists B as a dependency, B's dependents should include A.
4. **File existence** — all referenced source files and test paths still exist.
5. **Hash freshness** — no artifacts have stale `source_hash` values.

Validation runs automatically after generation and can be invoked standalone via `lexi validate`. Failures are surfaced in `lexi status`.

### Archivist prompt design

The Archivist is the specialised LLM prompt (defined in BAML) that generates and updates design files. Quality guidelines:

- **Describe *why*, not *what*** — the code itself shows what it does. The design file should explain intent, constraints, and non-obvious behaviour.
- **Flag edge cases and dragons** — surprising behaviour is the highest-value content a design file can contain.
- **Respect the token budget** — if a generated doc exceeds its target, flag the source file as potentially over-scoped rather than writing a longer doc.
- **Preserve continuity** — when updating an existing design file, carry forward human-added notes and guardrail references that are still relevant.

---

## 7a. Query Index (Decision Pending)

The markdown/YAML files are the source of truth. But several CLI operations — tag search, guardrail lookup, reverse dependency queries, concept graph traversal — require scanning many files to answer a single question. At scale, this becomes a bottleneck.

Two options are under consideration. Both preserve the "files are canonical" guarantee; they differ in whether a derived index exists.

### Option A: Files only (current design)

All queries scan the filesystem directly. No derived index, no cache.

| Pros | Cons |
|------|------|
| Truly zero infrastructure — nothing to build, rebuild, or invalidate | O(n) disk reads for cross-cutting queries (tags, guardrails, reverse deps) |
| No consistency risk between source files and index | Performance degrades with project size |
| Simpler codebase — no index-building pipeline | Every CLI query re-parses markdown files |

**Best for:** Small-to-medium projects where the file count stays manageable (< ~500 source files).

### Option B: Files + local query index

A derived index file (SQLite or JSON) is built from the markdown files during `lexi update` and queried by the CLI. The index is a cache — always rebuildable from the source files.

```
.lexibrary/
  index.db          # SQLite — gitignored, rebuilt by `lexi update`
```

| Pros | Cons |
|------|------|
| O(1) lookups for tags, reverse deps, concept graph, guardrail scope | Adds a build step (`lexi update` must rebuild the index) |
| Enables richer queries ("what's 2 hops from Authentication?") | Index can drift if `lexi update` isn't run (mitigated by staleness checks) |
| SQLite is stdlib (`sqlite3`), single file, zero external services | Slightly more complex codebase |

**Best for:** Large projects, monorepos, or projects that rely heavily on cross-cutting queries.

### Resolution approach

Start with Option A for MVP. The markdown files and CLI commands are designed so that Option B can be layered underneath without changing any user-facing behaviour — the CLI interface stays the same, only the query backend changes. If performance becomes a concern, add the index as an optimisation.

---

## 8. Agent Environment Auto-Setup

When a user runs `lexi init`, Lexibrarian detects (or is told) the agent environment and writes the appropriate configuration files.

### Supported environments

| Environment | Config location | What gets written |
|-------------|----------------|-------------------|
| **Cursor** | `.cursor/rules/`, `.cursor/skills/` | Rules (`.mdc`), skills (`SKILL.md`), commands |
| **Claude Code** | `CLAUDE.md`, `.claude/commands/`, `.claude/skills/` | Rules, commands, skills |
| **Codex** | `AGENTS.md` or equivalent | Agent instructions |

### What the rules contain

The auto-installed rules tell the agent:

- Always read `.lexibrary/START_HERE.md` and `.lexibrary/HANDOFF.md` at session start.
- Before editing a file, run `lexi lookup <file>` to load its design file.
- Before making architectural decisions, run `lexi concepts <topic>` to check for existing conventions/decisions.
- After encountering an error, run `lexi guardrail new --file <file> --mistake "..." --resolution "..."` to record it.
- After making changes, run `lexi update` to regenerate affected design files.
- Before ending a session, overwrite `.lexibrary/HANDOFF.md` with current task state, status, next step, key files, and any gotchas for the next agent.

### Updatable

`lexi setup <environment> --update` refreshes the rules if Lexibrarian's conventions have evolved, without clobbering user customisations.

---

## 9. CLI Design

The CLI is the product surface. Everything else is plumbing.

### Design principles

- **Query-oriented** — single commands return everything an agent needs for a given scope.
- **Agent-readable by default** — Concise structured text output designed for agent consumption.
- **Minimal round-trips** — agents are token-constrained. One call, scoped output. Don't make agents chain multiple commands for basic lookups.
- **Pipeable** — commands support composition. `lexi lookup` output includes wikilinks that can feed into `lexi concepts`, reducing multi-step lookups to a single piped invocation.
- **Read and write** — agents consume the library *and* contribute back to it (guardrails, design file updates).

### Core commands

```
lexi init [--agent cursor|claude|codex]   Initialise library in current project
lexi setup <env> [--update]               Install/update agent environment rules
lexi lookup <file>                        Return design file for a source file
lexi index <directory> [-r]               Return .aindex for a directory (-r for recursive)
lexi concepts [<topic>]                   List or search concept files
lexi guardrails [--scope <path>] [--concept <name>]
                                          Search guardrail threads
lexi guardrail new --file <f> --mistake "..." --resolution "..."
                                          Record a new guardrail thread
lexi search --tag <t> [--scope <path>]    Search by tags across the library
lexi update [<path>]                      Re-index changed files
lexi validate                             Run consistency checks on library
lexi status                               Show library health / staleness
```

---

## 10. Packaging and Distribution

- **Build system** — hatchling, src layout (`src/lexibrarian/`).
- **Global install** — `pipx install lexibrarian` or `uv tool install lexibrarian`. The `lexi` command goes on PATH.
- **Per-project init** — `lexi init` creates the `.lexibrary/` directory and its structure. Config is version-controlled with the project.
- **Not a project dependency** — Lexibrarian never appears in a project's `requirements.txt` or `pyproject.toml` dependencies. It's a tool, not a library.
- **Project root resolution** — CLI walks up from CWD to find `.lexibrary/`, like git finds `.git/`.
- **Multi-repo awareness** — MVP targets single-repo projects. Multi-repo support is a fast-follow: a root `.lexibrary/config.yaml` references child repos, `START_HERE.md` spans all of them, and the knowledge graph links concepts across repo boundaries. The initial architecture (wikilinks, relative paths, per-project config) is designed to extend to multi-repo without structural changes.

### Ecosystem relationship

Lexibrarian is the knowledge layer in a three-tool stack:

| Tool | Role |
|------|------|
| **OpenSpec** | Change management — specifies *what* is being built and tracks implementation tasks |
| **Beads** | Issue and progress tracking — the source of truth for task state |
| **Lexibrarian** | Codebase knowledge — tells agents *how* the existing code works so they can implement changes correctly |

The typical agent workflow: read `START_HERE.md` to orient → check Beads for the active task → use `lexi lookup` to understand relevant code → implement → run `lexi update` → update `HANDOFF.md`. Lexibrarian does not replace OpenSpec's task specs or Beads' issue tracking; it answers the question those tools leave open: *"what does the existing code actually do?"*

### Two-tier configuration

| Level | Location | What it configures |
|-------|----------|--------------------|
| **Global** | `~/.config/lexibrarian/config.yaml` (XDG) | Default LLM provider, API keys, default agent environment, personal preferences |
| **Project** | `.lexibrary/config.yaml` (project root) | Mapping strategies, token budgets, ignore patterns, trigger modes, project-specific conventions |

Project config overrides global config where they overlap. Global config provides defaults so that `lexi init` in a new project works without manual setup.

### Project directory structure

`lexi init` creates the following structure at the project root:

```
.lexibrary/
  config.yaml          # project config (version controlled)
  START_HERE.md        # bootloader — agent entry point
  HANDOFF.md           # session relay — agent-to-agent post-it note
  concepts/            # concept files (cross-cutting knowledge)
  guardrails/          # guardrail threads (recorded mistakes + fixes)
  src/                 # design file mirror tree
    auth/
      .aindex
      login.py.md
```

The `.lexibrary/` directory co-locates config with artifacts — everything Lexibrarian owns lives in one place. If the query index (§7a Option B) is adopted, `index.db` is added here and gitignored.

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Parsing | Tree-sitter | Robust multi-language AST parsing for structural change detection and interface extraction |
| Config | PyYAML + Pydantic 2 | YAML for human/agent readability; Pydantic validates on load |
| Validation | Pydantic 2 | Config and data model validation |
| Output | `rich.console.Console` | Rich terminal output for human mode |
| Graph | Wikilinks (`[[Link]]`) | Zero-infrastructure, agent-native. Upgrade to adjacency list if graph queries needed later |
| Change detection | SHA-256 (hashlib) | Content + interface hashing |
| Daemon | watchdog + debounce | File system monitoring for auto-updates |
| LLM prompts | BAML | Provider-agnostic prompt definitions |
| CLI | Click or Typer | Agent-friendly command structure |
| Packaging | hatchling | src layout, standard Python packaging |

---

## Open Design Notes

> Items below are recognized as important but don't yet have a settled home in the architecture. They'll be incorporated as the design matures.

### Agent context budget guidance

Different agents have different context budgets. `START_HERE.md` (or the agent environment rules) should include navigation strategies by context size:

- **Small context (4K–8K tokens):** Read `START_HERE.md` → one `.aindex` → one design file. Use the graph sparingly (one concept at a time). Rely heavily on Navigation by Intent.
- **Medium context (32K–128K tokens):** Load `START_HERE.md` + several `.aindex` files + 5–10 design files + 2–3 concept nodes. The sweet spot for this system.
- **Large context (200K+ tokens):** Load `START_HERE.md` + all `.aindex` files for relevant scope + concept nodes. Load design files on demand. The library prevents the "loaded everything but now confused" failure mode.

### Non-code artifacts

Database schemas, API specs (OpenAPI), infrastructure definitions (Terraform), CI configs — these exist in most projects and agents need to understand them. They should get design files with adapted templates. The hybrid mapping config (Section 2) should support custom templates per file type or glob pattern.

### Global state and event-driven patterns

Redux stores, event buses, and pub/sub systems are structurally owned by no single file — the state shape, action types, reducers, selectors, and dispatching components are spread across the codebase. A file-centric index will never surface this implicitly.

The recommended approach is a dedicated concept file (e.g., `[[AppState]]`, `[[EventBus]]`) that centrally documents the state schema or event contract, lists all producers and consumers as file links, and flags invariants agents must respect. Individual design files for reducers, selectors, and event handlers then link *to* the concept file rather than describing global state themselves.

This keeps each design file scoped to what *it* does while making the global structure discoverable in one place.

---

## Decision Log

Decisions made during implementation that refine the architecture above. Referenced by phase plans in `plans/`.

| # | Phase | Decision | Resolution | Date |
|---|-------|----------|------------|------|
| D-001 | 2 | LLM usage for `.aindex` generation | Structural-only in Phase 2 (language + line count descriptions). LLM enrichment deferred to Phase 4 (Archivist). | 2026-02-19 |
| D-002 | 2 | `lexi index` scope | Single directory by default; `-r`/`--recursive` flag for bottom-up recursive indexing. | 2026-02-19 |
| D-003 | 2 | Token column in Child Map | Dropped. `AIndexEntry` has `name`, `entry_type`, `description` — no per-entry token count. Token budgets validated at artifact level. | 2026-02-19 |
| D-004 | 2 | `.aindex` change detection | Always regenerate in Phase 2 (no LLM cost). Revisit with directory-level composite hashing when Phase 4 introduces LLM costs. | 2026-02-19 |
| D-005 | 2 | Crawl config in schema | `CrawlConfig` added to `LexibraryConfig` with `binary_extensions` and `max_file_size_kb`. | 2026-02-19 |
| D-006 | 2 | Local Conventions population | Empty placeholder in Phase 2. Future phase adds agent/human population mechanism with preservation on `lexi update`. | 2026-02-19 |

### Open Questions

| # | Phase | Question | Status |
|---|-------|----------|--------|
| Q-001 | 2+ | How should `lexi update` preserve agent/human-authored Local Conventions when regenerating `.aindex`? Options: parse-and-reinject vs. treat as untouchable section. | Open |
| Q-002 | 4 | When LLM enrichment replaces structural descriptions, should change detection use directory listing hash (cheap, misses content changes) or composite hash (listing + child content hashes, complete but more expensive)? | Open — revisit in Phase 4 planning |

# Codebase Cartography: A Navigation System for AI Agents

## The Problem

AI agents working with codebases face a fundamental tension: they need enough context to make good decisions, but every token of context they consume degrades their ability to reason. Large, multi-repo, polyglot projects make this worse — an agent looking for "where does user authentication happen" shouldn't need to read 200 files to find out.

What's needed is a **layered map** that lets agents drill down from "what is this project" to "what does this function do" with minimal context consumption at each step. The map must stay current as the code changes, work across languages, and serve agents with very different context budgets.

---

## Architecture Overview

The system has four layers, each serving a different depth of inquiry:

```
┌─────────────────────────────────────────────────┐
│  Layer 1: START_HERE.md                         │
│  "Where am I? What is this? Where do I go?"     │
├─────────────────────────────────────────────────┤
│  Layer 2: Library (per-file/dir markdown docs)  │
│  "What does this code do, specifically?"         │
├─────────────────────────────────────────────────┤
│  Layer 3: Index files (per-directory TOCs)       │
│  "What's in this folder and why?"                │
├─────────────────────────────────────────────────┤
│  Layer 4: Knowledge Graph (zettelkasten links)  │
│  "What connects to what, conceptually?"          │
└─────────────────────────────────────────────────┘
```

These layers live in a **separate directory tree** (e.g., `.codemap/`) that mirrors the codebase but contains only documentation. The codebase itself stays untouched.

---

## Layer 1: START_HERE.md — The Entry Point

### Purpose
A single file an agent reads first. It should orient the agent within ~500 tokens and let it decide where to drill down. Think of it as a building's lobby directory.

### Structure

```markdown
# [Project Name] — Agent Navigation Map

## What This Is
[2-3 sentences: what the project does, who it's for, what problem it solves]

## Architecture at a Glance
[Simple text diagram showing major components and how they connect]

## Repository Map
| Repo | Purpose | Primary Language | Entry Point |
|------|---------|-----------------|-------------|
| `api-server` | REST API + business logic | Python/FastAPI | `.codemap/repos/api-server/INDEX.md` |
| `web-client` | React SPA frontend | TypeScript/React | `.codemap/repos/web-client/INDEX.md` |
| `shared-types` | Shared type definitions | TypeScript | `.codemap/repos/shared-types/INDEX.md` |
| `infra` | Terraform + CI/CD | HCL/YAML | `.codemap/repos/infra/INDEX.md` |

## Navigation by Intent
- **"I need to change how users authenticate"** → [auth domain map](.codemap/domains/auth.md)
- **"I need to add a new API endpoint"** → [API patterns guide](.codemap/domains/api-patterns.md)
- **"I need to understand the data model"** → [data model map](.codemap/domains/data-models.md)
- **"I need to fix a frontend bug"** → [frontend architecture](.codemap/repos/web-client/INDEX.md)
- **"I need to understand the deployment pipeline"** → [infra overview](.codemap/repos/infra/INDEX.md)

## Conventions & Patterns
[Brief list of project-wide conventions: naming, error handling, testing approach, etc.]

## Tech Stack Summary
[Compact list: languages, frameworks, databases, infrastructure]
```

### Design Principles
- **Must fit in a single context load** (~500-800 tokens). If it's longer, it's wrong.
- **Intent-based navigation** is critical. Agents don't think in directory structures; they think in tasks. The "Navigation by Intent" section is the most important part.
- **One per project**, not one per repo. If you have 12 repos, you still have one START_HERE that shows the whole picture.

---

## Layer 2: The Library — Per-File Documentation

### Purpose
Small, focused markdown files that describe individual code files, classes, modules, or logical units. An agent reads one of these to understand a specific piece of code **without reading the code itself**.

### The 1:1 Mapping Question

**Recommendation: Hybrid approach.** Not every file deserves its own doc. The mapping strategy should vary by file type:

| File Type | Mapping Strategy | Rationale |
|-----------|-----------------|-----------|
| Core domain models | 1:1 per file | These are the nouns of your system. Agents need precise docs. |
| Service/controller classes | 1:1 per file | Business logic lives here. Worth documenting individually. |
| Utility/helper files | Group into one doc per directory | `utils/string_helpers.py` doesn't need its own page. |
| Config files | Group into one doc | Describe the config schema, not each file. |
| Tests | Reference from the file they test | Don't create separate docs for test files. |
| Generated files | Skip entirely | Migrations, lockfiles, build output — ignore. |
| Types/interfaces | 1:1 for core types, group for trivial ones | Core domain types deserve individual docs. |
| React components | 1:1 for pages/features, group for atoms/UI primitives | A `<Button>` doesn't need a doc; a `<CheckoutFlow>` does. |

### File Doc Template

Each library doc should follow a consistent structure. Consistency is what makes this machine-readable:

```markdown
# [File/Module Name]

## Source
`repos/api-server/src/services/auth_service.py`

## Purpose
[1-2 sentences: what this does and why it exists. Not HOW — WHY.]

## Public Interface
| Name | Type | Description |
|------|------|-------------|
| `authenticate(credentials)` | method | Validates credentials, returns JWT token or raises AuthError |
| `refresh_token(token)` | method | Issues new token from valid refresh token |
| `revoke_session(session_id)` | method | Invalidates active session |

## Input/Output Contracts
- `authenticate`: Takes `Credentials` (email + password) → returns `AuthToken` or raises `AuthError`
- `refresh_token`: Takes `str` (JWT) → returns `AuthToken` or raises `TokenExpiredError`

## Dependencies (what this uses)
- `UserRepository` — looks up user records
- `TokenService` — JWT creation and validation
- `PasswordHasher` — bcrypt comparison
- `SessionStore` — Redis session management

## Dependents (what uses this)
- `AuthController` — HTTP layer that calls these methods
- `WebSocketAuthMiddleware` — validates tokens on WS connections

## Key Behaviors & Edge Cases
- Failed auth attempts are rate-limited (5 per minute per IP)
- Tokens expire after 15 minutes; refresh tokens after 7 days
- Revoked sessions are cached in Redis for fast rejection

## Related Tests
- `tests/services/test_auth_service.py` — unit tests
- `tests/integration/test_auth_flow.py` — end-to-end auth flow

## Tags
`auth` `security` `jwt` `session-management`
```

### Sizing Constraint
Each library doc should be **200-400 tokens**. If it's bigger, the file it describes is probably doing too much (which is worth flagging), or the doc needs splitting. The whole point is that an agent can read 3-5 of these without burning significant context.

---

## Layer 3: Index Files — Directory-Level TOCs

### Purpose
Every directory in the library gets an `INDEX.md` that serves as a local table of contents. When an agent navigates to a directory, it reads the index to decide which file docs to load.

### Structure

```markdown
# /services — Business Logic Layer

## Purpose
Contains all domain services. Each service encapsulates a bounded context
of business logic. Services are called by controllers (HTTP layer) and
by event handlers (async processing).

## Files
| File | Purpose | Key Concepts |
|------|---------|-------------|
| `auth_service.md` | Authentication and session management | JWT, sessions, rate limiting |
| `billing_service.md` | Subscription and payment processing | Stripe, invoices, plans |
| `notification_service.md` | Email, SMS, push notification dispatch | Templates, queues, preferences |
| `user_service.md` | User CRUD, profile management, preferences | Profiles, settings, avatars |

## Subdirectories
| Directory | Purpose |
|-----------|---------|
| `internal/` | Internal services not exposed via API (background jobs, sync tasks) |
| `integrations/` | Third-party service wrappers (Stripe, SendGrid, Twilio) |

## Patterns in This Directory
- All services accept a `Context` object for tracing and auth info
- Services raise domain exceptions, never HTTP exceptions
- Each service has a corresponding interface for testing

## Cross-Cutting Concerns
- All service methods are wrapped in OpenTelemetry spans
- Database transactions are managed at the service level, not repository level
```

### Design Principles
- **Target: 100-200 tokens.** Index files are routing tables, not documentation.
- **Every directory gets one**, no exceptions. Even if a directory has two files, the index explains *why those two files are grouped*.
- **The "Patterns" section is key.** It tells the agent the local conventions so it doesn't have to infer them from reading code.

---

## Layer 4: Knowledge Graph — Zettelkasten-Style Semantic Links

### Purpose
The first three layers follow the file system's tree structure. But codebases don't think in trees — they think in **graphs**. Authentication touches the user model, the API layer, the frontend login page, the session store, and the deployment config. The knowledge graph captures these cross-cutting connections.

### Implementation

The graph lives in `.codemap/graph/` and consists of two types of files:

#### 4a. Concept Nodes (the "zettels")

Each node represents a **concept**, not a file. One concept might span many files across many repos.

```markdown
# Authentication

## ID
`concept:auth`

## Summary
The system uses JWT-based authentication with short-lived access tokens
(15 min) and long-lived refresh tokens (7 days). Sessions are tracked
in Redis. Rate limiting is applied at the IP level.

## Touches
- [[concept:user-model]] — auth depends on user records
- [[concept:api-gateway]] — all authenticated requests pass through gateway
- [[concept:session-management]] — auth creates and validates sessions
- [[concept:frontend-routing]] — client-side route guards check auth state
- [[concept:deployment]] — JWT secrets managed via environment config

## Implemented In
| Component | Location |
|-----------|----------|
| Auth service | `.codemap/repos/api-server/src/services/auth_service.md` |
| Auth controller | `.codemap/repos/api-server/src/controllers/auth_controller.md` |
| Auth middleware | `.codemap/repos/api-server/src/middleware/auth_middleware.md` |
| Login page | `.codemap/repos/web-client/src/pages/login.md` |
| Auth context | `.codemap/repos/web-client/src/contexts/auth_context.md` |
| Token util | `.codemap/repos/shared-types/src/auth/tokens.md` |

## Decision Log
- **Why JWT over session cookies?** — Need stateless auth for microservice-to-microservice calls
- **Why Redis for sessions?** — Need fast revocation; DB round-trip too slow for middleware

## Tags
`auth` `security` `jwt` `cross-cutting`
```

#### 4b. Graph Index

A single `GRAPH_INDEX.md` that lists all concept nodes, organized by domain:

```markdown
# Knowledge Graph Index

## Domains
### Identity & Access
- [[concept:auth]] — Authentication flow
- [[concept:authorization]] — Role-based access control
- [[concept:user-model]] — User data and profiles
- [[concept:session-management]] — Session lifecycle

### Commerce
- [[concept:billing]] — Subscription and payment
- [[concept:pricing]] — Plan tiers and features
- [[concept:invoicing]] — Invoice generation and delivery

### Infrastructure
- [[concept:deployment]] — CI/CD and environments
- [[concept:observability]] — Logging, metrics, tracing
- [[concept:data-storage]] — Database and cache architecture

## Cross-Cutting Concerns
- [[concept:error-handling]] — Error patterns across the stack
- [[concept:testing-strategy]] — How and what we test
- [[concept:api-conventions]] — REST API design patterns
```

### How Agents Use the Graph

An agent working on a task reads the relevant concept node(s) to understand the full scope of what it's touching. This prevents the classic failure mode where an agent changes the backend auth logic but doesn't know about the frontend auth context that also needs updating.

The `[[concept:...]]` links use zettelkasten-style wikilinks. Agents can resolve these to file paths. The linking pattern creates a navigable web: from any concept, you can reach related concepts in one hop.

---

## Directory Structure

```
.codemap/
├── START_HERE.md                    # Layer 1: Entry point
├── repos/                           # Layer 2 + 3: Library
│   ├── api-server/
│   │   ├── INDEX.md                 # Layer 3: Repo-level index
│   │   └── src/
│   │       ├── INDEX.md
│   │       ├── services/
│   │       │   ├── INDEX.md
│   │       │   ├── auth_service.md
│   │       │   └── billing_service.md
│   │       ├── controllers/
│   │       │   ├── INDEX.md
│   │       │   └── auth_controller.md
│   │       └── models/
│   │           ├── INDEX.md
│   │           └── user.md
│   ├── web-client/
│   │   ├── INDEX.md
│   │   └── src/
│   │       ├── INDEX.md
│   │       └── pages/
│   │           ├── INDEX.md
│   │           └── login.md
│   └── shared-types/
│       └── INDEX.md
├── graph/                           # Layer 4: Knowledge graph
│   ├── GRAPH_INDEX.md
│   ├── auth.md
│   ├── user-model.md
│   ├── billing.md
│   └── deployment.md
└── .codemap-config.yaml             # Generator configuration
```

---

## Self-Updating Mechanism

This is the hardest part and the most important. A map that's wrong is worse than no map.

### Update Strategy: Diff-Based Incremental

The updater runs as a **CI/CD step** (or git hook) and works in three phases:

#### Phase 1: Detect What Changed
```
git diff --name-only HEAD~1 HEAD
```
From the diff, classify changes:
- **New files** → generate new library docs
- **Deleted files** → remove library docs + update indexes and graph
- **Modified files** → re-analyze and update existing docs
- **Renamed/moved files** → update paths across all layers

#### Phase 2: Re-analyze Changed Files
For each changed file, run language-aware static analysis to extract:
- Public API surface (functions, classes, methods, exports)
- Import/dependency relationships
- Type signatures and contracts
- Test file associations

Tools by language:
| Language | AST Parser | Dependency Extraction |
|----------|-----------|----------------------|
| Python | `ast` module, `jedi` | Import statements, `requirements.txt` |
| TypeScript/JS | `ts-morph`, `babel` | Import/export statements, `package.json` |
| Go | `go/ast` | Import paths |
| Rust | `syn`, `rust-analyzer` | `use` statements, `Cargo.toml` |
| Java/Kotlin | `tree-sitter` | Import statements, `build.gradle` |
| Ruby | `parser` gem | `require` statements, `Gemfile` |

#### Phase 3: Regenerate Docs
Use an LLM to regenerate **only the affected docs**. The prompt includes:
- The old doc (for continuity — don't rewrite what hasn't changed)
- The new code
- The AST diff (what specifically changed)
- Surrounding context (the INDEX.md, related concept nodes)

The LLM produces an updated doc. A validation step checks:
- Token count is within bounds (200-400 for file docs, 100-200 for indexes)
- All referenced files still exist
- All `[[concept:...]]` links resolve
- Dependencies/dependents are consistent (if A says it depends on B, B should list A as a dependent)

#### Phase 4: Update Graph (Periodic)
Concept nodes change less frequently than file docs. Run a full graph reconciliation on a schedule (weekly) or when significant structural changes are detected (new directories, new repos, major refactors). This uses an LLM with a broader context: all the updated file docs feed into an analysis that asks "have any conceptual boundaries shifted?"

### Update Triggers
| Trigger | Scope | Timing |
|---------|-------|--------|
| PR merge to main | Changed files only | Immediate (CI step) |
| Manual invocation | Specified scope | On demand |
| Scheduled full rebuild | Everything | Weekly |
| New repo added | Full repo + START_HERE | On detection |

### Staleness Detection
Each doc includes a metadata footer:

```markdown
<!-- codemap:meta
source: repos/api-server/src/services/auth_service.py
source_hash: a3f2b8c1
generated: 2025-06-15T10:30:00Z
generator: codemap v0.4.2
model: claude-sonnet-4-5
-->
```

A CI check compares `source_hash` against the current file hash. If they diverge and no update has run, the doc is flagged as stale. Stale docs can include a warning agents will see:

```markdown
> ⚠️ This doc may be outdated. Source file changed since last update.
```

---

## Adapting to Different Agent Types

Different agents have different context budgets and reasoning styles. The map should work for all of them.

### Small Context Agents (~4K-8K tokens)
- Read START_HERE.md → one INDEX.md → one file doc
- Use the graph sparingly (one concept node at a time)
- Rely heavily on the "Navigation by Intent" section

### Medium Context Agents (~32K-128K tokens)
- Can load START_HERE + several INDEX files + 5-10 file docs
- Can load 2-3 concept nodes to understand cross-cutting concerns
- Sweet spot for this system

### Large Context Agents (~200K+ tokens)
- Could load most of the library but **shouldn't**
- Better strategy: load the graph index + relevant concept nodes + targeted file docs
- The map helps them avoid the "I loaded everything and now I'm confused" failure mode

### Agent-Specific Hints (Optional)
START_HERE can include a section:

```markdown
## Agent Configuration
- **If your context is < 16K tokens**: Follow links one at a time. Read an INDEX before any file docs.
- **If your context is 16K-128K tokens**: Load this file + the GRAPH_INDEX + relevant concept nodes.
- **If your context is > 128K tokens**: Load this file + GRAPH_INDEX + all INDEX files for the relevant repo. Load file docs on demand.
```

---

## Implementation Roadmap

### Phase 1: Manual Bootstrap (Week 1-2)
Write the system for one repo by hand. This validates the format and sizing before automating.
- Write START_HERE.md
- Write INDEX.md files for 3-4 key directories
- Write 10-15 file docs for core modules
- Write 3-5 concept nodes for major domains
- Test with an actual agent: give it tasks and see if the map helps

### Phase 2: Generator MVP (Week 3-5)
Build the automated generator.
- File discovery and classification (what gets a doc, what gets grouped)
- AST parsing for 2-3 primary languages
- LLM-powered doc generation with consistent templates
- INDEX file generation from directory contents
- Basic concept node extraction (start with dependency clusters)

### Phase 3: CI Integration (Week 6-7)
- Git diff-based incremental updates
- PR check that flags stale docs
- Hash-based staleness detection
- Validation pipeline (link checking, token counting, consistency)

### Phase 4: Graph Intelligence (Week 8-10)
- Automated concept extraction from file docs
- Cross-repo relationship detection
- Graph consistency validation
- Periodic full reconciliation

### Phase 5: Multi-Repo Scale (Week 11-12)
- Multi-repo START_HERE generation
- Cross-repo graph linking
- Repository onboarding CLI (`codemap init`)
- Configuration for project-specific conventions

---

## Open Questions to Resolve

1. **Where does the `.codemap/` directory live?** Options: (a) in each repo alongside code, (b) in a separate dedicated repo, (c) in a monorepo root. Tradeoff is between proximity to code (helps with updates) and centralization (helps with cross-repo views). **Recommendation**: one dedicated repo that the CI pipelines of all source repos push updates to.

2. **How do agents discover the map?** The agent's system prompt or tool configuration needs to know about `.codemap/`. This is an integration question — the map is only useful if agents are told to read it.

3. **How granular should concept nodes be?** Too few and they're too broad to be useful. Too many and the graph becomes its own navigation problem. **Heuristic**: if a concept spans more than 2 repos or more than 10 files, it deserves a node.

4. **Should file docs include code snippets?** Probably not — they add tokens and go stale faster. The docs should describe *what* and *why*, not show *how*. An agent that needs the actual code can read the source file after the doc tells it where to look.

5. **What about non-code artifacts?** Database schemas, API specs (OpenAPI), infrastructure definitions (Terraform), CI configs — these are part of the codebase but aren't "code." They should get library docs too, with adapted templates.

6. **Version alignment**: When the code is at commit `abc123`, the map should correspond to that commit. If the map lags behind (e.g., CI hasn't run yet), agents could get incorrect information. The staleness metadata helps, but real-time accuracy during active development is an unsolved tension.
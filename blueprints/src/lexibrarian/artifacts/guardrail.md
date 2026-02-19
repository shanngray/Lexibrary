# artifacts/guardrail

**Summary:** Pydantic 2 model for guardrail thread artifacts tracking known footguns, failed approaches, and resolutions.

## Interface

| Name | Key Fields | Purpose |
| --- | --- | --- |
| `GuardrailStatus` | `Literal["active", "resolved", "stale"]` | Thread lifecycle state |
| `GuardrailThread` | `thread_id`, `title`, `status: GuardrailStatus`, `scope: list[str]`, `reported_by`, `date`, `problem`, `failed_approaches`, `resolution`, `evidence` | One guardrail record |

## Dependents

- `lexibrarian.artifacts.__init__` — re-exports
- `lexi guardrail new` CLI command (stub) will populate these

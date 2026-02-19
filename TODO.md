1) Need to add design blueprints directly into Lexibrary.
    - Designs should follow the same structure as codes - file for file
    - Designs are in plain english and should be easy for a coding agent to understand.
    - Inputs & Outputs
    - Dependents and Dependencies
    - Tests
    - Purpose
    - Description
    - Guardrails
    - Future Direction -> this could maybe be pulled out into issues
    - Anything else
2) Lexibrary should only index design files
3) Should be built to work in concert with OpenSpec and Beads
4) How it stays up to date needs to be revised
5) It needs a knowledge graph that holds it all together -> the purpose of the KG is to pinpoint which design files the agent should add into context.
6) All interaction via command line interface only.
7) Agent-first app.
8) Auto-setup for Cursor, Claude Code, Codex.
Issues:
 - Multi-repo support
 - Global Events / Redux
 - Deep Abstraction
 - COnventions

library of a codebase that an agent can use to quickly understand the codebase and navigate it. written by agents for agents.
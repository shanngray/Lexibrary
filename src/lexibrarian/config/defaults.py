"""Default project configuration template."""

from __future__ import annotations

DEFAULT_PROJECT_CONFIG_TEMPLATE = """\
# Lexibrarian project configuration
# This file is created by `lexi init` and lives at .lexibrary/config.yaml
# Values here override the global config at ~/.config/lexibrarian/config.yaml

# LLM provider settings
llm:
  provider: anthropic                    # LLM provider: anthropic, openai, ollama
  model: claude-sonnet-4-6              # Model identifier
  api_key_env: ANTHROPIC_API_KEY         # Env var holding the API key
  max_retries: 3                         # Retry attempts on API failure
  timeout: 60                            # Request timeout in seconds

# Per-artifact token budgets (validation targets for generated content)
token_budgets:
  start_here_tokens: 800                 # START_HERE.md budget
  handoff_tokens: 100                    # HANDOFF.md budget
  design_file_tokens: 400                # Full design file budget
  design_file_abridged_tokens: 100       # Abridged design file budget
  aindex_tokens: 200                     # .aindex routing table budget
  concept_file_tokens: 400               # Concept file budget

# Mapping strategies (glob patterns → generation strategy)
# Populated in Phase 4; empty list uses default 1:1 mapping
mapping:
  strategies: []

# Ignore patterns for file discovery
ignore:
  use_gitignore: true                    # Respect .gitignore files
  additional_patterns:
    - .lexibrary/START_HERE.md
    - .lexibrary/HANDOFF.md
    - ".lexibrary/**/*.md"
    - ".lexibrary/**/.aindex"
    - node_modules/
    - __pycache__/
    - .git/
    - .venv/
    - venv/
    - "*.lock"

# Background daemon settings
daemon:
  debounce_seconds: 2.0                  # Coalesce rapid file events (seconds)
  sweep_interval_seconds: 300            # Full re-index safety net (seconds)
  enabled: true                          # Enable daemon on start
"""

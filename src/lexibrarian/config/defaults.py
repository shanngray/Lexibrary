"""Default configuration template."""

from __future__ import annotations

DEFAULT_CONFIG_TEMPLATE = """\
# Lexibrarian Configuration
# This file controls how Lexibrarian indexes your codebase.

[llm]
# LLM provider configuration
provider = "{provider}"                      # LLM provider: "anthropic", "openai", or "ollama"
model = "{model}"                            # Model identifier
api_key_env = "{api_key_env}"               # Environment variable for API key
max_retries = 3                             # Number of retry attempts on API failure
timeout = 60                                # Request timeout in seconds

[tokenizer]
# Token counting configuration
model = "cl100k_base"                       # Tokenizer model (tiktoken)
max_tokens_per_chunk = 4000                 # Maximum tokens per chunk

[crawl]
# Crawler behavior
max_file_size_kb = 512                      # Skip files larger than this (KB)
max_files_per_llm_batch = 10                # Max files to process in one LLM batch
summary_max_tokens = 80                     # Max tokens for file summaries
dir_summary_max_tokens = 150                # Max tokens for directory summaries
binary_extensions = [                       # Known binary file extensions to skip
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp3", ".wav", ".mp4", ".avi", ".mov",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".pyc", ".pyo", ".so", ".dll", ".dylib", ".o", ".a",
    ".class", ".jar", ".wasm",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pdf", ".exe", ".bin", ".dat", ".db", ".sqlite",
]

[ignore]
# Ignore patterns
use_gitignore = true                        # Respect .gitignore files
additional_patterns = [                     # Additional patterns to ignore
    ".aindex",
    "lexibrary.toml",
    "node_modules/",
    "__pycache__/",
    ".git/",
    ".venv/",
    "venv/",
    "*.lock",
]

[daemon]
# Background daemon settings
debounce_seconds = 2.0                      # Debounce file system events (seconds)
sweep_interval_seconds = 300                # Full sweep interval (seconds)

[output]
# Output file names
index_filename = ".aindex"                  # Index file name
cache_filename = ".lexibrarian_cache.json"  # Cache file name
log_filename = ".lexibrarian.log"           # Log file name
"""

PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "anthropic": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250514",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
    },
    "ollama": {
        "provider": "ollama",
        "model": "llama3.2",
        "api_key_env": "",
    },
}


def render_default_config(provider: str) -> str:
    """Render the default config template with provider-specific values.

    Unknown providers fall back to anthropic defaults.
    """
    values = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["anthropic"])
    return DEFAULT_CONFIG_TEMPLATE.format(**values)

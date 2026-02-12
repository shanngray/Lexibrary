"""Configuration schema with Pydantic models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5-20250514"
    api_key_env: str = "ANTHROPIC_API_KEY"
    max_retries: int = 3
    timeout: int = 60


class TokenizerConfig(BaseModel):
    """Tokenizer configuration."""

    backend: str = "tiktoken"
    model: str = "cl100k_base"
    max_tokens_per_chunk: int = 4000


class CrawlConfig(BaseModel):
    """Crawling behavior configuration."""

    max_file_size_kb: int = 512
    max_files_per_llm_batch: int = 10
    summary_max_tokens: int = 80
    dir_summary_max_tokens: int = 150
    binary_extensions: list[str] = Field(
        default_factory=lambda: [
            # Images
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
            # Audio/Video
            ".mp3", ".wav", ".mp4", ".avi", ".mov",
            # Archives
            ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
            # Compiled
            ".pyc", ".pyo", ".so", ".dll", ".dylib", ".o", ".a",
            ".class", ".jar", ".wasm",
            # Fonts
            ".woff", ".woff2", ".ttf", ".otf", ".eot",
            # Other binary
            ".pdf", ".exe", ".bin", ".dat", ".db", ".sqlite",
        ]
    )


class IgnoreConfig(BaseModel):
    """Ignore pattern configuration."""

    use_gitignore: bool = True
    additional_patterns: list[str] = Field(
        default_factory=lambda: [
            ".aindex",
            "lexibrary.toml",
            "node_modules/",
            "__pycache__/",
            ".git/",
            ".venv/",
            "venv/",
            "*.lock",
        ]
    )


class DaemonConfig(BaseModel):
    """Daemon watch configuration."""

    debounce_seconds: float = 2.0
    sweep_interval_seconds: int = 300


class OutputConfig(BaseModel):
    """Output file configuration."""

    index_filename: str = ".aindex"
    cache_filename: str = ".lexibrarian_cache.json"
    log_filename: str = ".lexibrarian.log"


class LexibraryConfig(BaseModel):
    """Top-level Lexibrarian configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    tokenizer: TokenizerConfig = Field(default_factory=TokenizerConfig)
    crawl: CrawlConfig = Field(default_factory=CrawlConfig)
    ignore: IgnoreConfig = Field(default_factory=IgnoreConfig)
    daemon: DaemonConfig = Field(default_factory=DaemonConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

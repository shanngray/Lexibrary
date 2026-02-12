"""CLI application for Lexibrarian."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from lexibrarian.config import LexibraryConfig, find_config_file, load_config
from lexibrarian.config.defaults import render_default_config

console = Console()

app = typer.Typer(
    name="lexibrarian",
    help="AI-friendly codebase indexer. Creates .aindex files for enhanced AI code understanding.",
    no_args_is_help=True,
)


def _load_dotenv(path: Path | None = None) -> None:
    """Load variables from a .env file into os.environ (won't override existing vars)."""
    env_file = (path or Path.cwd()) / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def _resolve_project_path(path: Path) -> Path:
    """Resolve project path, falling back to LEXI_PROJECT_PATH env var."""
    if path == Path("."):
        env_path = os.environ.get("LEXI_PROJECT_PATH")
        if env_path:
            return Path(env_path).resolve()
    return path.resolve()


def _apply_env_overrides(config: LexibraryConfig) -> None:
    """Override config values from LEXI_* environment variables."""
    if provider := os.environ.get("LEXI_LLM_PROVIDER"):
        config.llm.provider = provider
    if model := os.environ.get("LEXI_LLM_MODEL"):
        config.llm.model = model
    if api_key := os.environ.get("LEXI_API_KEY"):
        # Set the provider-specific env var so the BAML client picks it up
        os.environ[config.llm.api_key_env] = api_key


@app.callback()
def _app_callback() -> None:
    """Load .env before running any command."""
    _load_dotenv()

_GITIGNORE_ENTRIES = [
    ".aindex",
    ".lexibrarian_cache.json",
    ".lexibrarian.log",
    ".lexibrarian.pid",
]


@app.command()
def init(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the project directory to initialize.",
            exists=False,
        ),
    ] = Path("."),
    *,
    provider: Annotated[
        str,
        typer.Option(help="LLM provider to configure."),
    ] = "anthropic",
) -> None:
    """Initialize Lexibrary in a project. Creates lexibrary.toml config file."""
    target = _resolve_project_path(path)
    config_path = target / "lexibrary.toml"

    if config_path.exists():
        console.print(
            f"[yellow]Config file already exists:[/yellow] {config_path}",
        )
        raise typer.Exit(code=1)

    # Write config
    target.mkdir(parents=True, exist_ok=True)
    config_content = render_default_config(provider)
    config_path.write_text(config_content, encoding="utf-8")
    console.print(f"[green]Created[/green] {config_path}")

    # Manage .gitignore
    gitignore_path = target / ".gitignore"
    _update_gitignore(gitignore_path)

    # Next steps
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Edit [cyan]lexibrary.toml[/cyan] to customize settings")
    console.print("  2. Run [cyan]lexi crawl[/cyan] to index your project")


def _update_gitignore(gitignore_path: Path) -> None:
    """Create or update .gitignore with Lexibrarian entries."""
    existing_lines: list[str] = []
    if gitignore_path.exists():
        existing_lines = gitignore_path.read_text(encoding="utf-8").splitlines()

    missing = [entry for entry in _GITIGNORE_ENTRIES if entry not in existing_lines]
    if not missing:
        return

    lines_to_add = ["", "# Lexibrary", *missing]
    with gitignore_path.open("a", encoding="utf-8") as f:
        # Ensure we start on a new line if file doesn't end with one
        if existing_lines and existing_lines[-1] != "":
            f.write("\n")
        f.write("\n".join(lines_to_add) + "\n")

    console.print(f"[green]Updated[/green] {gitignore_path}")


@app.command()
def crawl(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the project directory to crawl.",
            exists=False,
        ),
    ] = Path("."),
    *,
    full: Annotated[
        bool,
        typer.Option("--full", help="Force full re-crawl, ignoring cache."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview what would be indexed without writing files."),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Enable debug logging."),
    ] = False,
) -> None:
    """Run the Lexibrarian crawler. Generates .aindex files for all directories."""
    root = _resolve_project_path(path)

    # Load config
    config_path = find_config_file(root)
    config = load_config(config_path)
    _apply_env_overrides(config)

    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            filename=str(root / config.output.log_filename),
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )

    # Import crawler engine — may not be implemented yet
    try:
        from lexibrarian.crawler import full_crawl as run_crawl
        from lexibrarian.crawler.change_detector import ChangeDetector
        from lexibrarian.ignore import create_ignore_matcher
        from lexibrarian.llm import create_llm_service
        from lexibrarian.tokenizer import create_tokenizer
    except ImportError:
        console.print(
            "[red]Crawler engine is not yet available.[/red] "
            "This feature requires the crawler module to be implemented."
        )
        raise typer.Exit(code=1) from None

    # Build dependencies
    ignore_matcher = create_ignore_matcher(config, root)
    token_counter = create_tokenizer(config.tokenizer)
    llm_service = create_llm_service(config.llm)
    change_detector = ChangeDetector(root / config.output.cache_filename)
    change_detector.load()

    if full:
        change_detector.clear()
        console.print("[yellow]Cache cleared — full re-crawl[/yellow]")

    if dry_run:
        console.print("[cyan]Dry run mode — no files will be written[/cyan]")

    # Run crawl with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Crawling...", total=None)

        def on_progress(current: int, total: int, dir_name: str) -> None:
            progress.update(task_id, total=total, completed=current, description=dir_name)

        stats = asyncio.run(
            run_crawl(
                root=root,
                config=config,
                ignore_matcher=ignore_matcher,
                token_counter=token_counter,
                llm_service=llm_service,
                change_detector=change_detector,
                dry_run=dry_run,
                progress_callback=on_progress,
            )
        )

    # Summary table
    table = Table(title="Crawl Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Directories indexed", str(stats.directories_indexed))
    table.add_row("Files summarized", str(stats.files_summarized))
    table.add_row("Files cached", str(stats.files_cached))
    table.add_row("Files skipped", str(stats.files_skipped))
    table.add_row("LLM calls", str(stats.llm_calls))
    if stats.errors > 0:
        table.add_row("Errors", f"[red]{stats.errors}[/red]")
    console.print(table)

    if dry_run:
        console.print("[cyan]Dry run complete[/cyan] — no files were written.")


@app.command()
def status(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the project directory to check.",
            exists=False,
        ),
    ] = Path("."),
) -> None:
    """Show indexing status: files indexed, stale files, daemon status."""
    root = _resolve_project_path(path)

    # Load config
    config_path = find_config_file(root)
    config = load_config(config_path)
    _apply_env_overrides(config)

    config_display = str(config_path) if config_path else "not found (using defaults)"

    # Count .aindex files
    iandex_count = sum(1 for _ in root.rglob(config.output.index_filename))

    # Load cache and count entries
    cache_path = root / config.output.cache_filename
    cached_files = 0
    stale_files = 0
    if cache_path.exists():
        try:
            cache_data = json.loads(cache_path.read_text(encoding="utf-8"))
            files = cache_data.get("files", {})
            cached_files = len(files)
            # Detect stale files: cached but file no longer matches hash
            from lexibrarian.utils.hashing import hash_file

            for file_path_str, state in files.items():
                fp = Path(file_path_str)
                if not fp.exists():
                    stale_files += 1
                else:
                    try:
                        current_hash = hash_file(fp)
                        if current_hash != state.get("hash"):
                            stale_files += 1
                    except OSError:
                        stale_files += 1
        except (json.JSONDecodeError, KeyError):
            pass

    # Daemon PID detection
    pid_path = root / ".lexibrarian.pid"
    daemon_status = "not running"
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            daemon_status = f"running (PID {pid})"
        except (ValueError, ProcessLookupError, PermissionError):
            daemon_status = "not running (stale PID file)"

    # Build status panel
    lines = [
        f"[bold]Config:[/bold]       {config_display}",
        f"[bold]Provider:[/bold]     {config.llm.provider}",
        f"[bold]Model:[/bold]        {config.llm.model}",
        f"[bold]Tokenizer:[/bold]    {config.tokenizer.backend} ({config.tokenizer.model})",
        f"[bold]Directories:[/bold]  {iandex_count} indexed",
        f"[bold]Cached files:[/bold] {cached_files}",
        f"[bold]Stale files:[/bold]  {stale_files}",
        f"[bold]Daemon:[/bold]       {daemon_status}",
    ]

    if stale_files > 0:
        lines.append("")
        lines.append(
            "[yellow]Some files are stale. Run [cyan]lexi crawl[/cyan] to re-index.[/yellow]"
        )

    panel = Panel("\n".join(lines), title="Lexibrarian Status", border_style="blue")
    console.print(panel)


@app.command()
def clean(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the project directory to clean.",
            exists=False,
        ),
    ] = Path("."),
    *,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Remove all .aindex files and the cache from the project."""
    root = _resolve_project_path(path)

    config_path = find_config_file(root)
    config = load_config(config_path)
    _apply_env_overrides(config)

    # Find files to remove
    iandex_files = list(root.rglob(config.output.index_filename))
    cache_file = root / config.output.cache_filename
    log_file = root / config.output.log_filename

    files_to_remove: list[Path] = list(iandex_files)
    if cache_file.exists():
        files_to_remove.append(cache_file)
    if log_file.exists():
        files_to_remove.append(log_file)

    if not files_to_remove:
        console.print("Nothing to clean.")
        return

    console.print(f"Found [bold]{len(files_to_remove)}[/bold] file(s) to remove:")
    console.print(f"  .aindex files: {len(iandex_files)}")
    if cache_file.exists():
        console.print(f"  Cache: {cache_file.name}")
    if log_file.exists():
        console.print(f"  Log: {log_file.name}")

    if not yes:
        confirm = typer.confirm("Delete all?")
        if not confirm:
            console.print("[yellow]Aborted.[/yellow]")
            return

    for f in files_to_remove:
        f.unlink()

    console.print(f"[green]Removed {len(files_to_remove)} file(s).[/green]")


@app.command()
def daemon(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the project directory to watch.",
            exists=False,
        ),
    ] = Path("."),
    *,
    foreground: Annotated[
        bool,
        typer.Option("--foreground", help="Run in foreground instead of background."),
    ] = False,
) -> None:
    """Start the background daemon."""
    _root = _resolve_project_path(path)

    from lexibrarian.daemon import DaemonService

    svc = DaemonService(root=_root, foreground=foreground)
    svc.start()

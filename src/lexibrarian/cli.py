"""CLI application for Lexibrarian (v2)."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from lexibrarian.exceptions import LexibraryNotFoundError
from lexibrarian.init.scaffolder import create_lexibrary_skeleton
from lexibrarian.utils.root import find_project_root

console = Console()

app = typer.Typer(
    name="lexibrarian",
    help=(
        "AI-friendly codebase indexer. "
        "Maintains a .lexibrary/ library for LLM context navigation."
    ),
    no_args_is_help=True,
)

# ---------------------------------------------------------------------------
# Guardrail sub-group
# ---------------------------------------------------------------------------
guardrail_app = typer.Typer(help="Guardrail management commands.")
app.add_typer(guardrail_app, name="guardrail")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_project_root() -> Path:
    """Resolve the project root or exit with a friendly error."""
    try:
        return find_project_root()
    except LexibraryNotFoundError:
        console.print(
            "[red]No .lexibrary/ directory found.[/red] "
            "Run [cyan]lexi init[/cyan] to create one."
        )
        raise typer.Exit(1) from None


def _stub(name: str) -> None:
    """Print a standard stub message for unimplemented commands."""
    _require_project_root()
    console.print(f"[yellow]Not yet implemented.[/yellow]  ([dim]{name}[/dim])")


# ---------------------------------------------------------------------------
# init — fully implemented
# ---------------------------------------------------------------------------

@app.command()
def init(
    *,
    agent: Annotated[
        str | None,
        typer.Option(
            help="Agent environment to configure (cursor, claude, codex). "
            "Handled by `lexi setup`; accepted here for convenience.",
        ),
    ] = None,
) -> None:
    """Initialize Lexibrarian in a project. Creates .lexibrary/ directory."""
    project_root = Path.cwd()
    created = create_lexibrary_skeleton(project_root)

    if not created:
        console.print(
            "[yellow].lexibrary/ already exists.[/yellow] No files were overwritten."
        )
    else:
        console.print(
            f"[green]Created .lexibrary/ skeleton[/green] ({len(created)} items)"
        )

    if agent:
        console.print(
            f"[dim]--agent={agent} noted. Run [cyan]lexi setup {agent}[/cyan] "
            "to install agent environment rules.[/dim]"
        )


# ---------------------------------------------------------------------------
# Stub commands
# ---------------------------------------------------------------------------

@app.command()
def lookup(
    file: Annotated[
        Path,
        typer.Argument(help="Source file to look up."),
    ],
) -> None:
    """Return the design file for a source file."""
    from lexibrarian.artifacts.design_file_parser import parse_design_file_metadata
    from lexibrarian.config.loader import load_config
    from lexibrarian.utils.paths import mirror_path

    project_root = _require_project_root()
    config = load_config(project_root)

    target = Path(file).resolve()

    # Check scope: file must be under scope_root
    scope_abs = (project_root / config.scope_root).resolve()
    try:
        target.relative_to(scope_abs)
    except ValueError:
        console.print(
            f"[yellow]{file}[/yellow] is outside the configured scope_root "
            f"([dim]{config.scope_root}[/dim])."
        )
        raise typer.Exit(1) from None

    # Compute mirror path
    design_path = mirror_path(project_root, target)

    if not design_path.exists():
        console.print(
            f"[yellow]No design file found for[/yellow] {file}\n"
            f"Run [cyan]lexi update {file}[/cyan] to generate one."
        )
        raise typer.Exit(1)

    # Check staleness
    metadata = parse_design_file_metadata(design_path)
    if metadata is not None:
        try:
            current_hash = hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            if current_hash != metadata.source_hash:
                console.print(
                    "[yellow]Warning:[/yellow] Source file has changed since "
                    "the design file was last generated. "
                    "Run [cyan]lexi update " + str(file) + "[/cyan] to refresh.\n"
                )
        except OSError:
            pass

    # Display design file content
    content = design_path.read_text(encoding="utf-8")
    console.print(content)


@app.command()
def index(
    directory: Annotated[
        Path,
        typer.Argument(help="Directory to index."),
    ] = Path("."),
    *,
    recursive: Annotated[
        bool,
        typer.Option("-r", "--recursive", help="Recursively index all directories."),
    ] = False,
) -> None:
    """Generate .aindex file(s) for a directory."""
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from lexibrarian.config.loader import load_config
    from lexibrarian.indexer.orchestrator import index_directory, index_recursive

    project_root = _require_project_root()

    # Resolve directory relative to cwd
    target = Path(directory).resolve()

    # Validate directory exists
    if not target.exists():
        console.print(f"[red]Directory not found:[/red] {directory}")
        raise typer.Exit(1)

    if not target.is_dir():
        console.print(f"[red]Not a directory:[/red] {directory}")
        raise typer.Exit(1)

    # Validate directory is within project root
    try:
        target.relative_to(project_root)
    except ValueError:
        console.print(
            f"[red]Directory is outside the project root:[/red] {directory}\n"
            f"Project root: {project_root}"
        )
        raise typer.Exit(1) from None

    config = load_config(project_root)

    if recursive:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Indexing...", total=None)

            def _progress_callback(current: int, total: int, name: str) -> None:
                progress.update(task, description=f"Indexing [{current}/{total}] {name}")

            stats = index_recursive(
                target, project_root, config, progress_callback=_progress_callback
            )

        console.print(
            f"\n[green]Indexing complete.[/green] "
            f"{stats.directories_indexed} directories indexed, "
            f"{stats.files_found} files found"
            + (f", [red]{stats.errors} errors[/red]" if stats.errors else "")
            + "."
        )
    else:
        output_path = index_directory(target, project_root, config)
        console.print(f"[green]Wrote[/green] {output_path}")


@app.command()
def concepts(
    topic: Annotated[
        str | None,
        typer.Argument(help="Optional topic to search for."),
    ] = None,
) -> None:
    """List or search concept files."""
    _stub("concepts")


@app.command()
def guardrails(
    *,
    scope: Annotated[
        str | None,
        typer.Option(help="Limit search to a path scope."),
    ] = None,
    concept: Annotated[
        str | None,
        typer.Option(help="Filter by concept name."),
    ] = None,
) -> None:
    """Search guardrail threads."""
    _stub("guardrails")


@guardrail_app.command("new")
def guardrail_new(
    *,
    file: Annotated[
        str | None,
        typer.Option(help="Source file the guardrail relates to."),
    ] = None,
    mistake: Annotated[
        str | None,
        typer.Option(help="Description of the mistake."),
    ] = None,
    resolution: Annotated[
        str | None,
        typer.Option(help="How the mistake was resolved."),
    ] = None,
) -> None:
    """Record a new guardrail thread."""
    _stub("guardrail new")


@app.command()
def search(
    *,
    tag: Annotated[
        str | None,
        typer.Option(help="Tag to search for."),
    ] = None,
    scope: Annotated[
        str | None,
        typer.Option(help="Limit search to a path scope."),
    ] = None,
) -> None:
    """Search artifacts by tag across the library."""
    _stub("search")


@app.command()
def update(
    path: Annotated[
        Path | None,
        typer.Argument(help="File or directory to update. Omit to update entire project."),
    ] = None,
) -> None:
    """Re-index changed files and regenerate design files."""
    from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn

    from lexibrarian.archivist.pipeline import UpdateStats, update_file, update_project
    from lexibrarian.archivist.service import ArchivistService
    from lexibrarian.config.loader import load_config
    from lexibrarian.llm.rate_limiter import RateLimiter

    project_root = _require_project_root()
    config = load_config(project_root)
    rate_limiter = RateLimiter()
    archivist = ArchivistService(rate_limiter=rate_limiter, config=config.llm)

    if path is not None:
        target = Path(path).resolve()

        # Validate target exists
        if not target.exists():
            console.print(f"[red]Path not found:[/red] {path}")
            raise typer.Exit(1)

        # Validate target is within project root
        try:
            target.relative_to(project_root)
        except ValueError:
            console.print(
                f"[red]Path is outside the project root:[/red] {path}\n"
                f"Project root: {project_root}"
            )
            raise typer.Exit(1) from None

        if target.is_file():
            # Single file update
            console.print(f"Updating design file for [cyan]{path}[/cyan]...")
            result = asyncio.run(update_file(target, project_root, config, archivist))
            if result.failed:
                console.print(f"[red]Failed[/red] to update design file for {path}")
                raise typer.Exit(1)
            console.print(
                f"[green]Done.[/green] Change level: {result.change.value}"
            )
            return

        # Directory update -- update all files in subtree
        # Delegate to update_project but the scope is effectively the whole project;
        # the pipeline already filters by scope_root. We run the full pipeline.
        # For directory-scoped updates we run update_project (it respects scope_root).

    # Project or directory update with progress bar
    stats = UpdateStats()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Updating design files...", total=None)

        def _progress_callback(file_path: Path, change_level: object) -> None:
            progress.update(
                task,
                advance=1,
                description=f"Processing {file_path.name}",
            )

        stats = asyncio.run(
            update_project(project_root, config, archivist, progress_callback=_progress_callback)
        )

    if stats.start_here_failed:
        console.print("[red]Failed to regenerate START_HERE.md.[/red]")
    else:
        console.print("[green]START_HERE.md regenerated.[/green]")

    # Print summary stats
    console.print()
    console.print("[bold]Update summary:[/bold]")
    console.print(f"  Files scanned:       {stats.files_scanned}")
    console.print(f"  Files unchanged:     {stats.files_unchanged}")
    console.print(f"  Files created:       {stats.files_created}")
    console.print(f"  Files updated:       {stats.files_updated}")
    console.print(f"  Files agent-updated: {stats.files_agent_updated}")
    if stats.files_failed:
        console.print(f"  [red]Files failed:       {stats.files_failed}[/red]")
    if stats.aindex_refreshed:
        console.print(f"  .aindex refreshed:   {stats.aindex_refreshed}")
    if stats.token_budget_warnings:
        console.print(
            f"  [yellow]Token budget warnings: {stats.token_budget_warnings}[/yellow]"
        )

    if stats.files_failed:
        raise typer.Exit(1)


@app.command()
def describe(
    directory: Annotated[
        Path,
        typer.Argument(help="Directory whose .aindex billboard to update."),
    ],
    description: Annotated[
        str,
        typer.Argument(help="New billboard description for the directory."),
    ],
) -> None:
    """Update the billboard description in a directory's .aindex file."""
    from lexibrarian.artifacts.aindex_parser import parse_aindex
    from lexibrarian.artifacts.aindex_serializer import serialize_aindex
    from lexibrarian.utils.paths import aindex_path

    project_root = _require_project_root()

    target = Path(directory).resolve()

    # Validate directory exists
    if not target.exists():
        console.print(f"[red]Directory not found:[/red] {directory}")
        raise typer.Exit(1)

    if not target.is_dir():
        console.print(f"[red]Not a directory:[/red] {directory}")
        raise typer.Exit(1)

    # Validate directory is within project root
    try:
        target.relative_to(project_root)
    except ValueError:
        console.print(
            f"[red]Directory is outside the project root:[/red] {directory}\n"
            f"Project root: {project_root}"
        )
        raise typer.Exit(1) from None

    # Find the .aindex file
    aindex_file = aindex_path(project_root, target)

    if not aindex_file.exists():
        console.print(
            f"[yellow]No .aindex file found for[/yellow] {directory}\n"
            f"Run [cyan]lexi index {directory}[/cyan] to generate one first."
        )
        raise typer.Exit(1)

    # Parse, update billboard, re-serialize
    aindex = parse_aindex(aindex_file)
    if aindex is None:
        console.print(f"[red]Failed to parse .aindex file:[/red] {aindex_file}")
        raise typer.Exit(1)

    aindex.billboard = description
    serialized = serialize_aindex(aindex)
    aindex_file.write_text(serialized, encoding="utf-8")

    console.print(
        f"[green]Updated[/green] billboard for [cyan]{directory}[/cyan]"
    )


@app.command()
def validate() -> None:
    """Run consistency checks on the library."""
    _stub("validate")


@app.command()
def status(
    path: Annotated[
        Path | None,
        typer.Argument(help="Project directory to check."),
    ] = None,
) -> None:
    """Show library health and staleness summary."""
    _stub("status")


@app.command()
def setup(
    environment: Annotated[
        str | None,
        typer.Argument(help="Agent environment (cursor, claude, codex)."),
    ] = None,
    *,
    update_flag: Annotated[
        bool,
        typer.Option("--update", help="Update existing agent rules."),
    ] = False,
) -> None:
    """Install or update agent environment rules."""
    _stub("setup")


@app.command()
def daemon(
    path: Annotated[
        Path | None,
        typer.Argument(help="Project directory to watch."),
    ] = None,
) -> None:
    """Start the background file watcher daemon."""
    _stub("daemon")

"""CLI application for Lexibrarian (v2)."""

from __future__ import annotations

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
    _stub("lookup")


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
        typer.Argument(help="Optional path to re-index."),
    ] = None,
) -> None:
    """Re-index changed files and regenerate design files."""
    _stub("update")


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

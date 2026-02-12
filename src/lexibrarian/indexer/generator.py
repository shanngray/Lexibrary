from __future__ import annotations

from lexibrarian.indexer import DirEntry, FileEntry, IandexData


def _escape_pipe(text: str) -> str:
    """Escape literal pipe characters for Markdown tables."""
    return text.replace("|", "\\|")


def _files_table(files: list[FileEntry]) -> str:
    """Generate the Files section content."""
    if not files:
        return "(none)"

    sorted_files = sorted(files, key=lambda f: f.name.lower())
    lines = [
        "| File | Tokens | Description |",
        "| --- | --- | --- |",
    ]
    for f in sorted_files:
        lines.append(f"| `{f.name}` | {f.tokens} | {_escape_pipe(f.description)} |")
    return "\n".join(lines)


def _subdirs_table(subdirs: list[DirEntry]) -> str:
    """Generate the Subdirectories section content."""
    if not subdirs:
        return "(none)"

    sorted_dirs = sorted(subdirs, key=lambda d: d.name.lower())
    lines = [
        "| Directory | Description |",
        "| --- | --- |",
    ]
    for d in sorted_dirs:
        name = d.name if d.name.endswith("/") else d.name + "/"
        lines.append(f"| `{name}` | {_escape_pipe(d.description)} |")
    return "\n".join(lines)


def generate_iandex(data: IandexData) -> str:
    """Transform IandexData into a formatted .aindex Markdown string."""
    sections = [
        f"# {data.directory_name}",
        "",
        data.summary,
        "",
        "## Files",
        "",
        _files_table(data.files),
        "",
        "## Subdirectories",
        "",
        _subdirs_table(data.subdirectories),
        "",
    ]
    return "\n".join(sections)

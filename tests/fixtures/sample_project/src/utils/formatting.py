"""String formatting utilities."""


def titlecase(text: str) -> str:
    """Convert text to title case."""
    return text.title()


def truncate(text: str, max_length: int = 80) -> str:
    """Truncate text to max_length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."

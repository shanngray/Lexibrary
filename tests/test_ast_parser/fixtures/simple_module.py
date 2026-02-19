"""A simple Python module for testing interface extraction.

This fixture covers basic function definitions, constants, and __all__.
"""

MAX_RETRIES = 3
DEFAULT_TIMEOUT: float = 30.0

__all__ = ["process_data", "MAX_RETRIES", "DEFAULT_TIMEOUT"]


def process_data(input_path: str, output_path: str, verbose: bool = False) -> int:
    """Process data from input to output."""
    if verbose:
        print(f"Processing {input_path} -> {output_path}")
    return 0


def validate(data: dict) -> bool:
    """Validate input data."""
    return bool(data)


async def fetch_resource(url: str, timeout: float = 10.0) -> bytes:
    """Fetch a resource from a URL."""
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout) as resp:
            return await resp.read()

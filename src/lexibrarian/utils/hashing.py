"""File hashing utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path


def hash_file(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute SHA-256 hash of file contents.

    Reads file in chunks to handle large files efficiently.

    Args:
        file_path: Path to file to hash.
        chunk_size: Size of chunks to read (bytes). Default 8192.

    Returns:
        64-character hexadecimal string (SHA-256 digest).

    Raises:
        OSError: If file cannot be read.
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)

    return sha256.hexdigest()

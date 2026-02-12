from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path


def write_iandex(
    directory: Path, content: str, filename: str = ".aindex"
) -> Path:
    """Atomically write .aindex content to a file in the given directory.

    Uses temp-file-then-rename to prevent partial writes on failure.
    """
    target = directory / filename
    fd = -1
    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".aindex_tmp_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd = -1  # os.fdopen takes ownership of the fd
            f.write(content)
        os.replace(tmp_path, target)
        tmp_path = None  # successfully moved, no cleanup needed
    finally:
        if fd >= 0:
            os.close(fd)
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
    return target

"""IWH (I Was Here) module -- ephemeral inter-agent signal files."""

from __future__ import annotations

from lexibrarian.iwh.gitignore import ensure_iwh_gitignored
from lexibrarian.iwh.model import IWHFile, IWHScope
from lexibrarian.iwh.parser import parse_iwh
from lexibrarian.iwh.reader import consume_iwh, read_iwh
from lexibrarian.iwh.serializer import serialize_iwh
from lexibrarian.iwh.writer import write_iwh

__all__ = [
    "IWHFile",
    "IWHScope",
    "consume_iwh",
    "ensure_iwh_gitignored",
    "parse_iwh",
    "read_iwh",
    "serialize_iwh",
    "write_iwh",
]

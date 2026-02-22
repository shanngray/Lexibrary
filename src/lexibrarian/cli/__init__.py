"""CLI package for Lexibrarian — two entry points: lexi (agent) and lexictl (maintenance)."""

from __future__ import annotations

from lexibrarian.cli.lexi_app import lexi_app
from lexibrarian.cli.lexictl_app import lexictl_app

__all__ = ["lexi_app", "lexictl_app"]

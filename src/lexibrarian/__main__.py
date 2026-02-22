"""Entry point for running lexibrarian as a module (runs the agent-facing CLI)."""

from __future__ import annotations

from lexibrarian.cli import lexi_app

if __name__ == "__main__":
    lexi_app()

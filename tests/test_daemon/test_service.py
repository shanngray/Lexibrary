"""Tests for the DaemonService."""

from __future__ import annotations

import os
import signal
from pathlib import Path

from lexibrarian.daemon.service import _PID_FILENAME, DaemonService


def test_pid_file_created_on_start(tmp_path: Path) -> None:
    """PID file is written when the daemon starts."""
    svc = DaemonService(root=tmp_path, foreground=True)

    svc._write_pid_file()
    pid_path = tmp_path / _PID_FILENAME
    assert pid_path.exists()
    assert pid_path.read_text(encoding="utf-8") == str(os.getpid())

    # Cleanup
    svc._remove_pid_file()


def test_pid_file_removed_on_stop(tmp_path: Path) -> None:
    """PID file is removed when the daemon stops."""
    pid_path = tmp_path / _PID_FILENAME
    pid_path.write_text("12345", encoding="utf-8")

    svc = DaemonService(root=tmp_path, foreground=True)
    svc._remove_pid_file()

    assert not pid_path.exists()


def test_pid_file_removal_tolerates_missing(tmp_path: Path) -> None:
    """Removing a non-existent PID file does not raise."""
    svc = DaemonService(root=tmp_path, foreground=True)
    # Should not raise
    svc._remove_pid_file()


def test_signal_handler_triggers_shutdown(tmp_path: Path) -> None:
    """Signal handler sets the shutdown event."""
    svc = DaemonService(root=tmp_path, foreground=True)
    assert not svc._shutdown_event.is_set()

    svc._signal_handler(signal.SIGTERM, None)

    assert svc._shutdown_event.is_set()


def test_shutdown_completes_with_none_components(tmp_path: Path) -> None:
    """stop() completes without error when no components are initialized."""
    svc = DaemonService(root=tmp_path, foreground=True)
    assert svc._observer is None
    assert svc._debouncer is None
    assert svc._sweep is None

    # Should not raise
    svc.stop()


def test_background_mode_prints_message(tmp_path: Path) -> None:
    """Starting without foreground prints a not-yet-supported message."""
    svc = DaemonService(root=tmp_path, foreground=False)
    svc.start()
    # Service should return immediately without starting anything
    assert svc._observer is None

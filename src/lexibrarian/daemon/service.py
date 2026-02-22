"""Daemon service orchestrating watcher, debouncer, and periodic sweep."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import threading
from pathlib import Path
from types import FrameType

from rich.console import Console
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

from lexibrarian.config import LexibraryConfig, find_config_file, load_config
from lexibrarian.crawler import full_crawl
from lexibrarian.crawler.change_detector import ChangeDetector
from lexibrarian.daemon.debouncer import Debouncer
from lexibrarian.daemon.scheduler import PeriodicSweep
from lexibrarian.daemon.watcher import LexibrarianEventHandler
from lexibrarian.ignore import create_ignore_matcher
from lexibrarian.llm import create_llm_service
from lexibrarian.tokenizer import create_tokenizer

logger = logging.getLogger(__name__)
console = Console()

_PID_FILENAME = ".lexibrarian.pid"


class DaemonService:
    """Orchestrates file watching, debouncing, and periodic sweeps."""

    def __init__(self, root: Path, foreground: bool = True) -> None:
        self._root = root.resolve()
        self._foreground = foreground
        self._shutdown_event = threading.Event()
        self._observer: BaseObserver | None = None
        self._debouncer: Debouncer | None = None
        self._sweep: PeriodicSweep | None = None

    def start(self) -> None:
        """Start the daemon service."""
        if not self._foreground:
            console.print(
                "[yellow]Background mode is not yet supported.[/yellow]\n"
                "Use [cyan]lexictl daemon --foreground[/cyan] instead."
            )
            return

        # Load config
        config_path = find_config_file(self._root)
        config = load_config(config_path)

        # Configure logging to file
        log_path = self._root / config.output.log_filename
        logging.basicConfig(
            level=logging.INFO,
            filename=str(log_path),
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )

        # Build dependencies
        ignore_matcher = create_ignore_matcher(config, self._root)
        token_counter = create_tokenizer(config.tokenizer)
        llm_service = create_llm_service(config.llm)
        change_detector = ChangeDetector(self._root / config.output.cache_filename)
        change_detector.load()

        # Create debouncer
        self._debouncer = Debouncer(
            delay=config.daemon.debounce_seconds,
            callback=lambda dirs: self._incremental_reindex(
                config, ignore_matcher, token_counter, llm_service, change_detector
            ),
        )

        # Create periodic sweep
        self._sweep = PeriodicSweep(
            interval=float(config.daemon.sweep_interval_seconds),
            callback=lambda: self._full_sweep(
                config, ignore_matcher, token_counter, llm_service, change_detector
            ),
        )

        # Create watcher
        handler = LexibrarianEventHandler(
            debouncer=self._debouncer,
            ignore_matcher=ignore_matcher,
        )
        self._observer = Observer()
        self._observer.schedule(handler, str(self._root), recursive=True)

        # Write PID file
        self._write_pid_file()

        # Install signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Start components
        self._observer.start()
        self._sweep.start()

        pid = os.getpid()
        console.print(
            f"[green]Daemon running[/green] (PID {pid}) watching [cyan]{self._root}[/cyan]\n"
            "Press Ctrl+C to stop."
        )
        logger.info("Daemon started (PID %d) watching %s", pid, self._root)

        # Block until shutdown
        self._shutdown_event.wait()

        # Cleanup
        self.stop()

    def stop(self) -> None:
        """Gracefully stop all daemon components."""
        logger.info("Daemon shutting down...")

        if self._debouncer is not None:
            self._debouncer.cancel()

        if self._sweep is not None:
            self._sweep.stop()

        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5.0)

        self._remove_pid_file()

        console.print("[yellow]Daemon stopped.[/yellow]")
        logger.info("Daemon stopped.")

    def _signal_handler(self, signum: int, frame: FrameType | None) -> None:
        """Handle SIGTERM/SIGINT by triggering shutdown."""
        logger.info("Received signal %d, shutting down...", signum)
        self._shutdown_event.set()

    def _write_pid_file(self) -> None:
        """Write the current PID to the PID file."""
        pid_path = self._root / _PID_FILENAME
        pid_path.write_text(str(os.getpid()), encoding="utf-8")

    def _remove_pid_file(self) -> None:
        """Remove the PID file, tolerating if already gone."""
        pid_path = self._root / _PID_FILENAME
        pid_path.unlink(missing_ok=True)

    def _incremental_reindex(
        self,
        config: LexibraryConfig,
        ignore_matcher: object,
        token_counter: object,
        llm_service: object,
        change_detector: ChangeDetector,
    ) -> None:
        """Debounce callback: run full_crawl via asyncio.run()."""
        logger.info("Incremental re-index triggered")
        try:
            stats = asyncio.run(
                full_crawl(
                    root=self._root,
                    config=config,
                    ignore_matcher=ignore_matcher,  # type: ignore[arg-type]
                    token_counter=token_counter,  # type: ignore[arg-type]
                    llm_service=llm_service,  # type: ignore[arg-type]
                    change_detector=change_detector,
                )
            )
            logger.info(
                "Re-index complete: %d dirs, %d summarized, %d cached",
                stats.directories_indexed,
                stats.files_summarized,
                stats.files_cached,
            )
        except Exception:
            logger.exception("Incremental re-index failed")

    def _full_sweep(
        self,
        config: LexibraryConfig,
        ignore_matcher: object,
        token_counter: object,
        llm_service: object,
        change_detector: ChangeDetector,
    ) -> None:
        """Periodic sweep callback: run full_crawl via asyncio.run()."""
        logger.info("Periodic full sweep triggered")
        try:
            stats = asyncio.run(
                full_crawl(
                    root=self._root,
                    config=config,
                    ignore_matcher=ignore_matcher,  # type: ignore[arg-type]
                    token_counter=token_counter,  # type: ignore[arg-type]
                    llm_service=llm_service,  # type: ignore[arg-type]
                    change_detector=change_detector,
                )
            )
            logger.info(
                "Full sweep complete: %d dirs, %d summarized, %d cached",
                stats.directories_indexed,
                stats.files_summarized,
                stats.files_cached,
            )
        except Exception:
            logger.exception("Full sweep failed")

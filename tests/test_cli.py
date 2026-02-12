"""Tests for the CLI application."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from lexibrarian.cli import app

runner = CliRunner()


# -- Init command tests --


class TestInit:
    def test_init_creates_config(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 0
        config_path = tmp_path / "lexibrary.toml"
        assert config_path.exists()
        content = config_path.read_text(encoding="utf-8")
        assert 'provider = "anthropic"' in content
        assert 'model = "claude-sonnet-4-5-20250514"' in content

    def test_init_already_exists(self, tmp_path: Path) -> None:
        config_path = tmp_path / "lexibrary.toml"
        config_path.write_text("existing", encoding="utf-8")
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 1
        assert "already exists" in result.output
        # File should not be modified
        assert config_path.read_text(encoding="utf-8") == "existing"

    def test_init_provider_openai(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["init", str(tmp_path), "--provider", "openai"])
        assert result.exit_code == 0
        content = (tmp_path / "lexibrary.toml").read_text(encoding="utf-8")
        assert 'provider = "openai"' in content
        assert 'model = "gpt-4o-mini"' in content

    def test_init_creates_gitignore(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 0
        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text(encoding="utf-8")
        assert ".aindex" in content
        assert ".lexibrarian_cache.json" in content
        assert ".lexibrarian.log" in content
        assert ".lexibrarian.pid" in content

    def test_init_updates_gitignore(self, tmp_path: Path) -> None:
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules/\n", encoding="utf-8")
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 0
        content = gitignore.read_text(encoding="utf-8")
        # Original content preserved
        assert "node_modules/" in content
        # New entries added
        assert ".aindex" in content
        assert "# Lexibrary" in content

    def test_init_does_not_duplicate_gitignore_entries(self, tmp_path: Path) -> None:
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(
            ".aindex\n.lexibrarian_cache.json\n.lexibrarian.log\n.lexibrarian.pid\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 0
        content = gitignore.read_text(encoding="utf-8")
        # Should not have duplicate entries
        assert content.count(".aindex") == 1

    def test_init_shows_next_steps(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code == 0
        assert "Next steps" in result.output
        assert "lexibrary.toml" in result.output
        assert "lexi crawl" in result.output


# -- Crawl command tests --


class TestCrawl:
    def test_crawl_dry_run(self, tmp_path: Path) -> None:
        # Create a minimal config
        config_content = '[llm]\nprovider = "anthropic"\n'
        (tmp_path / "lexibrary.toml").write_text(config_content, encoding="utf-8")
        (tmp_path / "hello.py").write_text("print('hello')", encoding="utf-8")

        from lexibrarian.crawler.engine import CrawlStats

        mock_stats = CrawlStats(
            directories_indexed=1,
            files_summarized=1,
            files_cached=0,
            files_skipped=0,
            llm_calls=2,
            errors=0,
        )

        with (
            patch("lexibrarian.ignore.create_ignore_matcher"),
            patch("lexibrarian.tokenizer.create_tokenizer"),
            patch("lexibrarian.llm.create_llm_service"),
            patch("lexibrarian.crawler.change_detector.ChangeDetector"),
            patch(
                "lexibrarian.crawler.full_crawl", new_callable=AsyncMock, return_value=mock_stats
            ),
        ):
            result = runner.invoke(app, ["crawl", str(tmp_path), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run" in result.output


# -- Status command tests --


class TestStatus:
    def test_status_no_config(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["status", str(tmp_path)])
        assert result.exit_code == 0
        assert "not found (using defaults)" in result.output
        assert "Lexibrarian Status" in result.output

    def test_status_with_cache(self, tmp_path: Path) -> None:
        # Create a config file
        (tmp_path / "lexibrary.toml").write_text(
            '[llm]\nprovider = "anthropic"\n', encoding="utf-8"
        )

        # Create a cache file with entries
        cache_data = {
            "version": 1,
            "files": {
                str(tmp_path / "existing.py"): {
                    "hash": "abc123",
                    "tokens": 50,
                    "summary": "A test file",
                    "last_indexed": "2024-01-01T00:00:00",
                },
            },
        }
        (tmp_path / ".lexibrarian_cache.json").write_text(json.dumps(cache_data), encoding="utf-8")

        result = runner.invoke(app, ["status", str(tmp_path)])
        assert result.exit_code == 0
        assert "Lexibrarian Status" in result.output
        # The cached file doesn't exist, so it's stale
        assert "1" in result.output  # stale count

    def test_status_daemon_not_running(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["status", str(tmp_path)])
        assert result.exit_code == 0
        assert "not running" in result.output

    def test_status_stale_pid_file(self, tmp_path: Path) -> None:
        # Write a PID that doesn't correspond to a running process
        pid_path = tmp_path / ".lexibrarian.pid"
        pid_path.write_text("999999999", encoding="utf-8")
        result = runner.invoke(app, ["status", str(tmp_path)])
        assert result.exit_code == 0
        assert "stale PID file" in result.output


# -- Clean command tests --


class TestClean:
    def test_clean_removes_files(self, tmp_path: Path) -> None:
        # Create files to clean
        (tmp_path / ".aindex").write_text("index", encoding="utf-8")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / ".aindex").write_text("index", encoding="utf-8")
        (tmp_path / ".lexibrarian_cache.json").write_text("{}", encoding="utf-8")
        (tmp_path / ".lexibrarian.log").write_text("log", encoding="utf-8")

        result = runner.invoke(app, ["clean", str(tmp_path), "--yes"])
        assert result.exit_code == 0
        assert "Removed" in result.output
        assert not (tmp_path / ".aindex").exists()
        assert not (sub / ".aindex").exists()
        assert not (tmp_path / ".lexibrarian_cache.json").exists()
        assert not (tmp_path / ".lexibrarian.log").exists()

    def test_clean_nothing_to_clean(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["clean", str(tmp_path)])
        assert result.exit_code == 0
        assert "Nothing to clean" in result.output


# -- Daemon command tests --


class TestDaemon:
    def test_daemon_without_foreground(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["daemon", str(tmp_path)])
        assert result.exit_code == 0
        assert "not yet supported" in result.output

    def test_daemon_foreground_starts_service(self, tmp_path: Path) -> None:
        (tmp_path / "lexibrary.toml").write_text("", encoding="utf-8")

        with patch("lexibrarian.daemon.DaemonService") as mock_cls:
            mock_svc = mock_cls.return_value
            result = runner.invoke(app, ["daemon", str(tmp_path), "--foreground"])

        assert result.exit_code == 0
        mock_cls.assert_called_once()
        mock_svc.start.assert_called_once()


# -- Help / integration tests --


class TestHelp:
    def test_help_lists_all_commands(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "crawl" in result.output
        assert "status" in result.output
        assert "clean" in result.output
        assert "daemon" in result.output

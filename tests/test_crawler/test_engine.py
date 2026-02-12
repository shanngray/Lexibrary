"""Integration tests for the crawl engine."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import AsyncMock

import pathspec
import pytest

from lexibrarian.config.schema import LexibraryConfig
from lexibrarian.crawler.change_detector import ChangeDetector
from lexibrarian.crawler.engine import full_crawl
from lexibrarian.ignore.matcher import IgnoreMatcher
from lexibrarian.indexer.parser import parse_iandex
from lexibrarian.llm.service import FileSummaryResult, LLMService

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_project"


class FakeTokenCounter:
    """Minimal token counter for testing."""

    def count(self, text: str) -> int:
        return len(text.split())

    def count_file(self, path: Path) -> int:
        return self.count(path.read_text(encoding="utf-8", errors="replace"))

    @property
    def name(self) -> str:
        return "fake (word count)"


def _make_matcher(root: Path, patterns: list[str] | None = None) -> IgnoreMatcher:
    """Create a minimal IgnoreMatcher."""
    spec = pathspec.PathSpec.from_lines(
        "gitignore", patterns or [".aindex", ".lexibrarian_cache.json"]
    )
    return IgnoreMatcher(root, config_spec=spec, gitignore_specs=[])


def _make_llm_service() -> LLMService:
    """Create a mock LLM service."""
    service = AsyncMock(spec=LLMService)

    async def fake_summarize_file(request: object) -> FileSummaryResult:
        return FileSummaryResult(path=request.path, summary=f"Summary of {request.path.name}")  # type: ignore[union-attr]

    async def fake_summarize_batch(requests: list[object]) -> list[FileSummaryResult]:
        return [
            FileSummaryResult(path=r.path, summary=f"Summary of {r.path.name}")  # type: ignore[union-attr]
            for r in requests
        ]

    async def fake_summarize_dir(request: object) -> str:
        return f"Directory summary for {request.path.name}"  # type: ignore[union-attr]

    service.summarize_file = AsyncMock(side_effect=fake_summarize_file)
    service.summarize_files_batch = AsyncMock(side_effect=fake_summarize_batch)
    service.summarize_directory = AsyncMock(side_effect=fake_summarize_dir)
    return service


@pytest.fixture()
def project_tree(tmp_path: Path) -> Path:
    """Copy sample_project fixture to tmp_path for isolation."""
    dest = tmp_path / "project"
    shutil.copytree(FIXTURES, dest)
    return dest


@pytest.mark.asyncio()
async def test_full_crawl_creates_iandex_files(project_tree: Path) -> None:
    """Full crawl produces .aindex files in every non-ignored directory."""
    config = LexibraryConfig()
    matcher = _make_matcher(project_tree)
    token_counter = FakeTokenCounter()
    llm_service = _make_llm_service()
    cache_path = project_tree / config.output.cache_filename
    change_detector = ChangeDetector(cache_path)

    stats = await full_crawl(
        root=project_tree,
        config=config,
        ignore_matcher=matcher,
        token_counter=token_counter,
        llm_service=llm_service,
        change_detector=change_detector,
    )

    # .aindex should exist in every directory
    expected_dirs = [
        project_tree,
        project_tree / "src",
        project_tree / "src" / "utils",
        project_tree / "docs",
    ]
    for dirpath in expected_dirs:
        iandex = dirpath / ".aindex"
        assert iandex.exists(), f"Missing .aindex in {dirpath}"

    assert stats.directories_indexed > 0
    assert stats.errors == 0


@pytest.mark.asyncio()
async def test_bottom_up_processing_order(project_tree: Path) -> None:
    """Child directories are processed before parents."""
    config = LexibraryConfig()
    matcher = _make_matcher(project_tree)
    token_counter = FakeTokenCounter()
    llm_service = _make_llm_service()
    change_detector = ChangeDetector(project_tree / config.output.cache_filename)

    processed: list[str] = []

    def track_progress(current: int, total: int, dir_name: str) -> None:
        processed.append(dir_name)

    await full_crawl(
        root=project_tree,
        config=config,
        ignore_matcher=matcher,
        token_counter=token_counter,
        llm_service=llm_service,
        change_detector=change_detector,
        progress_callback=track_progress,
    )

    # Root should be last
    assert processed[-1] == "."
    # src/utils should come before src
    if "src/utils" in processed and "src" in processed:
        assert processed.index("src/utils") < processed.index("src")


@pytest.mark.asyncio()
async def test_incremental_crawl_uses_cache(project_tree: Path) -> None:
    """Second crawl on unchanged project reuses cached file summaries."""
    config = LexibraryConfig()
    matcher = _make_matcher(project_tree)
    token_counter = FakeTokenCounter()
    llm_service = _make_llm_service()
    cache_path = project_tree / config.output.cache_filename
    change_detector = ChangeDetector(cache_path)

    # First crawl
    stats1 = await full_crawl(
        root=project_tree,
        config=config,
        ignore_matcher=matcher,
        token_counter=token_counter,
        llm_service=llm_service,
        change_detector=change_detector,
    )
    assert stats1.files_summarized > 0

    # Second crawl with fresh service mock but loaded cache
    llm_service2 = _make_llm_service()
    change_detector2 = ChangeDetector(cache_path)
    change_detector2.load()

    stats2 = await full_crawl(
        root=project_tree,
        config=config,
        ignore_matcher=matcher,
        token_counter=token_counter,
        llm_service=llm_service2,
        change_detector=change_detector2,
    )

    # No file summarization LLM calls on second run
    assert stats2.files_summarized == 0
    assert stats2.files_cached > 0


@pytest.mark.asyncio()
async def test_dry_run_no_side_effects(project_tree: Path) -> None:
    """Dry run produces stats but no .aindex files or cache."""
    config = LexibraryConfig()
    matcher = _make_matcher(project_tree)
    token_counter = FakeTokenCounter()
    llm_service = _make_llm_service()
    cache_path = project_tree / config.output.cache_filename
    change_detector = ChangeDetector(cache_path)

    stats = await full_crawl(
        root=project_tree,
        config=config,
        ignore_matcher=matcher,
        token_counter=token_counter,
        llm_service=llm_service,
        change_detector=change_detector,
        dry_run=True,
    )

    assert stats.directories_indexed > 0
    # No .aindex files should exist
    iandex_files = list(project_tree.rglob(".aindex"))
    assert len(iandex_files) == 0
    # Cache should not be saved
    assert not cache_path.exists()


@pytest.mark.asyncio()
async def test_stats_accuracy(project_tree: Path) -> None:
    """CrawlStats accurately reflects crawl activity."""
    config = LexibraryConfig()
    matcher = _make_matcher(project_tree)
    token_counter = FakeTokenCounter()
    llm_service = _make_llm_service()
    change_detector = ChangeDetector(project_tree / config.output.cache_filename)

    stats = await full_crawl(
        root=project_tree,
        config=config,
        ignore_matcher=matcher,
        token_counter=token_counter,
        llm_service=llm_service,
        change_detector=change_detector,
    )

    # We have directories: project_tree, src, src/utils, docs = 4
    assert stats.directories_indexed == 4
    # Binary files: logo.png
    assert stats.files_skipped >= 1
    # LLM calls: file summary calls + 4 directory summary calls
    assert stats.llm_calls >= 4
    assert stats.errors == 0


@pytest.mark.asyncio()
async def test_binary_file_in_iandex(project_tree: Path) -> None:
    """Binary files appear in .aindex with tokens=0 and binary description."""
    config = LexibraryConfig()
    matcher = _make_matcher(project_tree)
    token_counter = FakeTokenCounter()
    llm_service = _make_llm_service()
    change_detector = ChangeDetector(project_tree / config.output.cache_filename)

    await full_crawl(
        root=project_tree,
        config=config,
        ignore_matcher=matcher,
        token_counter=token_counter,
        llm_service=llm_service,
        change_detector=change_detector,
    )

    root_iandex = parse_iandex(project_tree / ".aindex")
    assert root_iandex is not None

    png_entries = [f for f in root_iandex.files if f.name == "logo.png"]
    assert len(png_entries) == 1
    assert png_entries[0].tokens == 0
    assert "Binary" in png_entries[0].description or "binary" in png_entries[0].description

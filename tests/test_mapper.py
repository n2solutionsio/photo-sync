"""Tests for album-to-category mapping."""

from __future__ import annotations

from typing import TYPE_CHECKING

from photo_sync.config import load_config
from photo_sync.mapper import resolve_album, resolve_all_albums

if TYPE_CHECKING:
    from pathlib import Path


def test_explicit_mapping(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    result = resolve_album("Eagles vs Cowboys 9-7-25", cfg)
    assert result.category == "eagles"
    assert result.slug == "2025-09-07-cowboys"
    assert result.source == "explicit"


def test_pattern_matching(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    result = resolve_album("Eagles vs Giants 12-1-25", cfg)
    assert result.category == "eagles"
    assert result.source == "pattern"
    assert result.slug == "eagles-vs-giants-12-1-25"


def test_sailing_pattern(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    result = resolve_album("Sailing Trip June 2025", cfg)
    assert result.category == "sailing"
    assert result.source == "pattern"


def test_unmatched_album(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    result = resolve_album("Random Vacation", cfg)
    assert result.category == ""
    assert result.source == "unmatched"


def test_explicit_takes_priority(sample_config_path: Path) -> None:
    """Explicit mapping should win over pattern matching."""
    cfg = load_config(sample_config_path)
    result = resolve_album("Eagles vs Cowboys 9-7-25", cfg)
    assert result.source == "explicit"
    assert result.slug == "2025-09-07-cowboys"


def test_resolve_all(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    results = resolve_all_albums(["Eagles vs Cowboys 9-7-25", "Sailing Trip", "Random"], cfg)
    assert len(results) == 3
    assert results[0].source == "explicit"
    assert results[1].source == "pattern"
    assert results[2].source == "unmatched"

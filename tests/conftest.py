"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def sample_config_path() -> Path:
    return FIXTURES_DIR / "sample_config.toml"


@pytest.fixture()
def tmp_config(tmp_path: Path) -> Path:
    """Copy sample config to a temp directory and return the path."""
    src = FIXTURES_DIR / "sample_config.toml"
    dst = tmp_path / "config.toml"
    dst.write_text(src.read_text())
    return dst

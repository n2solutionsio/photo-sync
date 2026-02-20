"""Tests for config loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from photo_sync.config import Config, load_config, write_default_config
from photo_sync.exceptions import ConfigError, ConfigNotFoundError


def test_load_sample_config(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    assert isinstance(cfg, Config)
    assert cfg.repo_path == Path("/tmp/fake-repo").resolve()
    assert cfg.output_base == "src/assets/photos"
    assert cfg.categories == ["eagles", "sailing", "pets"]


def test_load_export_settings(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    assert cfg.export.max_width == 2048
    assert cfg.export.format == "jpg"
    assert cfg.export.quality == 85
    assert cfg.export.strip_gps is True


def test_load_git_settings(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    assert cfg.git.auto_commit is True
    assert cfg.git.auto_push is False


def test_load_album_mappings(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    assert "Eagles vs Cowboys 9-7-25" in cfg.album_mappings
    m = cfg.album_mappings["Eagles vs Cowboys 9-7-25"]
    assert m.category == "eagles"
    assert m.slug == "2025-09-07-cowboys"


def test_load_album_patterns(sample_config_path: Path) -> None:
    cfg = load_config(sample_config_path)
    assert cfg.album_patterns["^Eagles.*"] == "eagles"
    assert cfg.album_patterns["^Sail.*"] == "sailing"


def test_missing_config_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigNotFoundError, match="Config not found"):
        load_config(tmp_path / "nonexistent.toml")


def test_missing_repo_path_raises(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[general]\ncategories = ["a"]\n')
    with pytest.raises(ConfigError, match="repo_path"):
        load_config(cfg_path)


def test_bad_format_raises(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[general]\nrepo_path = "/tmp"\n\n[export]\nformat = "bmp"\n')
    with pytest.raises(ConfigError, match="Unsupported export format"):
        load_config(cfg_path)


def test_bad_quality_raises(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[general]\nrepo_path = "/tmp"\n\n[export]\nquality = 0\n')
    with pytest.raises(ConfigError, match="quality must be 1-100"):
        load_config(cfg_path)


def test_album_mapping_missing_category(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[general]\nrepo_path = "/tmp"\n\n[sync.albums."Foo"]\nslug = "foo"\n')
    with pytest.raises(ConfigError, match="missing 'category'"):
        load_config(cfg_path)


def test_write_default_config(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    write_default_config(cfg_path, "/tmp/repo", ["eagles", "sailing"])
    assert cfg_path.exists()
    cfg = load_config(cfg_path)
    assert cfg.repo_path == Path("/tmp/repo").resolve()
    assert cfg.categories == ["eagles", "sailing"]
    # Check permissions (owner read/write only)
    mode = cfg_path.stat().st_mode
    assert mode & 0o777 == 0o600

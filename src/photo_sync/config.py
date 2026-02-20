"""TOML config loading and validation."""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from photo_sync.exceptions import ConfigError, ConfigNotFoundError

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "photo-sync"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.toml"


@dataclass(frozen=True)
class ExportConfig:
    max_width: int = 2048
    format: str = "jpg"
    quality: int = 85
    strip_gps: bool = True


@dataclass(frozen=True)
class GitConfig:
    auto_commit: bool = True
    auto_push: bool = False
    commit_message: str = "gallery: sync {count} photos from {albums}"


@dataclass(frozen=True)
class AlbumMapping:
    category: str
    slug: str


@dataclass(frozen=True)
class Config:
    repo_path: Path
    output_base: str
    output_pattern: str
    categories: list[str]
    export: ExportConfig
    git: GitConfig
    album_mappings: dict[str, AlbumMapping] = field(default_factory=dict)
    album_patterns: dict[str, str] = field(default_factory=dict)

    @property
    def config_dir(self) -> Path:
        return DEFAULT_CONFIG_DIR

    @property
    def state_db_path(self) -> Path:
        return DEFAULT_CONFIG_DIR / "sync.db"


def _parse_export(raw: dict[str, Any]) -> ExportConfig:
    allowed = {"max_width", "format", "quality", "strip_gps"}
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigError(f"Unknown keys in [export]: {unknown}")
    fmt = raw.get("format", "jpg")
    if fmt not in ("jpg", "png", "webp"):
        raise ConfigError(f"Unsupported export format: {fmt!r}")
    quality = raw.get("quality", 85)
    if not (1 <= quality <= 100):
        raise ConfigError(f"Export quality must be 1-100, got {quality}")
    max_width = raw.get("max_width", 2048)
    if max_width < 1:
        raise ConfigError(f"max_width must be positive, got {max_width}")
    return ExportConfig(
        max_width=max_width,
        format=fmt,
        quality=quality,
        strip_gps=raw.get("strip_gps", True),
    )


def _parse_git(raw: dict[str, Any]) -> GitConfig:
    return GitConfig(
        auto_commit=raw.get("auto_commit", True),
        auto_push=raw.get("auto_push", False),
        commit_message=raw.get("commit_message", GitConfig.commit_message),
    )


def _parse_album_mappings(raw: dict[str, Any]) -> dict[str, AlbumMapping]:
    mappings: dict[str, AlbumMapping] = {}
    albums_raw = raw.get("albums", {})
    for album_name, mapping in albums_raw.items():
        if "category" not in mapping:
            raise ConfigError(f"Album mapping {album_name!r} missing 'category'")
        if "slug" not in mapping:
            raise ConfigError(f"Album mapping {album_name!r} missing 'slug'")
        mappings[album_name] = AlbumMapping(category=mapping["category"], slug=mapping["slug"])
    return mappings


def load_config(path: Path | None = None) -> Config:
    """Load and validate config from a TOML file."""
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise ConfigNotFoundError(
            f"Config not found at {config_path}. Run `photo-sync init` to create one."
        )
    text = config_path.read_text(encoding="utf-8")
    try:
        raw = tomllib.loads(text)
    except Exception as exc:
        raise ConfigError(f"Failed to parse config: {exc}") from exc

    general = raw.get("general", {})
    repo_path_str = general.get("repo_path")
    if not repo_path_str:
        raise ConfigError("Missing required key: general.repo_path")
    repo_path = Path(repo_path_str).expanduser().resolve()

    output_base = general.get("output_base", "src/assets/photos")
    output_pattern = general.get("output_pattern", "{category}/{album_slug}/{filename}")
    categories = general.get("categories", [])
    if not isinstance(categories, list):
        raise ConfigError("general.categories must be a list")

    export = _parse_export(raw.get("export", {}))
    git = _parse_git(raw.get("git", {}))

    sync_raw = raw.get("sync", {})
    album_mappings = _parse_album_mappings(sync_raw)
    album_patterns: dict[str, str] = sync_raw.get("patterns", {})

    return Config(
        repo_path=repo_path,
        output_base=output_base,
        output_pattern=output_pattern,
        categories=categories,
        export=export,
        git=git,
        album_mappings=album_mappings,
        album_patterns=album_patterns,
    )


def write_default_config(path: Path, repo_path: str, categories: list[str]) -> None:
    """Write a default config file with secure permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)

    cats_toml = ", ".join(f'"{c}"' for c in categories)
    content = f"""\
[general]
repo_path = "{repo_path}"
output_base = "src/assets/photos"
output_pattern = "{{category}}/{{album_slug}}/{{filename}}"
categories = [{cats_toml}]

[export]
max_width = 2048
format = "jpg"
quality = 85
strip_gps = true

[git]
auto_commit = true
auto_push = false
commit_message = "gallery: sync {{count}} photos from {{albums}}"

# Map specific albums to categories:
# [sync.albums."My Album Name"]
# category = "sailing"
# slug = "2025-summer-sail"

# Map album name patterns to categories:
# [sync.patterns]
# "^Eagles.*" = "eagles"
# "^Sail.*" = "sailing"
"""
    path.write_text(content, encoding="utf-8")
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600

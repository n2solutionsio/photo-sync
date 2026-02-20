"""Album to category mapping logic."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from photo_sync.path import slugify

if TYPE_CHECKING:
    from photo_sync.config import AlbumMapping, Config


@dataclass(frozen=True)
class ResolvedMapping:
    album_name: str
    category: str
    slug: str
    source: str  # "explicit", "pattern", or "unmatched"


def resolve_album(album_name: str, config: Config) -> ResolvedMapping:
    """Resolve an album name to a category and slug.

    Priority:
    1. Explicit album mapping in config
    2. Pattern match against album name
    3. Unmatched (no category)
    """
    # 1. Check explicit mappings
    if album_name in config.album_mappings:
        m: AlbumMapping = config.album_mappings[album_name]
        return ResolvedMapping(
            album_name=album_name,
            category=m.category,
            slug=m.slug,
            source="explicit",
        )

    # 2. Check patterns
    for pattern, category in config.album_patterns.items():
        if re.match(pattern, album_name):
            return ResolvedMapping(
                album_name=album_name,
                category=category,
                slug=slugify(album_name),
                source="pattern",
            )

    # 3. Unmatched
    return ResolvedMapping(
        album_name=album_name,
        category="",
        slug=slugify(album_name),
        source="unmatched",
    )


def resolve_all_albums(album_names: list[str], config: Config) -> list[ResolvedMapping]:
    """Resolve all album names, returning mappings for each."""
    return [resolve_album(name, config) for name in album_names]

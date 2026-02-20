"""Output path template rendering with safety checks."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from photo_sync.exceptions import PathError

if TYPE_CHECKING:
    from pathlib import Path


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def render_output_path(
    *,
    pattern: str,
    category: str,
    album_slug: str,
    filename: str,
) -> str:
    """Render an output path from a template pattern.

    Raises PathError if the result would escape the output directory.
    """
    rendered = pattern.format(
        category=category,
        album_slug=album_slug,
        filename=filename,
    )
    # Prevent path traversal
    if ".." in rendered:
        raise PathError(f"Path traversal detected in rendered path: {rendered!r}")
    return rendered


def resolve_safe_path(base: Path, relative: str) -> Path:
    """Resolve a relative path within a base directory safely.

    Raises PathError if the resolved path escapes the base directory.
    """
    resolved = (base / relative).resolve()
    base_resolved = base.resolve()
    if not resolved.is_relative_to(base_resolved):
        raise PathError(f"Path {resolved} escapes base directory {base_resolved}")
    return resolved

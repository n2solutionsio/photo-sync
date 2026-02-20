"""Tests for path rendering and safety."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from photo_sync.exceptions import PathError
from photo_sync.path import render_output_path, resolve_safe_path, slugify

if TYPE_CHECKING:
    from pathlib import Path


class TestSlugify:
    def test_basic(self) -> None:
        assert slugify("Eagles vs Cowboys 9-7-25") == "eagles-vs-cowboys-9-7-25"

    def test_special_chars(self) -> None:
        assert slugify("Rhaegar's Photos!") == "rhaegars-photos"

    def test_spaces_and_underscores(self) -> None:
        assert slugify("my  album__name") == "my-album-name"

    def test_already_clean(self) -> None:
        assert slugify("clean-slug") == "clean-slug"

    def test_empty(self) -> None:
        assert slugify("") == ""


class TestRenderOutputPath:
    def test_basic(self) -> None:
        result = render_output_path(
            pattern="{category}/{album_slug}/{filename}",
            category="eagles",
            album_slug="2025-09-07-cowboys",
            filename="IMG_0001.jpg",
        )
        assert result == "eagles/2025-09-07-cowboys/IMG_0001.jpg"

    def test_path_traversal_blocked(self) -> None:
        with pytest.raises(PathError, match="Path traversal"):
            render_output_path(
                pattern="{category}/{album_slug}/{filename}",
                category="../etc",
                album_slug="evil",
                filename="passwd",
            )


class TestResolveSafePath:
    def test_valid(self, tmp_path: Path) -> None:
        result = resolve_safe_path(tmp_path, "eagles/album/photo.jpg")
        assert result.is_relative_to(tmp_path)

    def test_traversal_blocked(self, tmp_path: Path) -> None:
        with pytest.raises(PathError, match="escapes base directory"):
            resolve_safe_path(tmp_path, "../../etc/passwd")

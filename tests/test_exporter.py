"""Tests for photo export functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PIL import Image

from photo_sync.exporter import compute_checksum, export_photo

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def sample_image(tmp_path: Path) -> Path:
    """Create a simple test image."""
    img_path = tmp_path / "source" / "test.jpg"
    img_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (4000, 3000), color="blue")
    img.save(img_path, format="JPEG")
    img.close()
    return img_path


@pytest.fixture()
def small_image(tmp_path: Path) -> Path:
    """Create a small test image (below max_width)."""
    img_path = tmp_path / "source" / "small.jpg"
    img_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (800, 600), color="red")
    img.save(img_path, format="JPEG")
    img.close()
    return img_path


class TestExportPhoto:
    def test_basic_export(self, sample_image: Path, tmp_path: Path) -> None:
        dest = tmp_path / "output" / "photo.jpg"
        checksum = export_photo(source_path=sample_image, dest_path=dest)
        assert dest.exists()
        assert len(checksum) == 64  # SHA-256 hex

    def test_resize(self, sample_image: Path, tmp_path: Path) -> None:
        dest = tmp_path / "output" / "photo.jpg"
        export_photo(source_path=sample_image, dest_path=dest, max_width=1024)
        img = Image.open(dest)
        assert img.width == 1024
        assert img.height == 768  # Aspect ratio preserved
        img.close()

    def test_no_resize_when_small(self, small_image: Path, tmp_path: Path) -> None:
        dest = tmp_path / "output" / "photo.jpg"
        export_photo(source_path=small_image, dest_path=dest, max_width=2048)
        img = Image.open(dest)
        assert img.width == 800
        img.close()

    def test_format_conversion_png(self, sample_image: Path, tmp_path: Path) -> None:
        dest = tmp_path / "output" / "photo.png"
        export_photo(source_path=sample_image, dest_path=dest, output_format="png", max_width=512)
        assert dest.exists()
        img = Image.open(dest)
        assert img.format == "PNG"
        img.close()

    def test_format_conversion_webp(self, sample_image: Path, tmp_path: Path) -> None:
        dest = tmp_path / "output" / "photo.webp"
        export_photo(source_path=sample_image, dest_path=dest, output_format="webp", max_width=512)
        assert dest.exists()
        img = Image.open(dest)
        assert img.format == "WEBP"
        img.close()

    def test_creates_parent_dirs(self, sample_image: Path, tmp_path: Path) -> None:
        dest = tmp_path / "deep" / "nested" / "dir" / "photo.jpg"
        export_photo(source_path=sample_image, dest_path=dest)
        assert dest.exists()

    def test_rgba_to_jpeg(self, tmp_path: Path) -> None:
        """RGBA images should be converted to RGB for JPEG output."""
        src = tmp_path / "source" / "rgba.png"
        src.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img.save(src, format="PNG")
        img.close()

        dest = tmp_path / "output" / "photo.jpg"
        export_photo(source_path=src, dest_path=dest, output_format="jpg")
        assert dest.exists()


class TestComputeChecksum:
    def test_deterministic(self, sample_image: Path) -> None:
        c1 = compute_checksum(sample_image)
        c2 = compute_checksum(sample_image)
        assert c1 == c2

    def test_different_files(self, sample_image: Path, small_image: Path) -> None:
        c1 = compute_checksum(sample_image)
        c2 = compute_checksum(small_image)
        assert c1 != c2

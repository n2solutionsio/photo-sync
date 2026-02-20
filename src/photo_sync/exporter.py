"""Photo export: resize, format conversion, EXIF stripping via Pillow."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from PIL import Image
from PIL.ExifTags import Base as ExifBase

from photo_sync.exceptions import ExportError

if TYPE_CHECKING:
    from pathlib import Path

# GPS-related EXIF tags to strip
_GPS_TAGS = {
    ExifBase.GPSInfo,
}


def _strip_gps_exif(img: Image.Image) -> Image.Image:
    """Remove GPS data from image EXIF while preserving other metadata."""
    exif = img.getexif()
    for tag in _GPS_TAGS:
        exif.pop(tag, None)
    # Also strip from IFD (sub-EXIF)
    for ifd_key in list(exif.get_ifd(0x8769)):
        if ifd_key in _GPS_TAGS:
            del exif.get_ifd(0x8769)[ifd_key]
    img.info["exif"] = exif.tobytes()
    return img


def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def export_photo(
    *,
    source_path: Path,
    dest_path: Path,
    max_width: int = 2048,
    output_format: str = "jpg",
    quality: int = 85,
    strip_gps: bool = True,
) -> str:
    """Export a photo with resize and optional GPS stripping.

    Returns the SHA-256 checksum of the exported file.
    """
    try:
        img: Image.Image = Image.open(source_path)
    except Exception as exc:
        raise ExportError(f"Failed to open {source_path}: {exc}") from exc

    try:
        # Resize if wider than max_width, preserving aspect ratio
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Strip GPS if requested
        if strip_gps:
            import contextlib

            with contextlib.suppress(Exception):
                _strip_gps_exif(img)

        # Ensure output directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Map format names to Pillow format strings
        format_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}
        pil_format = format_map.get(output_format.lower())
        if not pil_format:
            raise ExportError(f"Unsupported format: {output_format!r}")

        save_kwargs: dict[str, object] = {}
        if pil_format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
        if pil_format == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.save(dest_path, format=pil_format, **save_kwargs)
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError(f"Failed to export {source_path} -> {dest_path}: {exc}") from exc
    finally:
        img.close()

    return compute_checksum(dest_path)

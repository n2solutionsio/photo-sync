"""Apple Photos provider via osxphotos."""

from __future__ import annotations

from typing import TYPE_CHECKING

from photo_sync.exceptions import AlbumNotFoundError, ProviderError
from photo_sync.provider import AlbumInfo, PhotoInfo, PhotoProvider

if TYPE_CHECKING:
    import osxphotos


class ApplePhotosProvider(PhotoProvider):
    """Reads albums and photos from the macOS Photos library via osxphotos."""

    def __init__(self, db_path: str | None = None) -> None:
        try:
            import osxphotos as _osxphotos

            self._photosdb: osxphotos.PhotosDB = _osxphotos.PhotosDB(dbfile=db_path)
        except ImportError as exc:
            raise ProviderError(
                "osxphotos is required for Apple Photos. Install with: pip install osxphotos"
            ) from exc
        except Exception as exc:
            raise ProviderError(f"Failed to open Photos library: {exc}") from exc

    def list_albums(self) -> list[AlbumInfo]:
        album_names: set[str] = set()
        albums: list[AlbumInfo] = []
        for photo in self._photosdb.photos():
            for album in photo.albums:
                if album not in album_names:
                    album_names.add(album)
        # Get counts per album
        counts: dict[str, int] = {}
        for photo in self._photosdb.photos():
            for album in photo.albums:
                counts[album] = counts.get(album, 0) + 1
        for name in sorted(album_names):
            albums.append(AlbumInfo(name=name, photo_count=counts.get(name, 0)))
        return albums

    def get_photos(self, album_name: str) -> list[PhotoInfo]:
        photos = self._photosdb.photos(albums=[album_name])
        if not photos:
            # Check if album exists but is empty vs doesn't exist
            all_albums = {a.name for a in self.list_albums()}
            if album_name not in all_albums:
                raise AlbumNotFoundError(f"Album not found: {album_name!r}")
            return []

        result: list[PhotoInfo] = []
        for photo in photos:
            if photo.path is None:
                continue  # Skip photos without a path (e.g. iCloud-only)
            result.append(
                PhotoInfo(
                    uuid=photo.uuid,
                    filename=photo.original_filename,
                    original_path=photo.path,
                    album_name=album_name,
                    date_taken=photo.date.isoformat() if photo.date else None,
                    width=photo.width,
                    height=photo.height,
                )
            )
        return result

    def get_photo_path(self, photo: PhotoInfo) -> str:
        return photo.original_path

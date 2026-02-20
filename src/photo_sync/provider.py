"""Abstract base class for photo providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PhotoInfo:
    """Metadata for a single photo from a provider."""

    uuid: str
    filename: str
    original_path: str
    album_name: str
    date_taken: str | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class AlbumInfo:
    """Metadata for an album from a provider."""

    name: str
    photo_count: int


class PhotoProvider(ABC):
    """Abstract interface for photo source providers.

    Implementations must provide methods to list albums and retrieve
    photos from a specific album. This allows the sync engine to work
    with any photo source (Apple Photos, Google Photos, local folders, etc).
    """

    @abstractmethod
    def list_albums(self) -> list[AlbumInfo]:
        """Return all albums available from this provider."""

    @abstractmethod
    def get_photos(self, album_name: str) -> list[PhotoInfo]:
        """Return all photos in the named album.

        Raises AlbumNotFoundError if the album does not exist.
        """

    @abstractmethod
    def get_photo_path(self, photo: PhotoInfo) -> str:
        """Return the filesystem path to the original photo file.

        This is the path that the exporter will read from.
        """

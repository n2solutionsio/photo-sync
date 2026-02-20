"""Custom exception hierarchy for photo-sync."""


class PhotoSyncError(Exception):
    """Base exception for all photo-sync errors."""


class ConfigError(PhotoSyncError):
    """Configuration file is missing, invalid, or has bad values."""


class ConfigNotFoundError(ConfigError):
    """Config file does not exist. Run `photo-sync init` first."""


class ProviderError(PhotoSyncError):
    """Error communicating with a photo provider."""


class AlbumNotFoundError(ProviderError):
    """Requested album does not exist in the photo library."""


class ExportError(PhotoSyncError):
    """Error during photo export (resize, format conversion, write)."""


class GitError(PhotoSyncError):
    """Error during a git operation."""


class StateError(PhotoSyncError):
    """Error reading or writing the sync state database."""


class PathError(PhotoSyncError):
    """Error resolving or validating an output path (e.g. path traversal)."""

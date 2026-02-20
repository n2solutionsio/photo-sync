# photo-sync

Sync photos from Apple Photos (and more) to static site galleries.

## Features

- **Provider-agnostic**: Abstract provider interface — Apple Photos first, Google Photos / Lightroom / local folders can be added
- **Album-to-category mapping**: Map Apple Photos albums to gallery categories via config or regex patterns
- **Incremental sync**: SQLite state DB tracks what's been synced — only new/changed photos are exported
- **Image optimization**: Resize, format convert, and strip GPS EXIF data via Pillow
- **Git integration**: Auto-commit and push synced photos
- **Rich CLI**: Tables, progress bars, dry-run previews

## Installation

```bash
pip install git+https://github.com/n2solutionsio/photo-sync.git
```

Or for development:

```bash
git clone https://github.com/n2solutionsio/photo-sync.git
cd photo-sync
pip install -e ".[dev]"
```

## Quick Start

```bash
# 1. Create config
photo-sync init

# 2. See your albums
photo-sync list-albums

# 3. Preview what would sync
photo-sync sync --dry-run

# 4. Sync photos
photo-sync sync

# 5. Push to remote
photo-sync push
```

## Configuration

Config lives at `~/.config/photo-sync/config.toml`:

```toml
[general]
repo_path = "/path/to/your/static-site"
output_base = "src/assets/photos"
output_pattern = "{category}/{album_slug}/{filename}"
categories = ["eagles", "sailing", "pets"]

[export]
max_width = 2048
format = "jpg"
quality = 85
strip_gps = true    # Strip GPS EXIF by default

[git]
auto_commit = true
auto_push = false
commit_message = "gallery: sync {count} photos from {albums}"

# Explicit album mappings
[sync.albums."Eagles vs Cowboys 9-7-25"]
category = "eagles"
slug = "2025-09-07-cowboys"

# Pattern-based mappings (regex)
[sync.patterns]
"^Eagles.*" = "eagles"
"^Sail.*" = "sailing"
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `photo-sync init` | Interactive config setup |
| `photo-sync list-albums` | List albums and mapping status |
| `photo-sync sync` | Export photos to repo |
| `photo-sync sync --dry-run` | Preview without exporting |
| `photo-sync sync --album "Name"` | Sync specific album |
| `photo-sync sync --category eagles` | Sync all albums in category |
| `photo-sync sync --force` | Re-export already synced photos |
| `photo-sync status` | Show sync state |
| `photo-sync push` | Git push synced photos |

## Adding Providers

photo-sync uses an abstract `PhotoProvider` interface. To add a new provider:

1. Create `src/photo_sync/providers/your_provider.py`
2. Implement `PhotoProvider` with `list_albums()`, `get_photos()`, and `get_photo_path()`
3. Register it in the CLI

See `providers/apple.py` for a reference implementation.

## Development

```bash
pip install -e ".[dev]"
ruff check src/ tests/
ruff format src/ tests/
mypy src/
pytest
```

## License

MIT

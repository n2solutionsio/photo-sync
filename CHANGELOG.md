# Changelog

## 0.1.0 (2026-02-20)

### Added

- Initial release
- Apple Photos provider via osxphotos
- Album-to-category mapping (explicit + regex patterns)
- Pillow-based image export with resize, format conversion, GPS stripping
- SQLite sync state tracking for incremental sync
- Git integration (auto-commit, push)
- CLI: `init`, `list-albums`, `sync`, `status`, `push`
- Rich terminal output with tables and progress bars
- `--dry-run` mode for sync previews

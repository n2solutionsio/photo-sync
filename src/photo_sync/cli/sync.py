"""Core sync command: export photos from Apple Photos to repo."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from photo_sync.config import Config, load_config
from photo_sync.exceptions import AlbumNotFoundError, ExportError, PhotoSyncError
from photo_sync.exporter import compute_checksum, export_photo
from photo_sync.git import git_add, git_commit, is_git_repo
from photo_sync.mapper import resolve_album
from photo_sync.path import render_output_path, resolve_safe_path
from photo_sync.providers.apple import ApplePhotosProvider
from photo_sync.state import SyncState

if TYPE_CHECKING:
    from photo_sync.provider import PhotoInfo

console = Console()


def _sync_photo(
    *,
    photo: PhotoInfo,
    category: str,
    album_slug: str,
    cfg: Config,
    state: SyncState,
    dry_run: bool,
    force: bool,
) -> tuple[str, bool]:
    """Sync a single photo. Returns (output_path, was_exported)."""

    relative_path = render_output_path(
        pattern=cfg.output_pattern,
        category=category,
        album_slug=album_slug,
        filename=photo.filename,
    )
    output_base = cfg.repo_path / cfg.output_base
    dest_path = resolve_safe_path(output_base, relative_path)

    # Check if already synced (unless forcing)
    if not force and state.is_synced(photo.uuid, photo.album_name):
        old_checksum = state.get_checksum(photo.uuid, photo.album_name)
        source_checksum = compute_checksum(Path(photo.original_path))
        if old_checksum == source_checksum:
            return relative_path, False

    if dry_run:
        return relative_path, True

    checksum = export_photo(
        source_path=Path(photo.original_path),
        dest_path=dest_path,
        max_width=cfg.export.max_width,
        output_format=cfg.export.format,
        quality=cfg.export.quality,
        strip_gps=cfg.export.strip_gps,
    )

    state.record_sync(
        photo_uuid=photo.uuid,
        album_name=photo.album_name,
        category=category,
        output_path=relative_path,
        checksum=checksum,
    )

    return relative_path, True


@click.command()
@click.option("--dry-run", is_flag=True, help="Preview without exporting")
@click.option("--album", multiple=True, help="Sync specific album(s) only")
@click.option("--category", help="Sync all albums mapped to this category")
@click.option("--force", is_flag=True, help="Re-export even if already synced")
@click.option("--no-commit", is_flag=True, help="Skip git commit after sync")
def sync(
    dry_run: bool,
    album: tuple[str, ...],
    category: str | None,
    force: bool,
    no_commit: bool,
) -> None:
    """Export photos from Apple Photos to your static site repo."""
    cfg = load_config()

    if not cfg.repo_path.exists():
        console.print(f"[red]Repo path does not exist: {cfg.repo_path}[/red]")
        raise SystemExit(1)

    if not is_git_repo(cfg.repo_path):
        console.print(f"[red]Not a git repo: {cfg.repo_path}[/red]")
        raise SystemExit(1)

    provider = ApplePhotosProvider()
    all_albums = provider.list_albums()

    # Determine which albums to sync
    if album:
        target_albums = list(album)
    elif category:
        target_albums = []
        for a in all_albums:
            mapping = resolve_album(a.name, cfg)
            if mapping.category == category:
                target_albums.append(a.name)
        if not target_albums:
            console.print(f"[yellow]No albums mapped to category: {category}[/yellow]")
            return
    else:
        # Sync all mapped albums
        target_albums = []
        for a in all_albums:
            mapping = resolve_album(a.name, cfg)
            if mapping.source != "unmatched":
                target_albums.append(a.name)

    if not target_albums:
        console.print("[yellow]No albums to sync. Set up mappings first.[/yellow]")
        return

    state = SyncState(cfg.state_db_path)
    exported_paths: list[Path] = []
    exported_count = 0
    skipped_count = 0
    error_count = 0

    if dry_run:
        dry_table = Table(title="Dry Run Preview")
        dry_table.add_column("Album")
        dry_table.add_column("Photo")
        dry_table.add_column("Category")
        dry_table.add_column("Output Path")
        dry_table.add_column("Action")

    try:
        for album_name in target_albums:
            mapping = resolve_album(album_name, cfg)
            if not mapping.category:
                console.print(f"[yellow]Skipping unmapped album: {album_name}[/yellow]")
                continue

            try:
                photos = provider.get_photos(album_name)
            except AlbumNotFoundError:
                console.print(f"[red]Album not found: {album_name}[/red]")
                error_count += 1
                continue

            if not photos:
                console.print(f"[dim]No photos in album: {album_name}[/dim]")
                continue

            if not dry_run:
                with Progress() as progress:
                    task = progress.add_task(f"Syncing {album_name}...", total=len(photos))
                    for photo in photos:
                        try:
                            rel_path, was_exported = _sync_photo(
                                photo=photo,
                                category=mapping.category,
                                album_slug=mapping.slug,
                                cfg=cfg,
                                state=state,
                                dry_run=False,
                                force=force,
                            )
                            if was_exported:
                                output_base = cfg.repo_path / cfg.output_base
                                exported_paths.append(resolve_safe_path(output_base, rel_path))
                                exported_count += 1
                            else:
                                skipped_count += 1
                        except (ExportError, PhotoSyncError) as exc:
                            console.print(f"[red]Error exporting {photo.filename}: {exc}[/red]")
                            error_count += 1
                        progress.advance(task)
            else:
                for photo in photos:
                    try:
                        rel_path, would_export = _sync_photo(
                            photo=photo,
                            category=mapping.category,
                            album_slug=mapping.slug,
                            cfg=cfg,
                            state=state,
                            dry_run=True,
                            force=force,
                        )
                        action = "[green]export[/green]" if would_export else "[dim]skip[/dim]"
                        if would_export:
                            exported_count += 1
                        else:
                            skipped_count += 1
                        dry_table.add_row(
                            album_name,
                            photo.filename,
                            mapping.category,
                            rel_path,
                            action,
                        )
                    except PhotoSyncError as exc:
                        console.print(f"[red]Error: {exc}[/red]")
                        error_count += 1

        if dry_run:
            console.print(dry_table)

        # Summary
        console.print()
        console.print(f"[bold]Exported:[/bold] {exported_count}")
        console.print(f"[bold]Skipped:[/bold] {skipped_count}")
        if error_count:
            console.print(f"[bold red]Errors:[/bold red] {error_count}")

        # Git commit
        if not dry_run and exported_paths and not no_commit and cfg.git.auto_commit:
            album_names = ", ".join(target_albums[:3])
            if len(target_albums) > 3:
                album_names += f" (+{len(target_albums) - 3} more)"
            message = cfg.git.commit_message.format(count=exported_count, albums=album_names)
            git_add(exported_paths, cwd=cfg.repo_path)
            git_commit(message, cwd=cfg.repo_path)
            console.print(f"\n[green]Committed: {message}[/green]")

    finally:
        state.close()

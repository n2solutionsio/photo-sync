"""List Apple Photos albums and their mapping status."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from photo_sync.config import load_config
from photo_sync.mapper import resolve_all_albums
from photo_sync.providers.apple import ApplePhotosProvider

console = Console()


@click.command("list-albums")
@click.option("--unmapped-only", is_flag=True, help="Show only unmapped albums")
def list_albums(unmapped_only: bool) -> None:
    """List Apple Photos albums and their mapping status."""
    cfg = load_config()
    provider = ApplePhotosProvider()
    albums = provider.list_albums()

    if not albums:
        console.print("[yellow]No albums found in Photos library.[/yellow]")
        return

    mappings = resolve_all_albums([a.name for a in albums], cfg)

    table = Table(title="Apple Photos Albums")
    table.add_column("Album", style="bold")
    table.add_column("Photos", justify="right")
    table.add_column("Category", style="cyan")
    table.add_column("Slug")
    table.add_column("Source", style="dim")

    for album, mapping in zip(albums, mappings, strict=False):
        if unmapped_only and mapping.source != "unmatched":
            continue
        cat_display = mapping.category or "[dim]—[/dim]"
        source_display = (
            mapping.source if mapping.source != "unmatched" else "[yellow]unmatched[/yellow]"
        )
        table.add_row(
            album.name,
            str(album.photo_count),
            cat_display,
            mapping.slug,
            source_display,
        )

    console.print(table)

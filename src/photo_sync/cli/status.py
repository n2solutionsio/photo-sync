"""Show sync state."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from photo_sync.config import load_config
from photo_sync.state import SyncState

console = Console()


@click.command()
@click.option("--category", help="Filter by category")
def status(category: str | None) -> None:
    """Show synced photo state."""
    cfg = load_config()

    if not cfg.state_db_path.exists():
        console.print("[yellow]No sync database found. Run `photo-sync sync` first.[/yellow]")
        return

    state = SyncState(cfg.state_db_path)
    try:
        records = state.get_records_by_category(category) if category else state.get_all_records()

        if not records:
            console.print("[yellow]No synced photos found.[/yellow]")
            return

        table = Table(title=f"Synced Photos ({len(records)} total)")
        table.add_column("Album", style="bold")
        table.add_column("Photo UUID", style="dim", max_width=12)
        table.add_column("Category", style="cyan")
        table.add_column("Output Path")
        table.add_column("Synced At", style="dim")

        for record in records:
            table.add_row(
                record.album_name,
                record.photo_uuid[:12],
                record.category,
                record.output_path,
                record.synced_at[:19],
            )

        console.print(table)

        # Category summary
        cats: dict[str, int] = {}
        all_records = state.get_all_records()
        for r in all_records:
            cats[r.category] = cats.get(r.category, 0) + 1

        console.print()
        summary = Table(title="Category Summary")
        summary.add_column("Category")
        summary.add_column("Count", justify="right")
        for cat, count in sorted(cats.items()):
            summary.add_row(cat, str(count))
        console.print(summary)

    finally:
        state.close()

"""Interactive config setup wizard."""

from __future__ import annotations

import click
from rich.console import Console

from photo_sync.config import DEFAULT_CONFIG_PATH, write_default_config

console = Console()


@click.command()
@click.option(
    "--config",
    type=click.Path(),
    default=None,
    help="Config file path (default: ~/.config/photo-sync/config.toml)",
)
def init(config: str | None) -> None:
    """Interactive config setup wizard."""
    from pathlib import Path

    config_path = Path(config) if config else DEFAULT_CONFIG_PATH

    if config_path.exists() and not click.confirm(
        f"Config already exists at {config_path}. Overwrite?"
    ):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    console.print("\n[bold]photo-sync config setup[/bold]\n")

    repo_path = click.prompt(
        "Path to your static site repo",
        type=str,
    )
    repo_path = str(Path(repo_path).expanduser().resolve())

    categories_str = click.prompt(
        "Categories (comma-separated)",
        default="eagles, phillies, sailing, motorcycles, pets, events",
        type=str,
    )
    categories = [c.strip() for c in categories_str.split(",") if c.strip()]

    write_default_config(config_path, repo_path, categories)
    console.print(f"\n[green]Config written to {config_path}[/green]")
    console.print("Edit the file to set up album mappings and patterns.")

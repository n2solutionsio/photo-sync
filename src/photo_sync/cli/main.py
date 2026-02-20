"""Click CLI entry point."""

from __future__ import annotations

import click

from photo_sync.__about__ import __version__


@click.group()
@click.version_option(version=__version__, prog_name="photo-sync")
def cli() -> None:
    """Sync photos from Apple Photos to your static site gallery."""


# Import subcommands to register them
from photo_sync.cli.init import init  # noqa: E402
from photo_sync.cli.list_albums import list_albums  # noqa: E402
from photo_sync.cli.push import push  # noqa: E402
from photo_sync.cli.status import status  # noqa: E402
from photo_sync.cli.sync import sync  # noqa: E402

cli.add_command(init)
cli.add_command(list_albums)
cli.add_command(sync)
cli.add_command(status)
cli.add_command(push)

"""Git push command."""

from __future__ import annotations

import click
from rich.console import Console

from photo_sync.config import load_config
from photo_sync.exceptions import GitError
from photo_sync.git import git_current_branch, git_push, git_status, is_git_repo

console = Console()


@click.command()
@click.option("--remote", default="origin", help="Git remote name")
def push(remote: str) -> None:
    """Push synced photos to the remote repository."""
    cfg = load_config()

    if not is_git_repo(cfg.repo_path):
        console.print(f"[red]Not a git repo: {cfg.repo_path}[/red]")
        raise SystemExit(1)

    # Check for uncommitted changes
    status_output = git_status(cfg.repo_path)
    if status_output:
        console.print("[yellow]Warning: uncommitted changes in repo:[/yellow]")
        console.print(status_output)
        if not click.confirm("Push anyway?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    branch = git_current_branch(cfg.repo_path)
    console.print(f"Pushing [bold]{branch}[/bold] to [bold]{remote}[/bold]...")

    try:
        git_push(cfg.repo_path, remote=remote, branch=branch)
        console.print("[green]Pushed successfully.[/green]")
    except GitError as exc:
        console.print(f"[red]Push failed: {exc}[/red]")
        raise SystemExit(1) from exc

"""Git operations via subprocess (no shell=True)."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from photo_sync.exceptions import GitError

if TYPE_CHECKING:
    from pathlib import Path


def _run_git(args: list[str], cwd: Path) -> str:
    """Run a git command and return stdout.

    Uses list-form subprocess to avoid shell injection.
    """
    cmd = ["git", *args]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise GitError(
            f"git {' '.join(args)} failed (exit {exc.returncode}): {exc.stderr.strip()}"
        ) from exc
    except FileNotFoundError as exc:
        raise GitError("git not found on PATH") from exc
    return result.stdout.strip()


def is_git_repo(path: Path) -> bool:
    """Check if the given path is inside a git repository."""
    try:
        _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
        return True
    except GitError:
        return False


def git_add(paths: list[Path], cwd: Path) -> None:
    """Stage files for commit."""
    if not paths:
        return
    str_paths = [str(p) for p in paths]
    _run_git(["add", "--", *str_paths], cwd=cwd)


def git_commit(message: str, cwd: Path) -> str:
    """Create a commit and return the short hash."""
    output = _run_git(["commit", "-m", message], cwd=cwd)
    return output


def git_push(cwd: Path, remote: str = "origin", branch: str | None = None) -> str:
    """Push to remote."""
    args = ["push", remote]
    if branch:
        args.append(branch)
    return _run_git(args, cwd=cwd)


def git_status(cwd: Path) -> str:
    """Return git status --porcelain output."""
    return _run_git(["status", "--porcelain"], cwd=cwd)


def git_current_branch(cwd: Path) -> str:
    """Return the current branch name."""
    return _run_git(["branch", "--show-current"], cwd=cwd)

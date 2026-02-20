"""Tests for sync state tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING

from photo_sync.state import SyncState

if TYPE_CHECKING:
    from pathlib import Path


def test_record_and_query(tmp_path: Path) -> None:
    with SyncState(tmp_path / "sync.db") as state:
        assert not state.is_synced("uuid-1", "Album A")
        state.record_sync("uuid-1", "Album A", "eagles", "eagles/a/photo.jpg", "abc123")
        assert state.is_synced("uuid-1", "Album A")
        assert not state.is_synced("uuid-1", "Album B")


def test_get_checksum(tmp_path: Path) -> None:
    with SyncState(tmp_path / "sync.db") as state:
        assert state.get_checksum("uuid-1", "Album A") is None
        state.record_sync("uuid-1", "Album A", "eagles", "eagles/a/photo.jpg", "abc123")
        assert state.get_checksum("uuid-1", "Album A") == "abc123"


def test_update_on_conflict(tmp_path: Path) -> None:
    with SyncState(tmp_path / "sync.db") as state:
        state.record_sync("uuid-1", "Album A", "eagles", "eagles/a/photo.jpg", "abc123")
        state.record_sync("uuid-1", "Album A", "eagles", "eagles/a/photo.jpg", "def456")
        assert state.get_checksum("uuid-1", "Album A") == "def456"
        assert state.count() == 1


def test_remove_record(tmp_path: Path) -> None:
    with SyncState(tmp_path / "sync.db") as state:
        state.record_sync("uuid-1", "Album A", "eagles", "eagles/a/photo.jpg", "abc123")
        assert state.count() == 1
        state.remove_record("uuid-1", "Album A")
        assert state.count() == 0
        assert not state.is_synced("uuid-1", "Album A")


def test_get_all_records(tmp_path: Path) -> None:
    with SyncState(tmp_path / "sync.db") as state:
        state.record_sync("uuid-1", "Album A", "eagles", "eagles/a/p1.jpg", "aaa")
        state.record_sync("uuid-2", "Album B", "sailing", "sailing/b/p2.jpg", "bbb")
        records = state.get_all_records()
        assert len(records) == 2


def test_get_records_by_category(tmp_path: Path) -> None:
    with SyncState(tmp_path / "sync.db") as state:
        state.record_sync("uuid-1", "Album A", "eagles", "eagles/a/p1.jpg", "aaa")
        state.record_sync("uuid-2", "Album B", "sailing", "sailing/b/p2.jpg", "bbb")
        eagles = state.get_records_by_category("eagles")
        assert len(eagles) == 1
        assert eagles[0].category == "eagles"


def test_count(tmp_path: Path) -> None:
    with SyncState(tmp_path / "sync.db") as state:
        assert state.count() == 0
        state.record_sync("uuid-1", "Album A", "eagles", "eagles/a/p1.jpg", "aaa")
        assert state.count() == 1

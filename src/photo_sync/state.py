"""SQLite sync state tracking."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from photo_sync.exceptions import StateError

if TYPE_CHECKING:
    from pathlib import Path

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS synced_photos (
    photo_uuid   TEXT NOT NULL,
    album_name   TEXT NOT NULL,
    category     TEXT NOT NULL,
    output_path  TEXT NOT NULL,
    checksum     TEXT NOT NULL,
    synced_at    TEXT NOT NULL,
    PRIMARY KEY (photo_uuid, album_name)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action    TEXT NOT NULL,
    detail    TEXT
);
"""


@dataclass(frozen=True)
class SyncRecord:
    photo_uuid: str
    album_name: str
    category: str
    output_path: str
    checksum: str
    synced_at: str


class SyncState:
    """Manages the sync state database."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(_SCHEMA)
        except sqlite3.Error as exc:
            raise StateError(f"Failed to open state DB: {exc}") from exc

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> SyncState:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def is_synced(self, photo_uuid: str, album_name: str) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM synced_photos WHERE photo_uuid = ? AND album_name = ?",
            (photo_uuid, album_name),
        )
        return cur.fetchone() is not None

    def get_checksum(self, photo_uuid: str, album_name: str) -> str | None:
        cur = self._conn.execute(
            "SELECT checksum FROM synced_photos WHERE photo_uuid = ? AND album_name = ?",
            (photo_uuid, album_name),
        )
        row = cur.fetchone()
        return str(row["checksum"]) if row else None

    def record_sync(
        self,
        photo_uuid: str,
        album_name: str,
        category: str,
        output_path: str,
        checksum: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """\
            INSERT INTO synced_photos
                (photo_uuid, album_name, category, output_path, checksum, synced_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(photo_uuid, album_name) DO UPDATE SET
                checksum = excluded.checksum,
                output_path = excluded.output_path,
                synced_at = excluded.synced_at
            """,
            (photo_uuid, album_name, category, output_path, checksum, now),
        )
        self._conn.execute(
            "INSERT INTO audit_log (timestamp, action, detail) VALUES (?, ?, ?)",
            (now, "sync", f"{photo_uuid} -> {output_path}"),
        )
        self._conn.commit()

    def remove_record(self, photo_uuid: str, album_name: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "DELETE FROM synced_photos WHERE photo_uuid = ? AND album_name = ?",
            (photo_uuid, album_name),
        )
        self._conn.execute(
            "INSERT INTO audit_log (timestamp, action, detail) VALUES (?, ?, ?)",
            (now, "remove", f"{photo_uuid} from {album_name}"),
        )
        self._conn.commit()

    def get_all_records(self) -> list[SyncRecord]:
        cur = self._conn.execute("SELECT * FROM synced_photos ORDER BY synced_at DESC")
        return [SyncRecord(**dict(row)) for row in cur.fetchall()]

    def get_records_by_category(self, category: str) -> list[SyncRecord]:
        cur = self._conn.execute(
            "SELECT * FROM synced_photos WHERE category = ? ORDER BY synced_at DESC",
            (category,),
        )
        return [SyncRecord(**dict(row)) for row in cur.fetchall()]

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM synced_photos")
        row = cur.fetchone()
        return int(row[0]) if row else 0

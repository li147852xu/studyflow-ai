from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CacheEntry:
    key: str
    vector: list[float]
    model: str
    created_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings_cache (
            key TEXT PRIMARY KEY,
            vector_json TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def get_cached_embeddings(path: Path, keys: list[str]) -> dict[str, list[float]]:
    if not keys or not path.exists():
        return {}
    connection = _ensure_db(path)
    placeholders = ",".join(["?"] * len(keys))
    rows = connection.execute(
        f"SELECT key, vector_json FROM embeddings_cache WHERE key IN ({placeholders})",
        tuple(keys),
    ).fetchall()
    connection.close()
    return {row[0]: json.loads(row[1]) for row in rows}


def put_cached_embeddings(path: Path, entries: list[CacheEntry]) -> None:
    if not entries:
        return
    connection = _ensure_db(path)
    connection.executemany(
        """
        INSERT OR REPLACE INTO embeddings_cache (key, vector_json, model, created_at)
        VALUES (?, ?, ?, ?)
        """,
        [
            (entry.key, json.dumps(entry.vector), entry.model, entry.created_at)
            for entry in entries
        ],
    )
    connection.commit()
    connection.close()

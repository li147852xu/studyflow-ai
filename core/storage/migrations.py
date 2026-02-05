from __future__ import annotations

from datetime import datetime, timezone

from infra.db import get_connection
from infra.models import init_db


LATEST_VERSION = "3.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_schema_version() -> str | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT version FROM schema_version ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    return row["version"]


def _set_schema_version(version: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO schema_version (id, version, updated_at) VALUES (?, ?, ?)",
            (f"schema:{version}", version, _now_iso()),
        )
        connection.commit()


def run_migrations() -> str:
    """Initialize schema and stamp version for v3."""
    init_db()
    current = get_schema_version()
    if current == LATEST_VERSION:
        return current
    _set_schema_version(LATEST_VERSION)
    return LATEST_VERSION

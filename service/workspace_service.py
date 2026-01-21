from __future__ import annotations

import uuid
from datetime import datetime, timezone

from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_workspace(name: str) -> str:
    workspace_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO workspaces (id, name, created_at) VALUES (?, ?, ?)",
            (workspace_id, name, _now_iso()),
        )
        connection.commit()
    return workspace_id


def list_workspaces() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, created_at FROM workspaces ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_workspace(workspace_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, name, created_at FROM workspaces WHERE id = ?",
            (workspace_id,),
        ).fetchone()
    return dict(row) if row else None

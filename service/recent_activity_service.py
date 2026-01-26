from __future__ import annotations

import uuid
from datetime import datetime, timezone

from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_activity(
    *,
    workspace_id: str,
    type: str,
    title: str | None,
    status: str,
    output_ref: str | None,
    citations_summary: str | None = None,
) -> str:
    activity_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO recent_activity (
                id, workspace_id, type, title, status, output_ref, citations_summary, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                activity_id,
                workspace_id,
                type,
                title,
                status,
                output_ref,
                citations_summary,
                _now_iso(),
            ),
        )
        connection.execute(
            """
            DELETE FROM recent_activity
            WHERE workspace_id = ?
              AND id NOT IN (
                SELECT id FROM recent_activity
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT 30
              )
            """,
            (workspace_id, workspace_id),
        )
        connection.commit()
    return activity_id


def list_recent_activity(workspace_id: str, limit: int = 30) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM recent_activity
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (workspace_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_activity(activity_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM recent_activity WHERE id = ?",
            (activity_id,),
        ).fetchone()
    return dict(row) if row else None

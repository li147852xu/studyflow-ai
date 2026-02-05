from __future__ import annotations

import uuid
from datetime import datetime, timezone

from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_event(
    *,
    workspace_id: str,
    title: str,
    start_at: str,
    end_at: str,
    location: str | None,
    linked_course_id: str | None,
    linked_todo_id: str | None,
    kind: str,
) -> str:
    event_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO timetable_event (
                id, workspace_id, title, start_at, end_at, location,
                linked_course_id, linked_todo_id, kind, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                workspace_id,
                title,
                start_at,
                end_at,
                location,
                linked_course_id,
                linked_todo_id,
                kind,
                _now_iso(),
            ),
        )
        connection.commit()
    return event_id


def list_events(*, workspace_id: str, start_at: str, end_at: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, workspace_id, title, start_at, end_at, location, linked_course_id, linked_todo_id, kind, created_at
            FROM timetable_event
            WHERE workspace_id = ? AND start_at >= ? AND start_at <= ?
            ORDER BY start_at ASC
            """,
            (workspace_id, start_at, end_at),
        ).fetchall()
    return [dict(row) for row in rows]

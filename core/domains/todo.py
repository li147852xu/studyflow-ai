from __future__ import annotations

import uuid
from datetime import datetime, timezone

from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_todo(
    *,
    workspace_id: str,
    title: str,
    status: str = "todo",
    due_at: str | None = None,
    linked_course_id: str | None = None,
    linked_project_id: str | None = None,
    notes: str | None = None,
) -> str:
    todo_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO todo_item (
                id, workspace_id, title, status, due_at, linked_course_id,
                linked_project_id, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                todo_id,
                workspace_id,
                title,
                status,
                due_at,
                linked_course_id,
                linked_project_id,
                notes,
                _now_iso(),
                _now_iso(),
            ),
        )
        connection.commit()
    return todo_id


def update_todo_status(*, todo_id: str, status: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE todo_item
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, _now_iso(), todo_id),
        )
        connection.commit()


def list_todos(*, workspace_id: str, status: str | None = None) -> list[dict]:
    with get_connection() as connection:
        if status:
            rows = connection.execute(
                """
                SELECT id, workspace_id, title, status, due_at, linked_course_id, linked_project_id, notes, created_at, updated_at
                FROM todo_item
                WHERE workspace_id = ? AND status = ?
                ORDER BY due_at ASC, created_at DESC
                """,
                (workspace_id, status),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, workspace_id, title, status, due_at, linked_course_id, linked_project_id, notes, created_at, updated_at
                FROM todo_item
                WHERE workspace_id = ?
                ORDER BY due_at ASC, created_at DESC
                """,
                (workspace_id,),
            ).fetchall()
    return [dict(row) for row in rows]

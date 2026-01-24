from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from infra.db import get_connection
from core.tasks.schema import TaskRecord


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TaskPayload:
    data: dict


def create_task(*, workspace_id: str, type: str, payload: dict) -> str:
    task_id = str(uuid.uuid4())
    payload_json = json.dumps(payload, ensure_ascii=False)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO tasks (
                id, workspace_id, type, status, progress, error, payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                workspace_id,
                type,
                "queued",
                0,
                None,
                payload_json,
                _now_iso(),
                _now_iso(),
            ),
        )
        connection.commit()
    return task_id


def get_task(task_id: str) -> TaskRecord | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return TaskRecord(**dict(row)) if row else None


def list_tasks(*, workspace_id: str | None = None, status: str | None = None) -> list[TaskRecord]:
    query = "SELECT * FROM tasks"
    params: list = []
    conditions = []
    if workspace_id:
        conditions.append("workspace_id = ?")
        params.append(workspace_id)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if conditions:
        query = f"{query} WHERE {' AND '.join(conditions)}"
    query = f"{query} ORDER BY created_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    return [TaskRecord(**dict(row)) for row in rows]


def update_status(task_id: str, status: str, error: str | None = None) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE tasks
            SET status = ?, error = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, error, _now_iso(), task_id),
        )
        connection.commit()


def update_progress(task_id: str, progress: float) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE tasks
            SET progress = ?, updated_at = ?
            WHERE id = ?
            """,
            (progress, _now_iso(), task_id),
        )
        connection.commit()


def update_payload(task_id: str, payload: dict) -> None:
    payload_json = json.dumps(payload, ensure_ascii=False)
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE tasks
            SET payload_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (payload_json, _now_iso(), task_id),
        )
        connection.commit()

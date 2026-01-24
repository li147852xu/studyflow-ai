from __future__ import annotations

import uuid
from datetime import datetime, timezone

from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ws_key(workspace_id: str | None) -> str | None:
    return workspace_id if workspace_id else None


def set_setting(workspace_id: str | None, key: str, value: str) -> None:
    ws_id = _ws_key(workspace_id)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO ui_settings (id, workspace_id, key, value, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(workspace_id, key) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
            """,
            (str(uuid.uuid4()), ws_id, key, value, _now_iso()),
        )
        connection.commit()


def get_setting(workspace_id: str | None, key: str) -> str | None:
    ws_id = _ws_key(workspace_id)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT value FROM ui_settings
            WHERE workspace_id IS ? AND key = ?
            """,
            (ws_id, key),
        ).fetchone()
    return row["value"] if row else None


def list_history(workspace_id: str, action_type: str | None = None) -> list[dict]:
    with get_connection() as connection:
        if action_type and action_type != "all":
            rows = connection.execute(
                """
                SELECT *
                FROM ui_history
                WHERE workspace_id = ? AND action_type = ?
                ORDER BY created_at DESC
                LIMIT 50
                """,
                (workspace_id, action_type),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT *
                FROM ui_history
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                LIMIT 50
                """,
                (workspace_id,),
            ).fetchall()
    return [dict(row) for row in rows]


def add_history(
    *,
    workspace_id: str,
    action_type: str,
    summary: str,
    preview: str,
    source_ref: str | None,
    citations_count: int,
    run_id: str | None = None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO ui_history (
                id, workspace_id, action_type, summary, preview, source_ref, run_id, citations_count, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                workspace_id,
                action_type,
                summary,
                preview,
                source_ref,
                run_id,
                citations_count,
                _now_iso(),
            ),
        )
        connection.commit()


def clear_history(workspace_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM ui_history WHERE workspace_id = ?",
            (workspace_id,),
        )
        connection.commit()

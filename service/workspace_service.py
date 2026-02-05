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


def rename_workspace(workspace_id: str, new_name: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE workspaces SET name = ? WHERE id = ?",
            (new_name, workspace_id),
        )
        connection.commit()


def delete_workspace_except(keep_names: list[str] | None = None) -> int:
    """Delete all workspaces except those with names in keep_names.

    Returns the number of deleted workspaces.
    """
    if keep_names is None:
        keep_names = []
    keep_names_lower = [n.lower() for n in keep_names]

    workspaces = list_workspaces()
    deleted_count = 0

    for ws in workspaces:
        if ws["name"].lower() not in keep_names_lower:
            delete_workspace(ws["id"])
            deleted_count += 1

    return deleted_count


def delete_workspace(workspace_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM lecture_material WHERE lecture_id IN (SELECT id FROM lecture WHERE course_id IN (SELECT id FROM courses WHERE workspace_id = ?))",
            (workspace_id,),
        )
        connection.execute(
            "DELETE FROM assignment_asset WHERE assignment_id IN (SELECT id FROM assignment WHERE course_id IN (SELECT id FROM courses WHERE workspace_id = ?))",
            (workspace_id,),
        )
        connection.execute(
            "DELETE FROM assignment WHERE course_id IN (SELECT id FROM courses WHERE workspace_id = ?)",
            (workspace_id,),
        )
        connection.execute(
            "DELETE FROM lecture WHERE course_id IN (SELECT id FROM courses WHERE workspace_id = ?)",
            (workspace_id,),
        )
        connection.execute(
            "DELETE FROM course_schedule WHERE course_id IN (SELECT id FROM courses WHERE workspace_id = ?)",
            (workspace_id,),
        )
        connection.execute(
            "DELETE FROM exam_asset WHERE course_id IN (SELECT id FROM courses WHERE workspace_id = ?)",
            (workspace_id,),
        )
        connection.execute("DELETE FROM course_documents WHERE course_id IN (SELECT id FROM courses WHERE workspace_id = ?)", (workspace_id,))
        connection.execute("DELETE FROM courses WHERE workspace_id = ?", (workspace_id,))
        connection.execute("DELETE FROM paper_tags WHERE paper_id IN (SELECT id FROM papers WHERE workspace_id = ?)", (workspace_id,))
        connection.execute("DELETE FROM paper_card WHERE paper_id IN (SELECT id FROM papers WHERE workspace_id = ?)", (workspace_id,))
        connection.execute("DELETE FROM idea_dialogue WHERE idea_id IN (SELECT id FROM idea WHERE project_id IN (SELECT id FROM research_project WHERE workspace_id = ?))", (workspace_id,))
        connection.execute("DELETE FROM experiment_run WHERE project_id IN (SELECT id FROM research_project WHERE workspace_id = ?)", (workspace_id,))
        connection.execute("DELETE FROM experiment_plan WHERE project_id IN (SELECT id FROM research_project WHERE workspace_id = ?)", (workspace_id,))
        connection.execute("DELETE FROM idea WHERE project_id IN (SELECT id FROM research_project WHERE workspace_id = ?)", (workspace_id,))
        connection.execute("DELETE FROM deck WHERE workspace_id = ?", (workspace_id,))
        connection.execute("DELETE FROM research_project WHERE workspace_id = ?", (workspace_id,))
        connection.execute("DELETE FROM papers WHERE workspace_id = ?", (workspace_id,))
        connection.execute("DELETE FROM doc_index_assets WHERE doc_id IN (SELECT id FROM documents WHERE workspace_id = ?)", (workspace_id,))
        connection.execute("DELETE FROM timetable_event WHERE workspace_id = ?", (workspace_id,))
        connection.execute("DELETE FROM todo_item WHERE workspace_id = ?", (workspace_id,))
        connection.execute("DELETE FROM chunks WHERE workspace_id = ?", (workspace_id,))
        connection.execute("DELETE FROM documents WHERE workspace_id = ?", (workspace_id,))
        connection.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
        connection.commit()

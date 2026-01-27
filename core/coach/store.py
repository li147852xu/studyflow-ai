from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from infra.db import get_connection, get_workspaces_dir


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CoachSession:
    id: str
    workspace_id: str
    problem: str
    phase_a_output: str | None
    phase_b_output: str | None
    citations_json: str | None
    hits_json: str | None
    status: str | None
    created_at: str
    updated_at: str
    name: str | None = None


def _next_session_index(workspace_id: str) -> int:
    """Get the next session index for default naming."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) as count FROM coach_sessions WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
    return (row["count"] if row else 0) + 1


def create_session(workspace_id: str, problem: str, name: str | None = None) -> CoachSession:
    session_id = str(uuid.uuid4())
    if not name:
        index = _next_session_index(workspace_id)
        name = f"\u4f1a\u8bdd {index}"
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO coach_sessions (
                id, workspace_id, problem, name, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, workspace_id, problem, name, "phase_a", _now_iso(), _now_iso()),
        )
        connection.commit()
    return get_session(session_id)


def rename_session(session_id: str, new_name: str) -> None:
    """Rename a coach session."""
    with get_connection() as connection:
        connection.execute(
            "UPDATE coach_sessions SET name = ?, updated_at = ? WHERE id = ?",
            (new_name, _now_iso(), session_id),
        )
        connection.commit()


def update_phase_a(
    session_id: str, output: str, citations_json: str | None, hits_json: str | None
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE coach_sessions
            SET phase_a_output = ?, citations_json = ?, hits_json = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (output, citations_json, hits_json, "phase_a_done", _now_iso(), session_id),
        )
        connection.commit()


def update_phase_b(
    session_id: str, output: str, citations_json: str | None, hits_json: str | None
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE coach_sessions
            SET phase_b_output = ?, citations_json = ?, hits_json = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (output, citations_json, hits_json, "phase_b_done", _now_iso(), session_id),
        )
        connection.commit()


def get_session(session_id: str) -> CoachSession:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM coach_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    if not row:
        raise RuntimeError("Coach session not found.")
    return CoachSession(**dict(row))


def list_sessions(workspace_id: str) -> list[CoachSession]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM coach_sessions
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return [CoachSession(**dict(row)) for row in rows]


def clear_sessions(workspace_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM coach_sessions WHERE workspace_id = ?",
            (workspace_id,),
        )
        connection.commit()


def write_session_file(session: CoachSession) -> str:
    payload = {
        "session_id": session.id,
        "workspace_id": session.workspace_id,
        "name": session.name,
        "problem": session.problem,
        "phase_a_output": session.phase_a_output,
        "phase_b_output": session.phase_b_output,
        "citations_json": session.citations_json,
        "hits_json": session.hits_json,
        "status": session.status,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
    output_dir = get_workspaces_dir() / session.workspace_id / "coach"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"session_{session.id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)

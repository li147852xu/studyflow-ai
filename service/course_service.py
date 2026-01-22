from __future__ import annotations

import uuid
from datetime import datetime, timezone

from infra.db import get_connection
from core.agents.course_agent import CourseAgent, AgentOutput


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_course(workspace_id: str, name: str) -> str:
    course_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO courses (id, workspace_id, name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (course_id, workspace_id, name, _now_iso()),
        )
        connection.commit()
    return course_id


def list_courses(workspace_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, workspace_id, name, created_at
            FROM courses
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def link_document(course_id: str, doc_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO course_documents (id, course_id, doc_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), course_id, doc_id, _now_iso()),
        )
        connection.commit()


def list_course_documents(course_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT documents.id, documents.filename, documents.path, documents.page_count
            FROM course_documents
            JOIN documents ON documents.id = course_documents.doc_id
            WHERE course_documents.course_id = ?
            ORDER BY documents.created_at DESC
            """,
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_course_doc_ids(course_id: str) -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT doc_id
            FROM course_documents
            WHERE course_id = ?
            """,
            (course_id,),
        ).fetchall()
    return [row["doc_id"] for row in rows]


def generate_overview(
    *,
    workspace_id: str,
    course_id: str,
    progress_cb: callable | None = None,
) -> AgentOutput:
    doc_ids = list_course_doc_ids(course_id)
    if not doc_ids:
        raise RuntimeError("No lecture PDFs linked to this course.")
    agent = CourseAgent(workspace_id, course_id, doc_ids)
    return agent.generate_overview(progress_cb=progress_cb)


def generate_cheatsheet(
    *,
    workspace_id: str,
    course_id: str,
    progress_cb: callable | None = None,
) -> AgentOutput:
    doc_ids = list_course_doc_ids(course_id)
    if not doc_ids:
        raise RuntimeError("No lecture PDFs linked to this course.")
    agent = CourseAgent(workspace_id, course_id, doc_ids)
    return agent.generate_cheatsheet(progress_cb=progress_cb)


def explain_selection(
    *,
    workspace_id: str,
    course_id: str,
    selection: str,
    mode: str,
) -> AgentOutput:
    doc_ids = list_course_doc_ids(course_id)
    if not doc_ids:
        raise RuntimeError("No lecture PDFs linked to this course.")
    agent = CourseAgent(workspace_id, course_id, doc_ids)
    return agent.explain_selection(selection, mode)

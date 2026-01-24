from __future__ import annotations

import uuid
from datetime import datetime, timezone

import os
import time

from infra.db import get_connection
from core.agents.course_agent import CourseAgent, AgentOutput
from core.telemetry.run_logger import log_run
from service.asset_service import (
    course_explain_ref_id,
    course_ref_id,
    create_asset_version,
)


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
    retrieval_mode: str = "vector",
    progress_cb: callable | None = None,
) -> AgentOutput:
    doc_ids = list_course_doc_ids(course_id)
    if not doc_ids:
        raise RuntimeError("No lecture PDFs linked to this course.")
    start = time.time()
    agent = CourseAgent(workspace_id, course_id, doc_ids, retrieval_mode)
    output = agent.generate_overview(progress_cb=progress_cb)
    latency_ms = int((time.time() - start) * 1000)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="course_overview",
        input_payload={"course_id": course_id},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        embed_model=os.getenv("STUDYFLOW_EMBED_MODEL", ""),
        latency_ms=latency_ms,
        errors=None,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="course_overview",
        ref_id=course_ref_id(course_id),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        prompt_version="v1",
        hits=output.hits,
    )
    output.asset_id = version.asset_id
    output.asset_version_id = version.id
    output.asset_version_index = version.version_index
    return output


def generate_cheatsheet(
    *,
    workspace_id: str,
    course_id: str,
    retrieval_mode: str = "vector",
    progress_cb: callable | None = None,
) -> AgentOutput:
    doc_ids = list_course_doc_ids(course_id)
    if not doc_ids:
        raise RuntimeError("No lecture PDFs linked to this course.")
    start = time.time()
    agent = CourseAgent(workspace_id, course_id, doc_ids, retrieval_mode)
    output = agent.generate_cheatsheet(progress_cb=progress_cb)
    latency_ms = int((time.time() - start) * 1000)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="course_cheatsheet",
        input_payload={"course_id": course_id},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        embed_model=os.getenv("STUDYFLOW_EMBED_MODEL", ""),
        latency_ms=latency_ms,
        errors=None,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="course_cheatsheet",
        ref_id=course_ref_id(course_id),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        prompt_version="v1",
        hits=output.hits,
    )
    output.asset_id = version.asset_id
    output.asset_version_id = version.id
    output.asset_version_index = version.version_index
    return output


def explain_selection(
    *,
    workspace_id: str,
    course_id: str,
    selection: str,
    mode: str,
    retrieval_mode: str = "vector",
) -> AgentOutput:
    doc_ids = list_course_doc_ids(course_id)
    if not doc_ids:
        raise RuntimeError("No lecture PDFs linked to this course.")
    start = time.time()
    agent = CourseAgent(workspace_id, course_id, doc_ids, retrieval_mode)
    output = agent.explain_selection(selection, mode)
    latency_ms = int((time.time() - start) * 1000)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="course_explain",
        input_payload={"course_id": course_id, "mode": mode},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        embed_model=os.getenv("STUDYFLOW_EMBED_MODEL", ""),
        latency_ms=latency_ms,
        errors=None,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="course_explain",
        ref_id=course_explain_ref_id(course_id, selection, mode),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        prompt_version="v1",
        hits=output.hits,
    )
    output.asset_id = version.asset_id
    output.asset_version_id = version.id
    output.asset_version_index = version.version_index
    return output

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from core.agents.course_agent import AgentOutput, CourseAgent
from core.quality.citations_check import check_citations
from core.telemetry.run_logger import log_run
from infra.db import get_connection
from service.asset_service import (
    course_explain_ref_id,
    course_ref_id,
    create_asset_version,
)
from service.document_service import get_document
from service.metadata_service import llm_metadata


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
    doc = get_document(doc_id)
    if doc and doc.get("doc_type") != "course":
        raise RuntimeError("Only course documents can be linked to a course.")
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
            SELECT documents.id, documents.filename, documents.path, documents.page_count, documents.doc_type
            FROM course_documents
            JOIN documents ON documents.id = course_documents.doc_id
            WHERE course_documents.course_id = ? AND documents.doc_type = 'course'
            ORDER BY documents.created_at DESC
            """,
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_course_doc_ids(course_id: str) -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT course_documents.doc_id as doc_id
            FROM course_documents
            JOIN documents ON documents.id = course_documents.doc_id
            WHERE course_documents.course_id = ? AND documents.doc_type = 'course'
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
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.content, output.hits)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="course_overview",
        input_payload={"course_id": course_id},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version,
        latency_ms=latency_ms,
        citation_incomplete=not citation_ok,
        errors=citation_error,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="course_overview",
        ref_id=course_ref_id(course_id),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=output.retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version or "v1",
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
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.content, output.hits)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="course_cheatsheet",
        input_payload={"course_id": course_id},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version,
        latency_ms=latency_ms,
        citation_incomplete=not citation_ok,
        errors=citation_error,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="course_cheatsheet",
        ref_id=course_ref_id(course_id),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=output.retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version or "v1",
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
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.content, output.hits)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="course_explain",
        input_payload={"course_id": course_id, "mode": mode},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version,
        latency_ms=latency_ms,
        citation_incomplete=not citation_ok,
        errors=citation_error,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="course_explain",
        ref_id=course_explain_ref_id(course_id, selection, mode),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=output.retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version or "v1",
        hits=output.hits,
    )
    output.asset_id = version.asset_id
    output.asset_version_id = version.id
    output.asset_version_index = version.version_index
    return output


def answer_course_question(
    *,
    workspace_id: str,
    course_id: str,
    question: str,
    retrieval_mode: str = "vector",
) -> AgentOutput:
    """Answer a question about the course content using RAG."""
    from service.retrieval_service import answer_with_retrieval

    doc_ids = list_course_doc_ids(course_id)
    if not doc_ids:
        raise RuntimeError("No lecture PDFs linked to this course.")

    answer, hits, citations, run_id = answer_with_retrieval(
        workspace_id=workspace_id,
        query=question,
        mode=retrieval_mode,
        doc_ids=doc_ids,
    )
    from core.formatting.citations import build_citation_bundle
    bundle = build_citation_bundle(hits)
    meta = llm_metadata(temperature=0.2)
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="course_qa",
        ref_id=f"course_qa:{course_id}:{question[:50]}",
        content=answer,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version="v1",
        hits=hits,
    )
    return AgentOutput(
        content=answer,
        citations=bundle.citations,
        hits=hits,
        retrieval_mode=retrieval_mode,
        run_id=run_id,
        asset_id=version.asset_id,
        asset_version_id=version.id,
        asset_version_index=version.version_index,
        prompt_version="v1",
    )

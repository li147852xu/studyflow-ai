from __future__ import annotations

from pathlib import Path

from core.ui_state.storage import list_history
from infra.db import get_connection, get_workspaces_dir
from service.document_service import (
    add_document_tags,
    delete_document_by_id,
    get_document,
    list_document_tags,
    list_documents,
    list_documents_by_type,
    set_document_type,
)
from service.retrieval_service import index_status
from service.tasks_service import enqueue_ingest_index_task, run_task_in_background
from service.ui_facade import UIResult, safe_call


def import_and_process(
    *,
    workspace_id: str,
    filename: str,
    data: bytes,
    ocr_mode: str,
    ocr_threshold: int,
    doc_type: str = "other",
) -> UIResult:
    def _run() -> dict:
        upload_dir = get_workspaces_dir() / workspace_id / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        target_path = upload_dir / filename
        target_path.write_bytes(data)
        task_id = enqueue_ingest_index_task(
            workspace_id=workspace_id,
            path=str(target_path),
            ocr_mode=ocr_mode,
            ocr_threshold=ocr_threshold,
            doc_type=doc_type,
            save_dir=str(upload_dir),
            write_file=True,
        )
        run_task_in_background(task_id)
        return {"task_id": task_id}

    return safe_call(_run, hint="Check OCR and indexing tasks.")


def rebuild_index(*, workspace_id: str, doc_ids: list[str] | None = None) -> UIResult:
    def _run() -> dict:
        task_id = enqueue_index_task(
            workspace_id=workspace_id,
            reset=not doc_ids,
            doc_ids=doc_ids,
        )
        run_task_in_background(task_id)
        return {"task_id": task_id}

    return safe_call(_run, hint="Index rebuild failed; check tasks log.")


def workspace_status(workspace_id: str) -> UIResult:
    return safe_call(index_status, hint="Index status unavailable.", workspace_id=workspace_id)


def list_documents_with_tags(workspace_id: str) -> UIResult:
    def _run() -> list[dict]:
        docs = list_documents(workspace_id)
        for doc in docs:
            doc["tags"] = list_document_tags(doc["id"])
        return docs

    return safe_call(_run, hint="Unable to load documents.")


def list_documents_for_type(*, workspace_id: str, doc_type: str) -> UIResult:
    return safe_call(
        list_documents_by_type, hint="Unable to load documents.", workspace_id=workspace_id, doc_type=doc_type
    )


def update_document_tags(*, doc_id: str, tags: list[str]) -> UIResult:
    return safe_call(add_document_tags, hint="Unable to update tags.", doc_id=doc_id, tags=tags)


def update_document_type(*, doc_id: str, doc_type: str) -> UIResult:
    return safe_call(set_document_type, hint="Unable to update document type.", doc_id=doc_id, doc_type=doc_type)


def delete_document(*, workspace_id: str, doc_id: str) -> UIResult:
    return safe_call(
        delete_document_by_id,
        hint="Unable to delete document.",
        workspace_id=workspace_id,
        doc_id=doc_id,
    )


def get_document_detail(doc_id: str) -> UIResult:
    return safe_call(get_document, hint="Unable to load document details.", doc_id=doc_id)


def recent_history(*, workspace_id: str, limit: int = 10) -> UIResult:
    def _run() -> list[dict]:
        return list_history(workspace_id)[:limit]

    return safe_call(_run, hint="Unable to load history.")


def doc_chunk_counts(workspace_id: str) -> dict[str, int]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT doc_id, COUNT(*) as count
            FROM chunks
            WHERE workspace_id = ?
            GROUP BY doc_id
            """,
            (workspace_id,),
        ).fetchall()
    return {row["doc_id"]: int(row["count"]) for row in rows}


def doc_pages(workspace_id: str) -> dict[str, int]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, page_count
            FROM documents
            WHERE workspace_id = ?
            """,
            (workspace_id,),
        ).fetchall()
    return {row["id"]: int(row["page_count"] or 0) for row in rows}


def upload_dir(*, workspace_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "uploads"

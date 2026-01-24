from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from infra.db import get_connection, get_workspaces_dir
from core.indexing.sync import delete_document, delete_document_vectors
from core.retrieval.bm25_index import build_bm25_index


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workspace_upload_dir(workspace_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "uploads"


def save_document_bytes(
    workspace_id: str, filename: str, data: bytes
) -> dict:
    upload_dir = _workspace_upload_dir(workspace_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    document_id = str(uuid.uuid4())
    target_path = upload_dir / filename
    target_path.write_bytes(data)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (id, workspace_id, filename, path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (document_id, workspace_id, filename, str(target_path), _now_iso()),
        )
        connection.commit()

    return {
        "id": document_id,
        "workspace_id": workspace_id,
        "filename": filename,
        "path": str(target_path),
    }


def list_documents(workspace_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, workspace_id, filename, path, page_count, created_at
            FROM documents
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_document(doc_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, workspace_id, filename, path, sha256, page_count, created_at
            FROM documents
            WHERE id = ?
            """,
            (doc_id,),
        ).fetchone()
    return dict(row) if row else None


def delete_document_by_id(workspace_id: str, doc_id: str) -> None:
    delete_document_vectors(workspace_id, doc_id)
    delete_document(workspace_id, doc_id)
    try:
        build_bm25_index(workspace_id)
    except Exception:
        pass


def add_document_tags(doc_id: str, tags: list[str]) -> None:
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO document_tags (id, doc_id, tag, created_at)
            VALUES (?, ?, ?, ?)
            """,
            [
                (str(uuid.uuid4()), doc_id, tag.strip(), _now_iso())
                for tag in tags
                if tag.strip()
            ],
        )
        connection.commit()


def list_document_tags(doc_id: str) -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT tag FROM document_tags WHERE doc_id = ? ORDER BY tag ASC",
            (doc_id,),
        ).fetchall()
    return [row["tag"] for row in rows]

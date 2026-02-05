from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from infra.db import get_connection, get_workspaces_dir

DOC_TYPES = {"course", "paper", "other"}
from core.indexing.sync import delete_document, delete_document_vectors
from core.retrieval.bm25_index import build_bm25_index


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workspace_upload_dir(workspace_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "uploads"


def save_document_bytes(
    workspace_id: str, filename: str, data: bytes, doc_type: str = "other"
) -> dict:
    doc_type = normalize_doc_type(doc_type)
    upload_dir = _workspace_upload_dir(workspace_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    document_id = str(uuid.uuid4())
    target_path = upload_dir / filename
    target_path.write_bytes(data)
    extension = target_path.suffix.lower()
    file_type = extension.lstrip(".") or "unknown"
    size_bytes = len(data)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id, workspace_id, filename, path, doc_type, file_type,
                size_bytes, file_name, file_ext, file_size, imported_at,
                source, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                workspace_id,
                filename,
                str(target_path),
                doc_type,
                file_type,
                size_bytes,
                filename,
                extension.lstrip("."),
                size_bytes,
                _now_iso(),
                "upload",
                _now_iso(),
                _now_iso(),
            ),
        )
        connection.commit()

    return {
        "id": document_id,
        "workspace_id": workspace_id,
        "filename": filename,
        "path": str(target_path),
    }


def list_documents(
    workspace_id: str,
    *,
    limit: int | None = None,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    doc_type: str | None = None,
    search: str | None = None,
) -> list[dict]:
    sort_map = {
        "created_at": "created_at",
        "filename": "lower(filename)",
        "size_bytes": "COALESCE(size_bytes, 0)",
    }
    sort_column = sort_map.get(sort_by, "created_at")
    order = "DESC" if sort_order.lower() == "desc" else "ASC"
    filters = ["workspace_id = ?"]
    params: list = [workspace_id]
    if doc_type:
        filters.append("doc_type = ?")
        params.append(normalize_doc_type(doc_type))
    if search:
        filters.append("lower(filename) LIKE ?")
        params.append(f"%{search.strip().lower()}%")
    where_clause = " AND ".join(filters)
    limit_clause = ""
    if limit is not None:
        limit_clause = " LIMIT ? OFFSET ?"
        params.extend([int(limit), int(offset)])
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, workspace_id, filename, path, doc_type, page_count,
                   source_type, source_ref, summary, created_at, file_type,
                   size_bytes, source, file_name, file_ext, file_size, imported_at
            FROM documents
            WHERE {where_clause}
            ORDER BY {sort_column} {order}
            {limit_clause}
            """,
            tuple(params),
        ).fetchall()
    return [dict(row) for row in rows]


def count_documents(
    workspace_id: str, doc_type: str | None = None, search: str | None = None
) -> int:
    filters = ["workspace_id = ?"]
    params: list = [workspace_id]
    if doc_type:
        filters.append("doc_type = ?")
        params.append(normalize_doc_type(doc_type))
    if search:
        filters.append("lower(filename) LIKE ?")
        params.append(f"%{search.strip().lower()}%")
    where_clause = " AND ".join(filters)
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT COUNT(*) as count FROM documents WHERE {where_clause}",
            tuple(params),
        ).fetchone()
    return int(row["count"]) if row else 0


def get_document(doc_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, workspace_id, filename, path, doc_type, sha256, page_count,
                   source_type, source_ref, summary, created_at, file_type,
                   size_bytes, source, file_name, file_ext, file_size, imported_at
            FROM documents
            WHERE id = ?
            """,
            (doc_id,),
        ).fetchone()
    return dict(row) if row else None


def set_document_summary(*, doc_id: str, summary: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE documents SET summary = ? WHERE id = ?",
            (summary, doc_id),
        )
        connection.commit()


def normalize_doc_type(doc_type: str | None) -> str:
    value = (doc_type or "other").strip().lower()
    if value not in DOC_TYPES:
        raise ValueError("doc_type must be one of: course, paper, other.")
    return value


def set_document_type(*, doc_id: str, doc_type: str) -> None:
    doc_type = normalize_doc_type(doc_type)
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE documents
            SET doc_type = ?
            WHERE id = ?
            """,
            (doc_type, doc_id),
        )
        connection.commit()


def list_documents_by_type(workspace_id: str, doc_type: str) -> list[dict]:
    return list_documents(workspace_id, doc_type=doc_type)


def filter_doc_ids_by_type(doc_ids: list[str], doc_type: str) -> list[str]:
    doc_type = normalize_doc_type(doc_type)
    if not doc_ids:
        return []
    placeholders = ",".join(["?"] * len(doc_ids))
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id FROM documents
            WHERE id IN ({placeholders}) AND doc_type = ?
            """,
            (*doc_ids, doc_type),
        ).fetchall()
    return [row["id"] for row in rows]


def filter_doc_ids_by_types(doc_ids: list[str], doc_types: list[str]) -> list[str]:
    normalized = [normalize_doc_type(value) for value in doc_types]
    if not doc_ids or not normalized:
        return []
    placeholders = ",".join(["?"] * len(doc_ids))
    type_placeholders = ",".join(["?"] * len(normalized))
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id FROM documents
            WHERE id IN ({placeholders}) AND doc_type IN ({type_placeholders})
            """,
            (*doc_ids, *normalized),
        ).fetchall()
    return [row["id"] for row in rows]


def set_document_source(
    *, doc_id: str, source_type: str | None, source_ref: str | None
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE documents
            SET source_type = ?, source_ref = ?, source = ?
            WHERE id = ?
            """,
            (source_type, source_ref, source_type, doc_id),
        )
        connection.commit()


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

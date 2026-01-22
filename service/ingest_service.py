from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.ingest.chunker import Chunk, chunk_pages
from core.ingest.pdf_reader import PDFReadError, read_pdf
from core.indexing.planner import plan_document
from core.indexing.sync import delete_document, delete_document_vectors
from core.retrieval.bm25_index import build_bm25_index
from infra.db import get_connection, get_workspaces_dir


class IngestError(RuntimeError):
    pass


@dataclass
class IngestResult:
    doc_id: str
    workspace_id: str
    filename: str
    path: str
    sha256: str
    page_count: int
    chunk_count: int
    skipped: bool


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def _get_existing_document(workspace_id: str, sha256: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, workspace_id, filename, path, sha256, page_count
            FROM documents
            WHERE workspace_id = ? AND sha256 = ?
            """,
            (workspace_id, sha256),
        ).fetchone()
    return dict(row) if row else None


def _count_chunks(doc_id: str) -> int:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) as count FROM chunks WHERE doc_id = ?",
            (doc_id,),
        ).fetchone()
    return int(row["count"]) if row else 0


def _insert_document(
    *,
    workspace_id: str,
    filename: str,
    path: str,
    sha256: str,
    page_count: int,
) -> str:
    doc_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (id, workspace_id, filename, path, sha256, page_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                workspace_id,
                filename,
                path,
                sha256,
                page_count,
                _now_iso(),
                _now_iso(),
            ),
        )
        connection.commit()
    return doc_id


def _insert_chunks(
    *,
    doc_id: str,
    workspace_id: str,
    chunks: list[Chunk],
) -> None:
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO chunks (id, doc_id, workspace_id, chunk_index, page_start, page_end, text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    f"{doc_id}:{chunk.chunk_index}",
                    doc_id,
                    workspace_id,
                    chunk.chunk_index,
                    chunk.page_start,
                    chunk.page_end,
                    chunk.text,
                    _now_iso(),
                )
                for chunk in chunks
            ],
        )
        connection.commit()


def ingest_pdf(
    *,
    workspace_id: str,
    filename: str,
    data: bytes,
    save_dir: Path,
) -> IngestResult:
    if not data:
        raise IngestError("Uploaded PDF is empty.")

    sha256 = _sha256_bytes(data)

    save_dir.mkdir(parents=True, exist_ok=True)
    target_path = save_dir / filename
    target_path.write_bytes(data)

    plan = plan_document(workspace_id, target_path)
    if plan.action == "skip":
        existing = _get_existing_document(workspace_id, sha256)
        if existing:
            chunk_count = _count_chunks(existing["id"])
            return IngestResult(
                doc_id=existing["id"],
                workspace_id=workspace_id,
                filename=existing["filename"],
                path=existing["path"],
                sha256=sha256,
                page_count=existing.get("page_count") or 0,
                chunk_count=chunk_count,
                skipped=True,
            )

    if plan.action == "update" and plan.doc_id:
        delete_document_vectors(workspace_id, plan.doc_id)
        delete_document(workspace_id, plan.doc_id)

    try:
        parse_result = read_pdf(target_path)
    except PDFReadError as exc:
        raise IngestError(str(exc)) from exc

    chunks = chunk_pages(parse_result.pages)
    if not chunks:
        raise IngestError("No text extracted from PDF.")

    doc_id = _insert_document(
        workspace_id=workspace_id,
        filename=filename,
        path=str(target_path),
        sha256=sha256,
        page_count=parse_result.page_count,
    )
    _insert_chunks(doc_id=doc_id, workspace_id=workspace_id, chunks=chunks)
    try:
        build_bm25_index(workspace_id)
    except Exception:
        pass

    return IngestResult(
        doc_id=doc_id,
        workspace_id=workspace_id,
        filename=filename,
        path=str(target_path),
        sha256=sha256,
        page_count=parse_result.page_count,
        chunk_count=len(chunks),
        skipped=False,
    )


def get_random_chunks(doc_id: str, limit: int = 3) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, doc_id, workspace_id, chunk_index, page_start, page_end, text
            FROM chunks
            WHERE doc_id = ?
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (doc_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]

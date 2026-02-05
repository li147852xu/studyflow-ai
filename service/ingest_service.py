from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.indexing.planner import plan_document
from core.indexing.sync import delete_document, delete_document_vectors
from core.ingest.chunker import Chunk, chunk_pages
from core.ingest.document_reader import (
    DocumentReadError,
    read_docx,
    read_html,
    read_image,
    read_pptx,
    read_text_lines,
)
from core.ingest.ocr import OCRSettings
from core.ingest.pdf_reader import PDFReadError, read_pdf
from core.retrieval.bm25_index import build_bm25_index
from infra.db import get_connection
from service.document_service import normalize_doc_type


class IngestError(RuntimeError):
    pass


@dataclass
class IngestResult:
    doc_id: str
    workspace_id: str
    filename: str
    path: str
    doc_type: str
    file_type: str
    size_bytes: int
    source: str
    sha256: str
    page_count: int
    chunk_count: int
    skipped: bool
    ocr_pages_count: int = 0
    image_pages_count: int = 0
    ocr_mode: str = "off"
    warnings: list[str] | None = None


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
            SELECT id, workspace_id, filename, path, sha256, page_count,
                   ocr_mode, ocr_pages_count, image_pages_count, doc_type,
                   file_type, size_bytes, source
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
    doc_type: str,
    file_type: str,
    size_bytes: int,
    source: str,
    page_count: int,
    ocr_mode: str,
    ocr_pages_count: int,
    image_pages_count: int,
) -> str:
    doc_id = str(uuid.uuid4())
    file_ext = file_type or ""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id, workspace_id, filename, path, doc_type, sha256, page_count,
                ocr_mode, ocr_pages_count, image_pages_count, file_type, size_bytes,
                file_name, file_ext, file_size, imported_at,
                source, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                workspace_id,
                filename,
                path,
                doc_type,
                sha256,
                page_count,
                ocr_mode,
                ocr_pages_count,
                image_pages_count,
                file_type,
                size_bytes,
                filename,
                file_ext,
                size_bytes,
                _now_iso(),
                source,
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
            INSERT INTO chunks (
                id, doc_id, workspace_id, chunk_index, page_start, page_end,
                text, text_source, metadata_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    chunk.text_source,
                    chunk.metadata_json,
                    _now_iso(),
                )
                for chunk in chunks
            ],
        )
        connection.commit()


def _insert_document_pages(
    *,
    doc_id: str,
    workspace_id: str,
    pages: list,
) -> None:
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO document_pages (
                id, doc_id, workspace_id, page_number, text_source, ocr_text,
                image_count, has_images, blocks_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    f"{doc_id}:{page.number}",
                    doc_id,
                    workspace_id,
                    page.number,
                    page.text_source,
                    page.ocr_text,
                    page.image_count,
                    1 if page.has_images else 0,
                    page.blocks_json,
                    _now_iso(),
                )
                for page in pages
            ],
        )
        connection.commit()


def ingest_pdf(
    *,
    workspace_id: str,
    filename: str,
    data: bytes,
    save_dir: Path,
    write_file: bool = True,
    existing_path: Path | None = None,
    ocr_mode: str = "off",
    ocr_threshold: int = 50,
    doc_type: str = "other",
    source: str = "upload",
    progress_cb: callable | None = None,
    stop_check: callable | None = None,
) -> IngestResult:
    doc_type = normalize_doc_type(doc_type)
    if not data:
        raise IngestError("Uploaded PDF is empty.")
    if ocr_mode not in ["off", "auto", "on"]:
        raise IngestError("OCR mode must be off, auto, or on.")

    sha256 = _sha256_bytes(data)
    size_bytes = len(data)
    file_type = "pdf"

    save_dir.mkdir(parents=True, exist_ok=True)
    target_path = existing_path or (save_dir / filename)
    if write_file:
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
                doc_type=existing.get("doc_type") or doc_type,
                file_type=existing.get("file_type") or file_type,
                size_bytes=int(existing.get("size_bytes") or size_bytes),
                source=existing.get("source") or source,
                sha256=sha256,
                page_count=existing.get("page_count") or 0,
                chunk_count=chunk_count,
                skipped=True,
                ocr_pages_count=existing.get("ocr_pages_count") or 0,
                image_pages_count=existing.get("image_pages_count") or 0,
                ocr_mode=existing.get("ocr_mode") or "off",
                warnings=[],
            )

    if plan.action == "update" and plan.doc_id:
        delete_document_vectors(workspace_id, plan.doc_id)
        delete_document(workspace_id, plan.doc_id)

    try:
        parse_result = read_pdf(
            target_path,
            ocr_mode=ocr_mode,
            ocr_threshold=ocr_threshold,
            ocr_settings=OCRSettings(),
            progress_cb=progress_cb,
            stop_check=stop_check,
        )
    except PDFReadError as exc:
        raise IngestError(str(exc)) from exc

    chunks = chunk_pages(parse_result.pages)
    if not chunks:
        raise IngestError("No text extracted from PDF.")

    ocr_pages_count = len([p for p in parse_result.pages if p.text_source in ["ocr", "mixed"]])
    image_pages_count = len([p for p in parse_result.pages if p.has_images])
    doc_id = _insert_document(
        workspace_id=workspace_id,
        filename=filename,
        path=str(target_path),
        sha256=sha256,
        doc_type=doc_type,
        file_type=file_type,
        size_bytes=size_bytes,
        source=source,
        page_count=parse_result.page_count,
        ocr_mode=ocr_mode,
        ocr_pages_count=ocr_pages_count,
        image_pages_count=image_pages_count,
    )
    _insert_chunks(doc_id=doc_id, workspace_id=workspace_id, chunks=chunks)
    _insert_document_pages(
        doc_id=doc_id,
        workspace_id=workspace_id,
        pages=parse_result.pages,
    )
    try:
        build_bm25_index(workspace_id)
    except Exception:
        pass

    return IngestResult(
        doc_id=doc_id,
        workspace_id=workspace_id,
        filename=filename,
        path=str(target_path),
        doc_type=doc_type,
        file_type=file_type,
        size_bytes=size_bytes,
        source=source,
        sha256=sha256,
        page_count=parse_result.page_count,
        chunk_count=len(chunks),
        skipped=False,
        ocr_pages_count=ocr_pages_count,
        image_pages_count=image_pages_count,
        ocr_mode=ocr_mode,
        warnings=parse_result.warnings,
    )


def ingest_document(
    *,
    workspace_id: str,
    filename: str,
    data: bytes,
    save_dir: Path,
    write_file: bool = True,
    existing_path: Path | None = None,
    ocr_mode: str = "off",
    ocr_threshold: int = 50,
    doc_type: str = "other",
    source: str = "upload",
    progress_cb: callable | None = None,
    stop_check: callable | None = None,
) -> IngestResult:
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        return ingest_pdf(
            workspace_id=workspace_id,
            filename=filename,
            data=data,
            save_dir=save_dir,
            write_file=write_file,
            existing_path=existing_path,
            ocr_mode=ocr_mode,
            ocr_threshold=ocr_threshold,
            doc_type=doc_type,
            source=source,
            progress_cb=progress_cb,
            stop_check=stop_check,
        )

    doc_type = normalize_doc_type(doc_type)
    if not data:
        raise IngestError("Uploaded file is empty.")
    sha256 = _sha256_bytes(data)
    size_bytes = len(data)
    file_type = extension.lstrip(".") or "unknown"

    save_dir.mkdir(parents=True, exist_ok=True)
    target_path = existing_path or (save_dir / filename)
    if write_file:
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
                doc_type=existing.get("doc_type") or doc_type,
                file_type=existing.get("file_type") or file_type,
                size_bytes=int(existing.get("size_bytes") or size_bytes),
                source=existing.get("source") or source,
                sha256=sha256,
                page_count=existing.get("page_count") or 0,
                chunk_count=chunk_count,
                skipped=True,
                ocr_pages_count=existing.get("ocr_pages_count") or 0,
                image_pages_count=existing.get("image_pages_count") or 0,
                ocr_mode=existing.get("ocr_mode") or "off",
                warnings=[],
            )

    if plan.action == "update" and plan.doc_id:
        delete_document_vectors(workspace_id, plan.doc_id)
        delete_document(workspace_id, plan.doc_id)

    try:
        if extension in [".txt", ".md"]:
            parse_result = read_text_lines(target_path)
        elif extension == ".docx":
            parse_result = read_docx(target_path)
        elif extension == ".pptx":
            parse_result = read_pptx(target_path)
        elif extension in [".html", ".htm"]:
            parse_result = read_html(target_path)
        elif extension in [".png", ".jpg", ".jpeg"]:
            parse_result = read_image(
                target_path, ocr_mode=ocr_mode, ocr_settings=OCRSettings()
            )
        else:
            raise IngestError("Unsupported file type.")
    except DocumentReadError as exc:
        raise IngestError(str(exc)) from exc

    chunks = chunk_pages(parse_result.pages)
    if not chunks:
        raise IngestError("No text extracted from the file.")

    ocr_pages_count = len(
        [p for p in parse_result.pages if p.text_source in ["ocr", "mixed"]]
    )
    image_pages_count = len([p for p in parse_result.pages if p.has_images])
    doc_id = _insert_document(
        workspace_id=workspace_id,
        filename=filename,
        path=str(target_path),
        sha256=sha256,
        doc_type=doc_type,
        file_type=file_type,
        size_bytes=size_bytes,
        source=source,
        page_count=parse_result.page_count,
        ocr_mode=ocr_mode,
        ocr_pages_count=ocr_pages_count,
        image_pages_count=image_pages_count,
    )
    _insert_chunks(doc_id=doc_id, workspace_id=workspace_id, chunks=chunks)
    _insert_document_pages(
        doc_id=doc_id,
        workspace_id=workspace_id,
        pages=parse_result.pages,
    )
    try:
        build_bm25_index(workspace_id)
    except Exception:
        pass

    return IngestResult(
        doc_id=doc_id,
        workspace_id=workspace_id,
        filename=filename,
        path=str(target_path),
        doc_type=doc_type,
        file_type=file_type,
        size_bytes=size_bytes,
        source=source,
        sha256=sha256,
        page_count=parse_result.page_count,
        chunk_count=len(chunks),
        skipped=False,
        ocr_pages_count=ocr_pages_count,
        image_pages_count=image_pages_count,
        ocr_mode=ocr_mode,
        warnings=parse_result.warnings,
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

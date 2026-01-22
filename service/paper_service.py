from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.ingest.pdf_reader import read_pdf
from core.parsing.metadata import PaperMetadata, extract_metadata
from core.prompts.paper_prompts import metadata_fallback_prompt
from infra.db import get_connection
from service.chat_service import ChatConfigError, chat
from service.ingest_service import ingest_pdf


class PaperServiceError(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_paper(
    *,
    workspace_id: str,
    doc_id: str,
    title: str,
    authors: str,
    year: str,
) -> str:
    paper_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO papers (id, workspace_id, doc_id, title, authors, year, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (paper_id, workspace_id, doc_id, title, authors, year, _now_iso()),
        )
        connection.commit()
    return paper_id


def update_paper_metadata(
    *,
    paper_id: str,
    title: str,
    authors: str,
    year: str,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE papers
            SET title = ?, authors = ?, year = ?
            WHERE id = ?
            """,
            (title, authors, year, paper_id),
        )
        connection.commit()


def list_papers(workspace_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT papers.id, papers.workspace_id, papers.doc_id, papers.title,
                   papers.authors, papers.year, papers.created_at,
                   documents.filename as filename
            FROM papers
            JOIN documents ON documents.id = papers.doc_id
            WHERE papers.workspace_id = ?
            ORDER BY papers.created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def find_paper_by_doc(workspace_id: str, doc_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, workspace_id, doc_id, title, authors, year, created_at
            FROM papers
            WHERE workspace_id = ? AND doc_id = ?
            """,
            (workspace_id, doc_id),
        ).fetchone()
    return dict(row) if row else None


def add_tags(paper_id: str, tags: list[str]) -> None:
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO paper_tags (id, paper_id, tag, created_at)
            VALUES (?, ?, ?, ?)
            """,
            [
                (str(uuid.uuid4()), paper_id, tag.strip(), _now_iso())
                for tag in tags
                if tag.strip()
            ],
        )
        connection.commit()


def list_tags(paper_id: str) -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT tag FROM paper_tags
            WHERE paper_id = ?
            ORDER BY tag ASC
            """,
            (paper_id,),
        ).fetchall()
    return [row["tag"] for row in rows]


def get_paper(paper_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, workspace_id, doc_id, title, authors, year, created_at
            FROM papers
            WHERE id = ?
            """,
            (paper_id,),
        ).fetchone()
    return dict(row) if row else None


def ingest_paper(
    *,
    workspace_id: str,
    filename: str,
    data: bytes,
    save_dir: Path,
) -> tuple[str, PaperMetadata]:
    ingest_result = ingest_pdf(
        workspace_id=workspace_id,
        filename=filename,
        data=data,
        save_dir=save_dir,
    )
    metadata = extract_paper_metadata(Path(ingest_result.path))
    existing = find_paper_by_doc(workspace_id, ingest_result.doc_id)
    if existing:
        update_paper_metadata(
            paper_id=existing["id"],
            title=metadata.title,
            authors=metadata.authors,
            year=metadata.year,
        )
        return existing["id"], metadata
    paper_id = create_paper(
        workspace_id=workspace_id,
        doc_id=ingest_result.doc_id,
        title=metadata.title,
        authors=metadata.authors,
        year=metadata.year,
    )
    return paper_id, metadata


def ensure_paper(
    *,
    workspace_id: str,
    doc_id: str,
    metadata: PaperMetadata,
) -> str:
    existing = find_paper_by_doc(workspace_id, doc_id)
    if existing:
        update_paper_metadata(
            paper_id=existing["id"],
            title=metadata.title,
            authors=metadata.authors,
            year=metadata.year,
        )
        return existing["id"]
    return create_paper(
        workspace_id=workspace_id,
        doc_id=doc_id,
        title=metadata.title,
        authors=metadata.authors,
        year=metadata.year,
    )


def extract_paper_metadata(path: Path) -> PaperMetadata:
    parse_result = read_pdf(path)
    text = "\n".join(page.text for page in parse_result.pages[:2])
    metadata = extract_metadata(text)
    if metadata:
        return metadata

    try:
        prompt = metadata_fallback_prompt(text[:3000])
        response = chat(prompt=prompt, temperature=0.1)
        data = json.loads(response)
        return PaperMetadata(
            title=data.get("title", "unknown"),
            authors=data.get("authors", "unknown"),
            year=data.get("year", "unknown"),
        )
    except (ChatConfigError, json.JSONDecodeError) as exc:
        return PaperMetadata(title="unknown", authors="unknown", year="unknown")

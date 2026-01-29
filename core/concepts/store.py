from __future__ import annotations

import uuid
from datetime import datetime, timezone

from core.concepts.schema import ConceptCard, ConceptEvidence
from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_card(
    *, workspace_id: str, name: str, type: str, content: str
) -> str:
    card_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO concept_cards (
                id, workspace_id, name, type, content, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (card_id, workspace_id, name, type, content, _now_iso(), _now_iso()),
        )
        connection.commit()
    return card_id


def update_card(
    *, card_id: str, name: str, type: str, content: str
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE concept_cards
            SET name = ?, type = ?, content = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, type, content, _now_iso(), card_id),
        )
        connection.commit()


def list_cards(workspace_id: str) -> list[ConceptCard]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM concept_cards
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return [ConceptCard(**dict(row)) for row in rows]


def get_card(card_id: str) -> ConceptCard | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM concept_cards WHERE id = ?",
            (card_id,),
        ).fetchone()
    return ConceptCard(**dict(row)) if row else None


def add_evidence(
    *,
    card_id: str,
    doc_id: str,
    chunk_id: str,
    page_start: int | None,
    page_end: int | None,
    snippet: str | None,
) -> str:
    evidence_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO concept_evidence (
                id, card_id, doc_id, chunk_id, page_start, page_end, snippet, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                card_id,
                doc_id,
                chunk_id,
                page_start,
                page_end,
                snippet,
                _now_iso(),
            ),
        )
        connection.commit()
    return evidence_id


def list_evidence(card_id: str) -> list[ConceptEvidence]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM concept_evidence
            WHERE card_id = ?
            ORDER BY created_at ASC
            """,
            (card_id,),
        ).fetchall()
    return [ConceptEvidence(**dict(row)) for row in rows]


def search_cards(
    *, workspace_id: str, query: str, type_filter: str | None = None
) -> list[ConceptCard]:
    q = f"%{query.strip()}%"
    with get_connection() as connection:
        if type_filter:
            rows = connection.execute(
                """
                SELECT * FROM concept_cards
                WHERE workspace_id = ? AND type = ? AND (name LIKE ? OR content LIKE ?)
                ORDER BY created_at DESC
                """,
                (workspace_id, type_filter, q, q),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM concept_cards
                WHERE workspace_id = ? AND (name LIKE ? OR content LIKE ?)
                ORDER BY created_at DESC
                """,
                (workspace_id, q, q),
            ).fetchall()
    return [ConceptCard(**dict(row)) for row in rows]


def upsert_processing_mark(
    *,
    workspace_id: str,
    doc_id: str,
    processor: str,
    doc_hash: str,
) -> None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id FROM document_processing_marks
            WHERE workspace_id = ? AND doc_id = ? AND processor = ?
            """,
            (workspace_id, doc_id, processor),
        ).fetchone()
        if row:
            connection.execute(
                """
                UPDATE document_processing_marks
                SET doc_hash = ?, updated_at = ?
                WHERE id = ?
                """,
                (doc_hash, _now_iso(), row["id"]),
            )
        else:
            connection.execute(
                """
                INSERT INTO document_processing_marks (
                    id, workspace_id, doc_id, processor, doc_hash, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), workspace_id, doc_id, processor, doc_hash, _now_iso(), _now_iso()),
            )
        connection.commit()


def get_processing_mark(
    *, workspace_id: str, doc_id: str, processor: str
) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM document_processing_marks
            WHERE workspace_id = ? AND doc_id = ? AND processor = ?
            """,
            (workspace_id, doc_id, processor),
        ).fetchone()
    return dict(row) if row else None

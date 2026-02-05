from __future__ import annotations

import json
from datetime import datetime, timezone

from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_doc_index_assets(
    *,
    doc_id: str,
    summary_text: str | None,
    outline: dict | None,
    entities: list[str] | None,
) -> None:
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT doc_id FROM doc_index_assets WHERE doc_id = ?",
            (doc_id,),
        ).fetchone()
        outline_json = json.dumps(outline) if outline is not None else None
        entities_json = json.dumps(entities) if entities is not None else None
        if existing:
            connection.execute(
                """
                UPDATE doc_index_assets
                SET summary_text = ?, outline_json = ?, entities_json = ?, updated_at = ?
                WHERE doc_id = ?
                """,
                (summary_text, outline_json, entities_json, _now_iso(), doc_id),
            )
        else:
            connection.execute(
                """
                INSERT INTO doc_index_assets (doc_id, summary_text, outline_json, entities_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (doc_id, summary_text, outline_json, entities_json, _now_iso()),
            )
        connection.commit()


def get_doc_index_assets(doc_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT doc_id, summary_text, outline_json, entities_json, updated_at
            FROM doc_index_assets
            WHERE doc_id = ?
            """,
            (doc_id,),
        ).fetchone()
    return dict(row) if row else None

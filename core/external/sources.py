from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExternalSource:
    id: str
    workspace_id: str
    source_type: str
    params_json: str | None
    last_sync_at: str | None
    created_at: str
    updated_at: str


@dataclass
class ExternalMapping:
    id: str
    source_id: str
    external_id: str
    external_sub_id: str | None
    doc_id: str | None
    status: str | None
    meta_json: str | None
    created_at: str
    updated_at: str


def create_source(
    *,
    workspace_id: str,
    source_type: str,
    params: dict | None = None,
) -> str:
    source_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO external_sources (
                id, workspace_id, source_type, params_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                workspace_id,
                source_type,
                json.dumps(params or {}, ensure_ascii=False),
                _now_iso(),
                _now_iso(),
            ),
        )
        connection.commit()
    return source_id


def get_source(source_id: str) -> ExternalSource:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM external_sources WHERE id = ?",
            (source_id,),
        ).fetchone()
    if not row:
        raise RuntimeError("External source not found.")
    return ExternalSource(**dict(row))


def find_source(
    *, workspace_id: str, source_type: str, params: dict | None = None
) -> ExternalSource | None:
    params_json = json.dumps(params or {}, ensure_ascii=False)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM external_sources
            WHERE workspace_id = ? AND source_type = ? AND params_json = ?
            """,
            (workspace_id, source_type, params_json),
        ).fetchone()
    return ExternalSource(**dict(row)) if row else None


def touch_source(source_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE external_sources
            SET last_sync_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (_now_iso(), _now_iso(), source_id),
        )
        connection.commit()


def upsert_mapping(
    *,
    source_id: str,
    external_id: str,
    external_sub_id: str | None,
    doc_id: str | None,
    status: str,
    meta: dict | None = None,
) -> str:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id FROM external_mappings
            WHERE source_id = ? AND external_id = ? AND IFNULL(external_sub_id, '') = IFNULL(?, '')
            """,
            (source_id, external_id, external_sub_id or ""),
        ).fetchone()
        if row:
            mapping_id = row["id"]
            connection.execute(
                """
                UPDATE external_mappings
                SET doc_id = ?, status = ?, meta_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    doc_id,
                    status,
                    json.dumps(meta or {}, ensure_ascii=False),
                    _now_iso(),
                    mapping_id,
                ),
            )
            connection.commit()
            return mapping_id
        mapping_id = str(uuid.uuid4())
        connection.execute(
            """
            INSERT INTO external_mappings (
                id, source_id, external_id, external_sub_id, doc_id, status, meta_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mapping_id,
                source_id,
                external_id,
                external_sub_id,
                doc_id,
                status,
                json.dumps(meta or {}, ensure_ascii=False),
                _now_iso(),
                _now_iso(),
            ),
        )
        connection.commit()
    return mapping_id


def get_mapping(
    *, source_id: str, external_id: str, external_sub_id: str | None
) -> ExternalMapping | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM external_mappings
            WHERE source_id = ? AND external_id = ? AND IFNULL(external_sub_id, '') = IFNULL(?, '')
            """,
            (source_id, external_id, external_sub_id or ""),
        ).fetchone()
    return ExternalMapping(**dict(row)) if row else None


def list_mappings(source_id: str) -> list[ExternalMapping]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM external_mappings WHERE source_id = ?",
            (source_id,),
        ).fetchall()
    return [ExternalMapping(**dict(row)) for row in rows]

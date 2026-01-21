from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from infra.db import get_connection, get_workspaces_dir


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
            SELECT id, workspace_id, filename, path, created_at
            FROM documents
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return [dict(row) for row in rows]

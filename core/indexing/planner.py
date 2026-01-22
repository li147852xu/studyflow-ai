from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from infra.db import get_connection


@dataclass
class IndexPlan:
    doc_id: str | None
    sha256: str
    action: str  # "skip" | "update" | "create"


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def plan_document(workspace_id: str, path: Path) -> IndexPlan:
    sha256 = compute_sha256(path)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, sha256
            FROM documents
            WHERE workspace_id = ? AND path = ?
            """,
            (workspace_id, str(path)),
        ).fetchone()
    if row:
        doc_id = row["id"]
        if row["sha256"] == sha256:
            return IndexPlan(doc_id=doc_id, sha256=sha256, action="skip")
        return IndexPlan(doc_id=doc_id, sha256=sha256, action="update")
    return IndexPlan(doc_id=None, sha256=sha256, action="create")

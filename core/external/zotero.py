from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ZoteroAttachment:
    item_key: str
    attachment_key: str
    title: str | None
    file_path: Path


def _open_db(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def _storage_path(data_dir: Path, attachment_key: str, stored_path: str | None) -> Path | None:
    storage_dir = data_dir / "storage" / attachment_key
    if stored_path:
        if stored_path.startswith("storage:"):
            name = stored_path.split("storage:", 1)[1]
            candidate = storage_dir / name
            if candidate.exists():
                return candidate
        candidate = storage_dir / stored_path
        if candidate.exists():
            return candidate
    if storage_dir.exists():
        pdfs = list(storage_dir.glob("*.pdf"))
        if pdfs:
            return pdfs[0]
    return None


def list_pdf_attachments(data_dir: Path) -> list[ZoteroAttachment]:
    db_path = data_dir / "zotero.sqlite"
    if not db_path.exists():
        raise RuntimeError("zotero.sqlite not found in Zotero data directory.")
    attachments: list[ZoteroAttachment] = []
    with _open_db(db_path) as connection:
        rows = connection.execute(
            """
            SELECT items.itemID AS item_id,
                   items.key AS item_key,
                   attachments.itemID AS attachment_id,
                   attachments.key AS attachment_key,
                   itemAttachments.path AS attachment_path,
                   itemAttachments.contentType AS content_type
            FROM itemAttachments
            JOIN items AS attachments ON attachments.itemID = itemAttachments.itemID
            JOIN items ON items.itemID = itemAttachments.parentItemID
            WHERE itemAttachments.contentType LIKE '%pdf%'
            """
        ).fetchall()
    for row in rows:
        file_path = _storage_path(data_dir, row["attachment_key"], row["attachment_path"])
        if not file_path or not file_path.exists():
            continue
        attachments.append(
            ZoteroAttachment(
                item_key=row["item_key"],
                attachment_key=row["attachment_key"],
                title=None,
                file_path=file_path,
            )
        )
    return attachments

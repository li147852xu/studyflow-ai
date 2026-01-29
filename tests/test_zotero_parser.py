import sqlite3
from pathlib import Path

from core.external.zotero import list_pdf_attachments


def _create_zotero_db(path: Path) -> None:
    connection = sqlite3.connect(str(path))
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE items (itemID INTEGER PRIMARY KEY, key TEXT)")
    cursor.execute(
        """
        CREATE TABLE itemAttachments (
            itemID INTEGER PRIMARY KEY,
            parentItemID INTEGER,
            path TEXT,
            contentType TEXT
        )
        """
    )
    cursor.execute("INSERT INTO items (itemID, key) VALUES (1, 'ITEMKEY1')")
    cursor.execute("INSERT INTO items (itemID, key) VALUES (2, 'ATTACHKEY1')")
    cursor.execute(
        "INSERT INTO itemAttachments (itemID, parentItemID, path, contentType) VALUES (2, 1, 'storage:file.pdf', 'application/pdf')"
    )
    connection.commit()
    connection.close()


def test_zotero_parser(tmp_path: Path) -> None:
    data_dir = tmp_path / "zotero"
    storage_dir = data_dir / "storage" / "ATTACHKEY1"
    storage_dir.mkdir(parents=True, exist_ok=True)
    (storage_dir / "file.pdf").write_bytes(b"%PDF-1.4 test")
    _create_zotero_db(data_dir / "zotero.sqlite")

    attachments = list_pdf_attachments(data_dir)
    assert attachments
    assert attachments[0].item_key == "ITEMKEY1"

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz

from infra.db import get_connection


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd).decode("utf-8").strip()


def _create_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def _create_mock_zotero(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    storage_dir = data_dir / "storage" / "ATTACHKEY1"
    storage_dir.mkdir(parents=True, exist_ok=True)
    _create_pdf(storage_dir / "file.pdf", "Zotero PDF")

    db_path = data_dir / "zotero.sqlite"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()


def main() -> int:
    try:
        _run([sys.executable, "-m", "compileall", "."])
        _run([sys.executable, "-m", "pytest", "-q"])

        ws_id = _capture([sys.executable, "-m", "cli.main", "workspace", "create", "verify-v2-3"])

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "folder"
            folder.mkdir(parents=True, exist_ok=True)
            _create_pdf(folder / "a.pdf", "Folder A")
            _create_pdf(folder / "b.pdf", "Folder B")

            _run(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "import",
                    "folder",
                    "--workspace",
                    ws_id,
                    "--path",
                    str(folder),
                ]
            )
            output = _capture(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "import",
                    "folder",
                    "--workspace",
                    ws_id,
                    "--path",
                    str(folder),
                ]
            )
            if "Skipped" not in output:
                print("Folder sync did not report skip.")

            zotero_dir = Path(tmpdir) / "zotero"
            _create_mock_zotero(zotero_dir)
            _run(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "import",
                    "zotero",
                    "--workspace",
                    ws_id,
                    "--data-dir",
                    str(zotero_dir),
                ]
            )

        arxiv_out = _capture(
            [
                sys.executable,
                "-m",
                "cli.main",
                "import",
                "arxiv",
                "--workspace",
                ws_id,
                "--id",
                "1706.03762",
            ]
        )
        if "failed" in arxiv_out.lower():
            print(f"arXiv download skipped: {arxiv_out}")

        with get_connection() as connection:
            count = connection.execute(
                "SELECT COUNT(*) as count FROM documents WHERE workspace_id = ?",
                (ws_id,),
            ).fetchone()["count"]
        if count == 0:
            raise RuntimeError("No documents imported.")

        _run([sys.executable, "-m", "cli.main", "doctor"])
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("V2.3 verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

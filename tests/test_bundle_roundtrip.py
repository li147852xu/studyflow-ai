import os
import zipfile
from pathlib import Path

from infra.db import get_connection, get_workspaces_dir
from infra.models import init_db
from service.bundle_service import bundle_export, bundle_import
from service.workspace_service import create_workspace


def _insert_document(ws_id: str, doc_id: str, path: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (id, workspace_id, filename, path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (doc_id, ws_id, "doc.pdf", path, "2024-01-01T00:00:00Z"),
        )
        connection.commit()


def test_bundle_roundtrip(tmp_path: Path) -> None:
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("bundle")
    docs_dir = get_workspaces_dir() / ws_id / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = docs_dir / "doc.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")
    _insert_document(ws_id, "doc1", str(pdf_path))

    bundle_path = Path(bundle_export(workspace_id=ws_id, out_path=None, with_pdf=True, with_assets=False, with_prompts=False))
    assert bundle_path.exists()
    with zipfile.ZipFile(bundle_path, "r") as bundle:
        assert "manifest.json" in bundle.namelist()

    new_ws = bundle_import(path=str(bundle_path), rebuild_index=False)
    with get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) as count FROM documents WHERE workspace_id = ?",
            (new_ws,),
        ).fetchone()["count"]
    assert count == 1

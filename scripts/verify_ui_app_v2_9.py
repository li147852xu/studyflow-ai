from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import fitz

from infra.db import get_workspaces_dir
from infra.models import init_db
from infra.db import get_connection
from service.document_service import get_document, list_documents_by_type, set_document_type
from service.ingest_service import ingest_pdf
from service.workspace_service import create_workspace, delete_workspace, list_workspaces


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _safe_remove(path: Path, root: Path) -> None:
    path = path.resolve()
    root = root.resolve()
    if root not in path.parents:
        raise RuntimeError(f"Refusing to delete non-workspace path: {path}")
    if path.exists():
        shutil.rmtree(path)


def _ensure_test_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "StudyFlow-AI v2.9 verify")
    doc.save(path)
    doc.close()


def _cleanup_workspaces(keep_name: str = "test1") -> None:
    workspaces_dir = get_workspaces_dir()
    workspaces = list_workspaces()
    keep_ids = [ws["id"] for ws in workspaces if ws["name"] == keep_name]
    if not keep_ids:
        keep_ids = [create_workspace(keep_name)]
    for ws in workspaces:
        if ws["id"] in keep_ids:
            continue
        delete_workspace(ws["id"])
        _safe_remove(workspaces_dir / ws["id"], workspaces_dir)

    # Ensure only keep workspace remains
    remaining = list_workspaces()
    remaining_names = {ws["name"] for ws in remaining}
    if keep_name not in remaining_names:
        create_workspace(keep_name)

    with get_connection() as connection:
        connection.execute("DELETE FROM tasks")
        connection.execute("DELETE FROM recent_activity")
        connection.execute("DELETE FROM ui_history")
        connection.commit()


def main() -> int:
    init_db()

    _run(["python", "-m", "compileall", "."])
    _run(["pytest", "-q"])
    _run(["python", "-c", "import app.main"])

    test_ws = create_workspace("verify-temp-1")
    test_ws2 = create_workspace("verify-temp-2")

    workspaces_dir = get_workspaces_dir()
    pdf_path = workspaces_dir / test_ws / "uploads" / "verify_sample.pdf"
    _ensure_test_pdf(pdf_path)
    result = ingest_pdf(
        workspace_id=test_ws,
        filename=pdf_path.name,
        data=pdf_path.read_bytes(),
        save_dir=pdf_path.parent,
        doc_type="course",
        ocr_mode="off",
    )
    doc = get_document(result.doc_id)
    assert doc and doc.get("doc_type") == "course"
    set_document_type(doc_id=result.doc_id, doc_type="paper")
    paper_docs = list_documents_by_type(test_ws, "paper")
    assert any(item["id"] == result.doc_id for item in paper_docs)

    _cleanup_workspaces(keep_name="test1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

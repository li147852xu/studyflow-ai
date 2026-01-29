import sys
import tempfile
from pathlib import Path

import fitz
from dotenv import load_dotenv

from core.ui_state.guards import llm_ready
from core.ui_state.storage import add_history, get_setting, list_history, set_setting
from infra.db import get_connection, get_workspaces_dir
from infra.models import init_db
from service.ingest_service import ingest_pdf
from service.workspace_service import create_workspace


def _create_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "UI polish verification PDF.")
    doc.save(path)
    doc.close()


def main() -> int:
    load_dotenv()
    init_db()
    try:
        workspace_id = create_workspace("ui-polish-verify")
        set_setting(None, "last_workspace_id", workspace_id)
        set_setting(workspace_id, "retrieval_mode", "bm25")
        if get_setting(None, "last_workspace_id") != workspace_id:
            raise RuntimeError("Settings write/read failed (global).")
        if get_setting(workspace_id, "retrieval_mode") != "bm25":
            raise RuntimeError("Settings write/read failed (workspace).")

        add_history(
            workspace_id=workspace_id,
            action_type="chat",
            summary="Test history",
            preview="Hello world",
            source_ref=None,
            citations_count=0,
        )
        history = list_history(workspace_id, "chat")
        if not history:
            raise RuntimeError("History write/read failed.")

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "ui_test.pdf"
            _create_pdf(pdf_path)
            data = pdf_path.read_bytes()
        ingest = ingest_pdf(
            workspace_id=workspace_id,
            filename="ui_test.pdf",
            data=data,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )
        with get_connection() as connection:
            row = connection.execute(
                "SELECT path FROM documents WHERE id = ?",
                (ingest.doc_id,),
            ).fetchone()
        if not row or row["path"] != str(get_workspaces_dir() / workspace_id / "uploads" / "ui_test.pdf"):
            raise RuntimeError("Ingest path mismatch.")

        ready, reason = llm_ready("", "", "")
        if ready or "Missing" not in reason:
            raise RuntimeError("LLM guard did not report missing config.")

        __import__("app.main")
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("UI polish verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

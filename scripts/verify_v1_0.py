import sys
import tempfile
from pathlib import Path

import fitz
from dotenv import load_dotenv

from core.retrieval.bm25_index import build_bm25_index
from infra.db import get_workspaces_dir
from infra.models import init_db
from service.ingest_service import ingest_pdf
from service.retrieval_service import retrieve_hits_mode
from service.workspace_service import create_workspace


def _create_temp_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Stable core test document.")
    doc.save(path)
    doc.close()


def main() -> int:
    load_dotenv()
    init_db()
    try:
        workspace_id = create_workspace("verify-v1-0")
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "doc.pdf"
            _create_temp_pdf(pdf_path)
            data = pdf_path.read_bytes()

        ingest_pdf(
            workspace_id=workspace_id,
            filename="doc.pdf",
            data=data,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )
        build_bm25_index(workspace_id)
        hits, _ = retrieve_hits_mode(
            workspace_id=workspace_id, query="test", mode="bm25", top_k=5
        )
        if not hits:
            raise RuntimeError("BM25 query returned no hits.")
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("V1.0 core checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

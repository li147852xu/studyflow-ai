import os
import tempfile
from pathlib import Path

import fitz

from infra.db import get_workspaces_dir
from infra.models import init_db
from service.ingest_service import ingest_pdf
from service.retrieval_service import retrieve_hits_mode
from service.workspace_service import create_workspace
from core.retrieval.bm25_index import build_bm25_index


def _create_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Test PDF content for retrieval.")
    doc.save(path)
    doc.close()


def test_minimal_e2e(tmp_path: Path):
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("e2e")
    pdf_path = tmp_path / "doc.pdf"
    _create_pdf(pdf_path)
    data = pdf_path.read_bytes()
    ingest = ingest_pdf(
        workspace_id=ws_id,
        filename="doc.pdf",
        data=data,
        save_dir=get_workspaces_dir() / ws_id / "uploads",
    )
    build_bm25_index(ws_id)
    hits, mode = retrieve_hits_mode(
        workspace_id=ws_id, query="retrieval", mode="bm25", top_k=3
    )
    assert hits

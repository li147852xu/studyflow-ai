import sys
import tempfile
from pathlib import Path

import fitz
from dotenv import load_dotenv

from core.ingest.cite import build_citation
from core.retrieval.embedder import build_embedding_settings
from core.retrieval.vector_store import VectorStore, VectorStoreSettings
from infra.db import get_workspaces_dir
from infra.models import init_db
from service.chat_service import ChatConfigError, chat
from service.ingest_service import IngestError, ingest_pdf
from service.retrieval_service import build_or_refresh_index, retrieve_hits
from service.workspace_service import create_workspace, list_workspaces


def _create_temp_pdf(path: Path) -> None:
    doc = fitz.open()
    for idx in range(2):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"Page {idx + 1}\n\nThis is a test document for StudyFlow V0.0.3 retrieval.",
        )
    doc.save(path)
    doc.close()


def verify_workspace() -> str:
    print("Verify: workspace creation")
    init_db()
    workspace_id = create_workspace("verify-v0-0-3")
    workspaces = list_workspaces()
    if not any(ws["id"] == workspace_id for ws in workspaces):
        raise RuntimeError("Workspace was not persisted.")
    print(f"OK: workspace created ({workspace_id})")
    return workspace_id


def main() -> int:
    load_dotenv()
    try:
        workspace_id = verify_workspace()
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "sample.pdf"
            _create_temp_pdf(pdf_path)
            data = pdf_path.read_bytes()

        ingest_result = ingest_pdf(
            workspace_id=workspace_id,
            filename="sample.pdf",
            data=data,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )
        if ingest_result.chunk_count <= 0:
            raise RuntimeError("Ingest created no chunks.")
        print("OK: ingest completed")

        build_embedding_settings()

        index_result = build_or_refresh_index(workspace_id=workspace_id, reset=True)
        if index_result.indexed_count < ingest_result.chunk_count:
            raise RuntimeError("Indexed chunk count is lower than chunk count.")
        index_dir = get_workspaces_dir() / workspace_id / "index" / "chroma"
        if not index_dir.exists():
            raise RuntimeError("Vector index directory missing.")
        store = VectorStore(
            VectorStoreSettings(
                persist_directory=index_dir,
                collection_name=f"workspace_{workspace_id}",
            )
        )
        if store.count() < ingest_result.chunk_count:
            raise RuntimeError("Vector index count is less than chunk count.")
        print("OK: index build completed")

        hits = retrieve_hits(workspace_id=workspace_id, query="test document", top_k=8)
        if not hits:
            raise RuntimeError("No retrieval hits returned.")
        print("OK: retrieval hits returned")

        hit = hits[0]
        citation = build_citation(
            filename=hit.filename,
            page_start=hit.page_start,
            page_end=hit.page_end,
            text=hit.text,
        )
        rendered = citation.render()
        if hit.filename not in rendered or "p." not in rendered or not citation.snippet:
            raise RuntimeError("Citation output invalid.")
        print("OK: citation output valid")

        # Optional: verify pure LLM path if key is present
        try:
            response = chat(prompt="Reply with one word: hello.")
            if not response.strip():
                raise RuntimeError("Empty LLM response.")
            print("OK: LLM direct chat works without retrieval")
        except ChatConfigError as exc:
            print(f"SKIP: LLM chat unavailable ({exc})")

    except IngestError as exc:
        print(f"FAILED: {exc}")
        return 1
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("All V0.0.3 checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

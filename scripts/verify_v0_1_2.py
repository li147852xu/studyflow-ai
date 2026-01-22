import os
import sys
import tempfile
from pathlib import Path

import fitz
from dotenv import load_dotenv

from infra.db import get_workspaces_dir
from infra.models import init_db
from service.ingest_service import ingest_pdf
from service.presentation_service import generate_slides
from service.retrieval_service import build_or_refresh_index
from service.workspace_service import create_workspace


def _create_temp_pdf(path: Path) -> None:
    doc = fitz.open()
    for idx in range(3):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"Slide Source {idx + 1}\n\nThis is a test presentation document.",
        )
    doc.save(path)
    doc.close()


def _has_llm_key() -> bool:
    return bool(os.getenv("STUDYFLOW_LLM_API_KEY", "").strip())


def main() -> int:
    load_dotenv()
    init_db()
    try:
        workspace_id = create_workspace("verify-v0-1-2")
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "slides.pdf"
            _create_temp_pdf(pdf_path)
            data = pdf_path.read_bytes()

        ingest_result = ingest_pdf(
            workspace_id=workspace_id,
            filename="slides.pdf",
            data=data,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )
        build_or_refresh_index(workspace_id=workspace_id, reset=True)

        if not _has_llm_key():
            print("SKIP: LLM tests (missing STUDYFLOW_LLM_API_KEY).")
            return 0

        output = generate_slides(
            workspace_id=workspace_id,
            doc_id=ingest_result.doc_id,
            duration="10",
            save_outputs=False,
        )
        deck = output.deck
        if not deck.strip():
            raise RuntimeError("Deck is empty.")
        if "---" not in deck:
            raise RuntimeError("Deck missing Marp front matter or separators.")
        if deck.count("---") < 8:
            raise RuntimeError("Deck has insufficient slide separators.")
        if "Notes:" not in deck:
            raise RuntimeError("Deck missing speaker notes.")
        if not output.qa or len(output.qa) < 10:
            raise RuntimeError("Q&A list missing or incomplete.")
        if not output.citations:
            raise RuntimeError("Citations missing.")
        if "slides.pdf" not in "\n".join(output.citations):
            raise RuntimeError("Citations missing filename.")

    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("All V0.1.2 checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

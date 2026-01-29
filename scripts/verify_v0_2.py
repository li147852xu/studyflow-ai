import json
import os
import sys
import tempfile
from pathlib import Path

import fitz
from dotenv import load_dotenv

from core.retrieval.bm25_index import build_bm25_index
from infra.db import get_workspaces_dir
from infra.models import init_db
from service.ingest_service import ingest_pdf
from service.presentation_service import generate_slides
from service.retrieval_service import retrieve_hits_mode
from service.workspace_service import create_workspace


def _create_temp_pdf(path: Path, title: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        f"{title}\n\nThis is a test document for BM25/Hybrid verification.",
    )
    doc.save(path)
    doc.close()


def _has_llm_key() -> bool:
    return bool(os.getenv("STUDYFLOW_LLM_API_KEY", "").strip())


def _has_embed_model() -> bool:
    return bool(os.getenv("STUDYFLOW_EMBED_MODEL", "").strip())


def main() -> int:
    load_dotenv()
    init_db()
    try:
        workspace_id = create_workspace("verify-v0-2-a")
        workspace_id_b = create_workspace("verify-v0-2-b")

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_a = Path(tmpdir) / "a.pdf"
            pdf_b = Path(tmpdir) / "b.pdf"
            _create_temp_pdf(pdf_a, "Doc A")
            _create_temp_pdf(pdf_b, "Doc B")
            data_a = pdf_a.read_bytes()
            data_b = pdf_b.read_bytes()

        ingest_a = ingest_pdf(
            workspace_id=workspace_id,
            filename="a.pdf",
            data=data_a,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )
        ingest_pdf(
            workspace_id=workspace_id_b,
            filename="b.pdf",
            data=data_b,
            save_dir=get_workspaces_dir() / workspace_id_b / "uploads",
        )

        index_path = build_bm25_index(workspace_id)
        if not index_path.exists():
            raise RuntimeError("BM25 index file missing.")

        bm25_hits, used_mode = retrieve_hits_mode(
            workspace_id=workspace_id,
            query="test document",
            mode="bm25",
            top_k=8,
        )
        if not bm25_hits:
            raise RuntimeError("BM25 retrieval returned no hits.")
        if any(hit.workspace_id != workspace_id for hit in bm25_hits):
            raise RuntimeError("BM25 workspace filter failed.")

        if _has_embed_model():
            vec_hits, _ = retrieve_hits_mode(
                workspace_id=workspace_id,
                query="test document",
                mode="vector",
                top_k=8,
            )
            if not vec_hits:
                raise RuntimeError("Vector retrieval returned no hits.")

            hy_hits, used_mode = retrieve_hits_mode(
                workspace_id=workspace_id,
                query="test document",
                mode="hybrid",
                top_k=8,
            )
            if not hy_hits:
                raise RuntimeError("Hybrid retrieval returned no hits.")
            if used_mode not in ("hybrid", "bm25"):
                raise RuntimeError("Hybrid mode did not return expected mode.")
        else:
            print("SKIP: embeddings unavailable for vector/hybrid.")

        if not _has_llm_key():
            print("SKIP: LLM tests (missing STUDYFLOW_LLM_API_KEY).")
            return 0

        slides = generate_slides(
            workspace_id=workspace_id,
            doc_id=ingest_a.doc_id,
            duration="5",
            retrieval_mode="bm25",
            save_outputs=True,
        )
        if not slides.run_id:
            raise RuntimeError("run_id missing for slides.")
        log_path = (
            get_workspaces_dir() / workspace_id / "runs" / f"run_{slides.run_id}.json"
        )
        if not log_path.exists():
            raise RuntimeError("run log file missing.")
        data = json.loads(log_path.read_text(encoding="utf-8"))
        required = [
            "run_id",
            "timestamp",
            "workspace_id",
            "action_type",
            "input",
            "retrieval_mode",
            "retrieval_hits",
            "model",
            "embed_model",
            "latency_ms",
        ]
        for key in required:
            if key not in data:
                raise RuntimeError(f"run log missing field: {key}")

    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("All V0.2 checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

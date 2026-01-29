import os
import sys
import tempfile
from pathlib import Path

import fitz
from dotenv import load_dotenv

from infra.db import get_workspaces_dir
from infra.models import init_db
from service.paper_generate_service import aggregate_papers, generate_paper_card
from service.paper_service import add_tags, ingest_paper, list_papers
from service.retrieval_service import build_or_refresh_index
from service.workspace_service import create_workspace


def _create_temp_pdf(path: Path, title: str, authors: str, year: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        f"{title}\n{authors}\n{year}\n\nThis paper discusses methods and results.",
    )
    doc.save(path)
    doc.close()


def _has_llm_key() -> bool:
    return bool(os.getenv("STUDYFLOW_LLM_API_KEY", "").strip())


def main() -> int:
    load_dotenv()
    init_db()
    try:
        workspace_id = create_workspace("verify-v0-1-1")
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf1 = Path(tmpdir) / "paper1.pdf"
            pdf2 = Path(tmpdir) / "paper2.pdf"
            _create_temp_pdf(pdf1, "Paper One", "Alice; Bob", "2021")
            _create_temp_pdf(pdf2, "Paper Two", "Carol; Dan", "2020")
            data1 = pdf1.read_bytes()
            data2 = pdf2.read_bytes()

        paper1_id, meta1 = ingest_paper(
            workspace_id=workspace_id,
            filename="paper1.pdf",
            data=data1,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )
        paper2_id, meta2 = ingest_paper(
            workspace_id=workspace_id,
            filename="paper2.pdf",
            data=data2,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )

        if not meta1.title or not meta1.authors or not meta1.year:
            raise RuntimeError("Metadata extraction failed for paper1.")
        if not meta2.title or not meta2.authors or not meta2.year:
            raise RuntimeError("Metadata extraction failed for paper2.")

        add_tags(paper1_id, ["nlp", "transformer"])
        add_tags(paper2_id, ["retrieval"])

        build_or_refresh_index(workspace_id=workspace_id, reset=True)

        if not _has_llm_key():
            print("SKIP: LLM tests (missing STUDYFLOW_LLM_API_KEY).")
            return 0

        papers = list_papers(workspace_id)
        paper1 = next(p for p in papers if p["id"] == paper1_id)
        paper2 = next(p for p in papers if p["id"] == paper2_id)

        card = generate_paper_card(
            workspace_id=workspace_id,
            doc_id=paper1["doc_id"],
        )
        if not card.content.strip():
            raise RuntimeError("PAPER_CARD output empty.")
        if "Key contributions" not in card.content:
            raise RuntimeError("PAPER_CARD missing contributions section.")
        if "Strengths" not in card.content or "Weaknesses" not in card.content:
            raise RuntimeError("PAPER_CARD missing strengths/weaknesses.")
        if "Extension ideas" not in card.content:
            raise RuntimeError("PAPER_CARD missing extension ideas.")
        if "[" not in card.content or not card.citations:
            raise RuntimeError("PAPER_CARD citations missing.")

        agg_consensus = aggregate_papers(
            workspace_id=workspace_id,
            doc_ids=[paper1["doc_id"], paper2["doc_id"]],
            question="共识是什么？",
        )
        if not agg_consensus.content.strip():
            raise RuntimeError("Aggregation consensus output empty.")
        if not agg_consensus.citations:
            raise RuntimeError("Aggregation citations missing.")
        if not _citations_cover_both_papers(
            agg_consensus.citations, paper1["filename"], paper2["filename"]
        ):
            raise RuntimeError("Aggregation citations do not cover both papers.")

        agg_related = aggregate_papers(
            workspace_id=workspace_id,
            doc_ids=[paper1["doc_id"], paper2["doc_id"]],
            question="related work 应该怎么分段？",
        )
        if not agg_related.content.strip():
            raise RuntimeError("Aggregation related work output empty.")

    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("All V0.1.1 checks passed.")
    return 0


def _citations_cover_both_papers(
    citations: list[str], filename1: str, filename2: str
) -> bool:
    joined = "\n".join(citations)
    return filename1 in joined and filename2 in joined


if __name__ == "__main__":
    sys.exit(main())

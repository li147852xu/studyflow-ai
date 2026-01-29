import sys

import requests
from dotenv import load_dotenv

from core.ingest.cite import build_citation
from infra.db import get_workspaces_dir
from infra.models import init_db
from service.ingest_service import IngestError, ingest_pdf
from service.retrieval_service import (
    RetrievalError,
    answer_with_retrieval,
    build_or_refresh_index,
)
from service.workspace_service import create_workspace

PDF_URL = "https://arxiv.org/pdf/1706.03762.pdf"


def download_pdf() -> bytes:
    response = requests.get(PDF_URL, timeout=60)
    response.raise_for_status()
    return response.content


def main() -> int:
    load_dotenv()
    init_db()
    workspace_id = create_workspace("realflow-v0-0-3")
    try:
        data = download_pdf()
        ingest_result = ingest_pdf(
            workspace_id=workspace_id,
            filename="attention_is_all_you_need.pdf",
            data=data,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )
        print(
            f"Ingested {ingest_result.page_count} pages, {ingest_result.chunk_count} chunks."
        )

        build_or_refresh_index(workspace_id=workspace_id, reset=True)
        print("Vector index built.")

        question = "What is the main contribution of the Transformer architecture?"
        answer, hits, citations, run_id = answer_with_retrieval(
            workspace_id=workspace_id, query=question
        )
        print("Answer:")
        print(answer)
        print("\nRetrieval Hits:")
        for idx, hit in enumerate(hits, start=1):
            citation = build_citation(
                filename=hit.filename,
                page_start=hit.page_start,
                page_end=hit.page_end,
                text=hit.text,
            )
            print(f"[{idx}] score={hit.score:.4f} {citation.page_label}")
            print(citation.snippet)
        print("\nCitations:")
        for citation in citations:
            print(citation)

    except RetrievalError as exc:
        print(f"FAILED: {exc}")
        return 1
    except IngestError as exc:
        print(f"FAILED: {exc}")
        return 1
    except requests.RequestException as exc:
        print(f"FAILED: download error: {exc}")
        return 1
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("Real flow V0.0.3 completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

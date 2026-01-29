import sys

import requests
from dotenv import load_dotenv

from infra.db import get_workspaces_dir
from infra.models import init_db
from service.course_service import create_course, generate_cheatsheet, generate_overview, link_document
from service.ingest_service import ingest_pdf
from service.retrieval_service import build_or_refresh_index
from service.workspace_service import create_workspace

PDF_URL = "https://arxiv.org/pdf/1706.03762.pdf"


def download_pdf() -> bytes:
    response = requests.get(PDF_URL, timeout=60)
    response.raise_for_status()
    return response.content


def main() -> int:
    load_dotenv()
    init_db()
    workspace_id = create_workspace("realflow-v0-1")
    course_id = create_course(workspace_id, "Attention Course")
    try:
        data = download_pdf()
        ingest_result = ingest_pdf(
            workspace_id=workspace_id,
            filename="attention_is_all_you_need.pdf",
            data=data,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )
        link_document(course_id, ingest_result.doc_id)
        print(
            f"Ingested {ingest_result.page_count} pages, {ingest_result.chunk_count} chunks."
        )
        build_or_refresh_index(workspace_id=workspace_id, reset=True)

        overview = generate_overview(
            workspace_id=workspace_id,
            course_id=course_id,
        )
        print("COURSE_OVERVIEW:")
        print(overview.content)
        print("\nCitations:")
        for citation in overview.citations:
            print(citation)

        cheatsheet = generate_cheatsheet(
            workspace_id=workspace_id,
            course_id=course_id,
        )
        print("\nEXAM_CHEATSHEET:")
        print(cheatsheet.content)
        print("\nCitations:")
        for citation in cheatsheet.citations:
            print(citation)

    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("Real flow V0.1 completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

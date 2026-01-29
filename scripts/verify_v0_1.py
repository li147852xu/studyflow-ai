import os
import sys
import tempfile
from pathlib import Path

import fitz
from dotenv import load_dotenv

from infra.db import get_workspaces_dir
from infra.models import init_db
from service.course_service import (
    create_course,
    explain_selection,
    generate_cheatsheet,
    generate_overview,
    link_document,
)
from service.ingest_service import ingest_pdf
from service.retrieval_service import build_or_refresh_index
from service.workspace_service import create_workspace


def _create_temp_pdf(path: Path) -> None:
    doc = fitz.open()
    for idx in range(3):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"Lecture {idx + 1}\n\nThis is a test course document for StudyFlow V0.1.",
        )
    doc.save(path)
    doc.close()


def _has_llm_key() -> bool:
    return bool(os.getenv("STUDYFLOW_LLM_API_KEY", "").strip())


def main() -> int:
    load_dotenv()
    init_db()
    try:
        workspace_id = create_workspace("verify-v0-1")
        course_id = create_course(workspace_id, "Test Course")

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
        link_document(course_id, ingest_result.doc_id)

        build_or_refresh_index(workspace_id=workspace_id, reset=True)

        if not _has_llm_key():
            print("SKIP: LLM tests (missing STUDYFLOW_LLM_API_KEY).")
            return 0

        overview = generate_overview(
            workspace_id=workspace_id,
            course_id=course_id,
        )
        if not overview.content.strip():
            raise RuntimeError("Empty COURSE_OVERVIEW output.")
        if overview.content.count("\n") < 5:
            raise RuntimeError("COURSE_OVERVIEW lacks enough bullet points.")
        if "[" not in overview.content:
            raise RuntimeError("COURSE_OVERVIEW missing citations.")
        if not overview.citations:
            raise RuntimeError("COURSE_OVERVIEW citations missing.")

        cheatsheet = generate_cheatsheet(
            workspace_id=workspace_id,
            course_id=course_id,
        )
        required_sections = [
            "Definitions",
            "Key Formulas",
            "Typical Question Types",
            "Common Pitfalls",
        ]
        for section in required_sections:
            if section not in cheatsheet.content:
                raise RuntimeError(f"Cheatsheet missing section: {section}")
        if "[" not in cheatsheet.content:
            raise RuntimeError("CHEATSHEET missing citations.")
        if not cheatsheet.citations:
            raise RuntimeError("CHEATSHEET citations missing.")

        for mode in ["plain", "example", "pitfall", "link_prev"]:
            result = explain_selection(
                workspace_id=workspace_id,
                course_id=course_id,
                selection="Self-attention enables parallel processing.",
                mode=mode,
            )
            if not result.content.strip():
                raise RuntimeError(f"Explain selection failed for mode: {mode}")

    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("All V0.1 checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

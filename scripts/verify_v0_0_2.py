import sys
import tempfile
from pathlib import Path

import fitz

from core.ingest.cite import build_citation
from infra.db import get_workspaces_dir
from infra.models import init_db
from service.ingest_service import IngestError, get_random_chunks, ingest_pdf
from service.workspace_service import create_workspace, list_workspaces


def _create_temp_pdf(path: Path) -> None:
    doc = fitz.open()
    for idx in range(2):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"Page {idx + 1}\n\nThis is a test document for StudyFlow V0.0.2.",
        )
    doc.save(path)
    doc.close()


def verify_workspace() -> str:
    print("Verify: workspace creation")
    init_db()
    workspace_id = create_workspace("verify-v0-0-2")
    workspaces = list_workspaces()
    if not any(ws["id"] == workspace_id for ws in workspaces):
        raise RuntimeError("Workspace was not persisted.")
    print(f"OK: workspace created ({workspace_id})")
    return workspace_id


def verify_ingest(workspace_id: str) -> tuple[str, int]:
    print("Verify: PDF ingest")
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "sample.pdf"
        _create_temp_pdf(pdf_path)
        data = pdf_path.read_bytes()
        result = ingest_pdf(
            workspace_id=workspace_id,
            filename="sample.pdf",
            data=data,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )

    if result.page_count != 2:
        raise RuntimeError("page_count does not match expected value.")
    if result.chunk_count <= 0:
        raise RuntimeError("No chunks were created.")
    print(f"OK: ingest created {result.chunk_count} chunks.")
    return result.doc_id, result.page_count


def verify_chunks(doc_id: str, page_count: int) -> None:
    print("Verify: chunk page ranges")
    chunks = get_random_chunks(doc_id, limit=10)
    if not chunks:
        raise RuntimeError("No chunks found for validation.")
    for chunk in chunks:
        if not (1 <= chunk["page_start"] <= page_count):
            raise RuntimeError("chunk page_start out of range.")
        if not (1 <= chunk["page_end"] <= page_count):
            raise RuntimeError("chunk page_end out of range.")
    print("OK: chunk page ranges valid.")


def verify_citation(doc_id: str, filename: str) -> None:
    print("Verify: citation output")
    chunks = get_random_chunks(doc_id, limit=1)
    if not chunks:
        raise RuntimeError("No chunks for citation.")
    chunk = chunks[0]
    citation = build_citation(
        filename=filename,
        page_start=chunk["page_start"],
        page_end=chunk["page_end"],
        text=chunk["text"],
    )
    rendered = citation.render()
    if filename not in rendered or "p." not in rendered or not citation.snippet:
        raise RuntimeError("Citation output missing required fields.")
    print("OK: citation output valid.")


def verify_dedup(workspace_id: str, doc_id: str, data: bytes) -> None:
    print("Verify: dedup ingest")
    result = ingest_pdf(
        workspace_id=workspace_id,
        filename="sample.pdf",
        data=data,
        save_dir=get_workspaces_dir() / workspace_id / "uploads",
    )
    if not result.skipped or result.doc_id != doc_id:
        raise RuntimeError("Duplicate ingest was not skipped.")
    print("OK: duplicate ingest skipped.")


def main() -> int:
    try:
        workspace_id = verify_workspace()
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "sample.pdf"
            _create_temp_pdf(pdf_path)
            data = pdf_path.read_bytes()
        result = ingest_pdf(
            workspace_id=workspace_id,
            filename="sample.pdf",
            data=data,
            save_dir=get_workspaces_dir() / workspace_id / "uploads",
        )
        if result.page_count != 2 or result.chunk_count <= 0:
            raise RuntimeError("Ingest result invalid.")
        verify_chunks(result.doc_id, result.page_count)
        verify_citation(result.doc_id, result.filename)
        verify_dedup(workspace_id, result.doc_id, data)
    except IngestError as exc:
        print(f"FAILED: {exc}")
        return 1
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1
    print("All V0.0.2 checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

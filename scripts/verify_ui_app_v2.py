from __future__ import annotations

import compileall
import time

import fitz

from app.adapters import facade
from core.ui_state.guards import llm_ready
from service.workspace_service import create_workspace


def _build_sample_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "StudyFlow UI verify", fontsize=12)
    data = doc.tobytes()
    doc.close()
    return data


def main() -> None:
    print("Running compileall...")
    compile_ok = compileall.compile_dir(".", quiet=1)
    if not compile_ok:
        raise SystemExit("compileall failed.")

    print("Importing app.main...")
    import app.main  # noqa: F401

    print("Creating temp workspace and importing PDF...")
    workspace_id = create_workspace(f"ui-verify-{int(time.time())}")
    pdf_bytes = _build_sample_pdf()
    result = facade.import_and_process(
        workspace_id=workspace_id,
        filename="ui_verify.pdf",
        data=pdf_bytes,
        ocr_mode="auto",
        ocr_threshold=50,
    )
    if not result.ok:
        raise SystemExit(f"Import failed: {result.error}")

    status = facade.workspace_status(workspace_id)
    if not status.ok or not status.data:
        raise SystemExit(f"Workspace status failed: {status.error}")
    payload = status.data
    if payload.get("doc_count", 0) < 1:
        raise SystemExit("Workspace status shows no documents.")

    llm_ok, _ = llm_ready("", "", "")
    if llm_ok:
        raise SystemExit("LLM readiness should be false without credentials.")

    print("UI v2 verification checks passed.")


if __name__ == "__main__":
    main()

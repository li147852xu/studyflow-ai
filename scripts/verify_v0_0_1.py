import os
import sys
import tempfile
from pathlib import Path

from infra.models import init_db
from service.chat_service import ChatConfigError, chat, build_settings
from service.document_service import save_document_bytes
from service.workspace_service import create_workspace, list_workspaces


def _make_test_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n% StudyFlow Test PDF\n1 0 obj\n<<>>\nendobj\nxref\n0 1\n0000000000 65535 f\ntrailer\n<<>>\nstartxref\n9\n%%EOF\n"


def verify_workspace() -> str:
    print("Verify: workspace creation")
    init_db()
    workspace_id = create_workspace("verify-workspace")
    workspaces = list_workspaces()
    if not any(ws["id"] == workspace_id for ws in workspaces):
        raise RuntimeError("Workspace was not persisted.")
    print(f"OK: workspace created ({workspace_id})")
    return workspace_id


def verify_upload(workspace_id: str) -> Path:
    print("Verify: PDF upload and save")
    pdf_bytes = _make_test_pdf_bytes()
    result = save_document_bytes(workspace_id, "verify.pdf", pdf_bytes)
    saved_path = Path(result["path"])
    if not saved_path.exists() or saved_path.stat().st_size == 0:
        raise RuntimeError("Saved PDF file is missing or empty.")
    print(f"OK: PDF saved to {saved_path}")
    return saved_path


def verify_llm() -> None:
    print("Verify: LLM config handling")
    try:
        build_settings(
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            api_key="",
        )
        raise RuntimeError("Expected missing API key error.")
    except ChatConfigError as exc:
        print(f"OK: missing key detected ({exc})")

    base_url = os.getenv("STUDYFLOW_LLM_BASE_URL", "").strip()
    model = os.getenv("STUDYFLOW_LLM_MODEL", "").strip()
    api_key = os.getenv("STUDYFLOW_LLM_API_KEY", "").strip()
    if not (base_url and model and api_key):
        print("SKIP: LLM call (missing env config).")
        return

    print("Verify: LLM call")
    try:
        response = chat(
            prompt="Reply with one word: hello.",
            base_url=base_url,
            api_key=api_key,
            model=model,
        )
        if not response.strip():
            raise RuntimeError("LLM response was empty.")
        print("OK: LLM call succeeded.")
    except Exception as exc:
        raise RuntimeError(f"LLM call failed: {exc}") from exc


def main() -> int:
    try:
        workspace_id = verify_workspace()
        verify_upload(workspace_id)
        verify_llm()
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1
    print("All V0.0.1 checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

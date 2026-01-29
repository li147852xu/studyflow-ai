from __future__ import annotations

import fitz

from app.components.chat_panel import render_chat_panel
from app.components.dialogs import confirm_action
from app.components.help_view import render_help
from app.components.inspector import render_citations
from app.components.layout import three_column_layout
from app.components.library_view import render_library_view
from app.components.sidebar import render_sidebar
from app.components.workbench_view import render_workbench_list
from core.ui_state.storage import add_history, get_setting, list_history, set_setting
from infra.db import get_workspaces_dir
from infra.models import init_db
from service.document_service import list_documents
from service.ingest_service import ingest_pdf
from service.workspace_service import create_workspace, list_workspaces


def _make_test_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "StudyFlow AI test PDF")
    data = doc.tobytes()
    doc.close()
    return data


def main() -> None:
    init_db()
    # 1) components import check
    _ = (
        three_column_layout,
        render_sidebar,
        render_library_view,
        render_workbench_list,
        render_chat_panel,
        render_help,
        confirm_action,
        render_citations,
    )

    # 2) workspace create/list
    workspace_id = create_workspace("ui-refactor-check")
    workspaces = list_workspaces()
    assert any(ws["id"] == workspace_id for ws in workspaces)

    # 3) PDF ingest flow callable
    pdf_bytes = _make_test_pdf()
    result = ingest_pdf(
        workspace_id=workspace_id,
        filename="ui_refactor_test.pdf",
        data=pdf_bytes,
        save_dir=get_workspaces_dir() / workspace_id / "uploads",
    )
    assert result.doc_id

    # 4) library list data structure load
    docs = list_documents(workspace_id)
    assert len(docs) >= 1

    # 5) history read/write
    add_history(
        workspace_id=workspace_id,
        action_type="ui_refactor_check",
        summary="History roundtrip",
        preview="OK",
        source_ref=result.doc_id,
        citations_count=0,
    )
    history = list_history(workspace_id, "ui_refactor_check")
    assert history

    # 6) settings read/write
    set_setting(workspace_id, "ui_refactor_key", "ok")
    assert get_setting(workspace_id, "ui_refactor_key") == "ok"

    print("verify_ui_refactor: OK")


if __name__ == "__main__":
    main()

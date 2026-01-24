import os
from pathlib import Path

from infra.models import init_db
from service.workspace_service import create_workspace
from service.asset_service import create_asset_version, list_versions, set_active, read_version
from core.retrieval.retriever import Hit


def test_asset_versioning(tmp_path: Path):
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("assets")
    hits = [
        Hit(
            chunk_id="c1",
            doc_id="d1",
            workspace_id=ws_id,
            filename="doc.pdf",
            page_start=1,
            page_end=1,
            text="Sample text",
            score=0.9,
        )
    ]
    v1 = create_asset_version(
        workspace_id=ws_id,
        kind="course_overview",
        ref_id="course-1",
        content="First version",
        content_type="text",
        run_id="run-1",
        model="test-model",
        prompt_version="v1",
        hits=hits,
    )
    v2 = create_asset_version(
        workspace_id=ws_id,
        kind="course_overview",
        ref_id="course-1",
        content="Second version",
        content_type="text",
        run_id="run-2",
        model="test-model",
        prompt_version="v1",
        hits=hits,
    )
    versions = list_versions(v1.asset_id)
    assert len(versions) == 2
    set_active(v1.asset_id, v1.id)
    view = read_version(v1.asset_id, v2.id)
    assert "Second version" in view.content

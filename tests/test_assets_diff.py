import os
from pathlib import Path

from infra.models import init_db
from service.workspace_service import create_workspace
from service.asset_service import create_asset_version, diff_versions
from core.retrieval.retriever import Hit


def test_assets_diff(tmp_path: Path):
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("assets-diff")
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
        kind="paper_card",
        ref_id="doc-1",
        content="Line A",
        content_type="text",
        run_id="run-1",
        model="test-model",
        provider=None,
        temperature=None,
        max_tokens=None,
        retrieval_mode=None,
        embed_model=None,
        seed=None,
        prompt_version="v1",
        hits=hits,
    )
    v2 = create_asset_version(
        workspace_id=ws_id,
        kind="paper_card",
        ref_id="doc-1",
        content="Line B",
        content_type="text",
        run_id="run-2",
        model="test-model",
        provider=None,
        temperature=None,
        max_tokens=None,
        retrieval_mode=None,
        embed_model=None,
        seed=None,
        prompt_version="v1",
        hits=hits,
    )
    diff = diff_versions(v1.asset_id, v1.id, v2.id)
    assert "-Line A" in diff
    assert "+Line B" in diff

import os
from pathlib import Path

from core.concepts.store import (
    add_evidence,
    create_card,
    get_processing_mark,
    list_cards,
    list_evidence,
    search_cards,
    upsert_processing_mark,
)
from infra.models import init_db
from service.workspace_service import create_workspace


def test_concepts_store(tmp_path: Path) -> None:
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("concepts")
    card_id = create_card(
        workspace_id=ws_id,
        name="Self-Attention",
        type="method",
        content="Key idea: weighted sum of values.",
    )
    add_evidence(
        card_id=card_id,
        doc_id="doc1",
        chunk_id="doc1:0",
        page_start=1,
        page_end=1,
        snippet="Self-attention is ...",
    )
    cards = list_cards(ws_id)
    assert cards
    evidence = list_evidence(card_id)
    assert evidence
    results = search_cards(workspace_id=ws_id, query="attention")
    assert results
    upsert_processing_mark(
        workspace_id=ws_id,
        doc_id="doc1",
        processor="concepts",
        doc_hash="hash1",
    )
    mark = get_processing_mark(workspace_id=ws_id, doc_id="doc1", processor="concepts")
    assert mark

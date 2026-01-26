import os
from pathlib import Path

from infra.models import init_db
from infra.db import get_connection
from service.workspace_service import create_workspace
from service.concepts_service import build_concept_cards
from service.course_service import create_course, link_document
from core.retrieval.retriever import Hit


def _insert_document(ws_id: str, doc_id: str, sha256: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (id, workspace_id, filename, path, sha256, doc_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, ws_id, "doc.pdf", "path", sha256, "course", "2024-01-01T00:00:00Z"),
        )
        connection.commit()


def test_concepts_incremental(monkeypatch, tmp_path: Path) -> None:
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("concepts-inc")
    _insert_document(ws_id, "doc1", "hash1")
    course_id = create_course(ws_id, "Course")
    link_document(course_id, "doc1")

    def fake_build(*args, **kwargs):
        return type(
            "Result",
            (),
            {
                "cards": [
                    {"name": "Card", "type": "definition", "content": "C", "evidence": [1]}
                ],
                "hits": [
                    Hit(
                        chunk_id="doc1:0",
                        doc_id="doc1",
                        workspace_id=ws_id,
                        filename="doc.pdf",
                        page_start=1,
                        page_end=1,
                        text="text",
                        score=0.9,
                    )
                ],
                "citations": [],
                "retrieval_mode": "vector",
                "prompt_version": "v1",
            },
        )()

    monkeypatch.setattr("service.concepts_service.build_concepts", fake_build)
    result = build_concept_cards(
        workspace_id=ws_id,
        retrieval_mode="vector",
        paper_ids=None,
        course_id=course_id,
    )
    assert result["cards_created"] == 1
    # incremental should skip if hash unchanged
    result2 = build_concept_cards(
        workspace_id=ws_id,
        retrieval_mode="vector",
        paper_ids=None,
        course_id=course_id,
        incremental=True,
    )
    assert result2.get("skipped")

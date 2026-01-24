import os
from pathlib import Path

from infra.models import init_db
from infra.db import get_connection
from service.workspace_service import create_workspace
from service.related_service import create_related_project, update_related_project
from core.retrieval.retriever import Hit


def _insert_document(ws_id: str, doc_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (id, workspace_id, filename, path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (doc_id, ws_id, f"{doc_id}.pdf", "path", "2024-01-01T00:00:00Z"),
        )
        connection.commit()


def _insert_paper(ws_id: str, doc_id: str, paper_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO papers (id, workspace_id, doc_id, title, authors, year, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (paper_id, ws_id, doc_id, "Title", "Author", "2024", "2024-01-01T00:00:00Z"),
        )
        connection.commit()


def test_related_manager(monkeypatch, tmp_path: Path) -> None:
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("related")
    _insert_document(ws_id, "doc1")
    _insert_document(ws_id, "doc2")
    _insert_paper(ws_id, "doc1", "paper1")
    _insert_paper(ws_id, "doc2", "paper2")

    def fake_build(*args, **kwargs):
        return type(
            "Result",
            (),
            {
                "comparison_axes": ["novelty"],
                "sections": [{"title": "Section A", "bullets": ["[1] bullet"]}],
                "draft": "Draft [1]",
                "hits": [
                    Hit(
                        chunk_id="doc1:0",
                        doc_id="doc1",
                        workspace_id=ws_id,
                        filename="doc1.pdf",
                        page_start=1,
                        page_end=1,
                        text="text",
                        score=0.9,
                    )
                ],
                "citations": ["[1] doc1 (p.1) text"],
                "retrieval_mode": "vector",
                "prompt_version": "v1",
            },
        )()

    def fake_update(*args, **kwargs):
        result = fake_build()
        result.insert_suggestions = ["Add to Section A"]
        return result

    monkeypatch.setattr("service.related_service.build_related", fake_build)
    monkeypatch.setattr("service.related_service.update_related", fake_update)

    created = create_related_project(
        workspace_id=ws_id,
        paper_ids=["paper1", "paper2"],
        topic="Topic",
        retrieval_mode="vector",
    )
    assert created["project_id"]
    updated = update_related_project(
        workspace_id=ws_id,
        project_id=created["project_id"],
        add_paper_ids=["paper1"],
        retrieval_mode="vector",
    )
    assert updated["insert_suggestions"]

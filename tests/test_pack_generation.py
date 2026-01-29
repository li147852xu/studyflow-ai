import os
import zipfile
from pathlib import Path

from core.retrieval.retriever import Hit
from infra.db import get_connection
from infra.models import init_db
from service.asset_service import create_asset_version
from service.pack_service import make_pack
from service.workspace_service import create_workspace


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


def _insert_course(ws_id: str, course_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO courses (id, workspace_id, name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (course_id, ws_id, "Course", "2024-01-01T00:00:00Z"),
        )
        connection.commit()


def _insert_related_project(ws_id: str, project_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO related_projects (id, workspace_id, topic, comparison_axes_json, current_draft, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, ws_id, "Topic", "[]", "Draft", "2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z"),
        )
        connection.execute(
            """
            INSERT INTO related_sections (id, project_id, section_index, title, bullets_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("section1", project_id, 0, "Section", "[]", "2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z"),
        )
        connection.commit()


def test_pack_generation(tmp_path: Path) -> None:
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("packs")
    _insert_document(ws_id, "doc1")
    _insert_course(ws_id, "course1")
    _insert_related_project(ws_id, "project1")

    hit = Hit(
        chunk_id="doc1:0",
        doc_id="doc1",
        workspace_id=ws_id,
        filename="doc1.pdf",
        page_start=1,
        page_end=1,
        text="text",
        score=0.9,
    )
    create_asset_version(
        workspace_id=ws_id,
        kind="course_cheatsheet",
        ref_id="course1",
        content="Cheatsheet",
        content_type="text",
        run_id=None,
        model=None,
        provider=None,
        temperature=None,
        max_tokens=None,
        retrieval_mode=None,
        embed_model=None,
        seed=None,
        prompt_version="v1",
        hits=[hit],
    )
    create_asset_version(
        workspace_id=ws_id,
        kind="related_work",
        ref_id="project1",
        content="Draft",
        content_type="text",
        run_id=None,
        model=None,
        provider=None,
        temperature=None,
        max_tokens=None,
        retrieval_mode=None,
        embed_model=None,
        seed=None,
        prompt_version="v1",
        hits=[hit],
    )

    slides_pack = make_pack(workspace_id=ws_id, pack_type="slides", source_id="doc1")
    exam_pack = make_pack(workspace_id=ws_id, pack_type="exam", source_id="course1")
    related_pack = make_pack(workspace_id=ws_id, pack_type="related", source_id="project1")

    for pack in [slides_pack, exam_pack, related_pack]:
        assert Path(pack).exists()
        with zipfile.ZipFile(pack, "r") as bundle:
            assert "manifest.json" in bundle.namelist()

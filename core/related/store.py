from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from infra.db import get_connection
from core.related.schema import RelatedProject, RelatedSection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_project(
    *, workspace_id: str, topic: str, comparison_axes: list[str], draft: str
) -> str:
    project_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO related_projects (
                id, workspace_id, topic, comparison_axes_json, current_draft, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                workspace_id,
                topic,
                json.dumps(comparison_axes, ensure_ascii=False),
                draft,
                _now_iso(),
                _now_iso(),
            ),
        )
        connection.commit()
    return project_id


def update_project(
    *, project_id: str, comparison_axes: list[str], draft: str
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE related_projects
            SET comparison_axes_json = ?, current_draft = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(comparison_axes, ensure_ascii=False), draft, _now_iso(), project_id),
        )
        connection.commit()


def get_project(project_id: str) -> RelatedProject:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM related_projects WHERE id = ?",
            (project_id,),
        ).fetchone()
    if not row:
        raise RuntimeError("Related project not found.")
    return RelatedProject(**dict(row))


def list_projects(workspace_id: str) -> list[RelatedProject]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM related_projects
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return [RelatedProject(**dict(row)) for row in rows]


def replace_sections(
    *, project_id: str, sections: list[dict]
) -> list[str]:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM related_sections WHERE project_id = ?",
            (project_id,),
        )
        connection.execute(
            "DELETE FROM related_candidates WHERE project_id = ?",
            (project_id,),
        )
        section_ids: list[str] = []
        for idx, section in enumerate(sections):
            section_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO related_sections (
                    id, project_id, section_index, title, bullets_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    section_id,
                    project_id,
                    idx,
                    section.get("title", f"Section {idx+1}"),
                    json.dumps(section.get("bullets", []), ensure_ascii=False),
                    _now_iso(),
                    _now_iso(),
                ),
            )
            section_ids.append(section_id)
        connection.commit()
    return section_ids


def list_sections(project_id: str) -> list[RelatedSection]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM related_sections
            WHERE project_id = ?
            ORDER BY section_index ASC
            """,
            (project_id,),
        ).fetchall()
    return [RelatedSection(**dict(row)) for row in rows]


def add_candidates(
    *, project_id: str, section_id: str, paper_ids: list[str]
) -> None:
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO related_candidates (
                id, project_id, section_id, paper_id, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (str(uuid.uuid4()), project_id, section_id, paper_id, _now_iso())
                for paper_id in paper_ids
            ],
        )
        connection.commit()


def list_candidates(project_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM related_candidates
            WHERE project_id = ?
            """,
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]

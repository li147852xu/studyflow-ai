from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_project(
    *,
    workspace_id: str,
    title: str,
    goal: str | None = None,
    scope: str | None = None,
) -> str:
    project_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO research_project (id, workspace_id, title, goal, scope, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, workspace_id, title, goal, scope, _now_iso()),
        )
        connection.commit()
    return project_id


def update_project(
    *,
    project_id: str,
    title: str,
    goal: str | None,
    scope: str | None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE research_project
            SET title = ?, goal = ?, scope = ?
            WHERE id = ?
            """,
            (title, goal, scope, project_id),
        )
        connection.commit()


def list_projects(workspace_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, workspace_id, title, goal, scope, created_at
            FROM research_project
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_paper(
    *,
    workspace_id: str,
    doc_id: str,
    title: str,
    authors: str,
    year: str,
    venue: str | None = None,
    project_id: str | None = None,
) -> str:
    paper_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            "UPDATE documents SET doc_type = 'paper' WHERE id = ?",
            (doc_id,),
        )
        connection.execute(
            """
            INSERT INTO papers (id, workspace_id, project_id, doc_id, title, authors, year, venue, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (paper_id, workspace_id, project_id, doc_id, title, authors, year, venue, _now_iso()),
        )
        connection.commit()
    return paper_id


def list_project_papers(project_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, workspace_id, project_id, doc_id, title, authors, year, venue, created_at
            FROM papers
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_ideas(project_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, project_id, title, claim, novelty_type, status, version, created_at, updated_at
            FROM idea
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_idea_dialogue(idea_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, idea_id, turn_no, role, content, created_at
            FROM idea_dialogue
            WHERE idea_id = ?
            ORDER BY turn_no ASC
            """,
            (idea_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_experiment_plans(project_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, project_id, idea_id, plan_json, created_at
            FROM experiment_plan
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_experiment_runs(project_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, project_id, plan_id, date, result, notes, next_action, created_at
            FROM experiment_run
            WHERE project_id = ?
            ORDER BY date DESC
            """,
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_paper_card(*, paper_id: str, card_md_ref: str) -> str:
    card_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO paper_card (id, paper_id, card_md_ref, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (card_id, paper_id, card_md_ref, _now_iso()),
        )
        connection.commit()
    return card_id


def create_idea(
    *,
    project_id: str,
    title: str,
    claim: str,
    novelty_type: str | None = None,
    status: str = "draft",
    version: int = 1,
) -> str:
    idea_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO idea (id, project_id, title, claim, novelty_type, status, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (idea_id, project_id, title, claim, novelty_type, status, version, _now_iso(), _now_iso()),
        )
        connection.commit()
    return idea_id


def add_idea_dialogue(*, idea_id: str, turn_no: int, role: str, content: str) -> str:
    dialogue_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO idea_dialogue (id, idea_id, turn_no, role, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (dialogue_id, idea_id, turn_no, role, content, _now_iso()),
        )
        connection.commit()
    return dialogue_id


def confirm_idea(*, idea_id: str, version: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE idea
            SET status = 'confirmed', version = ?, updated_at = ?
            WHERE id = ?
            """,
            (version, _now_iso(), idea_id),
        )
        connection.commit()


def create_experiment_plan(*, project_id: str, idea_id: str, plan: dict) -> str:
    plan_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO experiment_plan (id, project_id, idea_id, plan_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (plan_id, project_id, idea_id, json.dumps(plan), _now_iso()),
        )
        connection.commit()
    return plan_id


def create_experiment_run(
    *,
    project_id: str,
    date: str,
    result: str | None,
    notes: str | None,
    next_action: str | None,
    plan_id: str | None = None,
) -> str:
    run_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO experiment_run (id, project_id, plan_id, date, result, notes, next_action, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, project_id, plan_id, date, result, notes, next_action, _now_iso()),
        )
        connection.commit()
    return run_id


def create_deck(
    *,
    workspace_id: str,
    source_kind: str,
    source_ids: list[str],
    duration: int | None,
    deck_md_ref: str,
    notes_ref: str | None,
    qa_ref: str | None,
    coverage_json: dict | None,
) -> str:
    deck_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO deck (id, workspace_id, source_kind, source_ids_json, duration, deck_md_ref,
                              notes_ref, qa_ref, coverage_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                deck_id,
                workspace_id,
                source_kind,
                json.dumps(source_ids),
                duration,
                deck_md_ref,
                notes_ref,
                qa_ref,
                json.dumps(coverage_json) if coverage_json else None,
                _now_iso(),
            ),
        )
        connection.commit()
    return deck_id

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import streamlit as st  # noqa: F401

from app.ui import components as ui_components
from core.domains.course import (
    add_assignment_asset,
    add_lecture_material,
    create_assignment,
    create_course,
    create_lecture,
)
from core.domains.research import add_paper, create_project
from core.index_assets.store import get_doc_index_assets
from core.storage.migrations import run_migrations
from core.version import VERSION
from infra.db import get_workspaces_dir
from service.course_v3_service import generate_exam_blueprint
from service.ingest_service import ingest_document
from service.recent_activity_service import add_activity, list_recent_activity
from service.research_v3_service import (
    add_experiment_run,
    confirm_idea_version,
    create_idea_from_prompt,
    generate_deck,
    generate_experiment_plan_from_idea,
    generate_paper_card,
)
from service.tasks_service import enqueue_index_assets_task, run_task_by_id
from service.workspace_service import create_workspace


def _run_cmd(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stdout}\n{result.stderr}")


def _prepare_sample_file(workspace_id: str, name: str, content: str) -> Path:
    target = get_workspaces_dir() / workspace_id / "uploads" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def main() -> None:
    print(f"StudyFlow v{VERSION} verify (v3)")

    _run_cmd([sys.executable, "-m", "compileall", "."])
    _run_cmd([sys.executable, "-m", "pytest", "-q"])
    __import__("app.main")

    run_migrations()
    workspace_id = create_workspace("v3-verify")

    course_id = create_course(workspace_id=workspace_id, name="CS101", code="CS101")
    lecture_id = create_lecture(course_id=course_id, lecture_no=1, topic="Intro")
    assignment_id = create_assignment(course_id=course_id, title="HW1", due_at=None, status="todo")

    doc_a = _prepare_sample_file(workspace_id, "lecture1.txt", "Lecture 1: Intro to AI.\nKey concepts...")
    doc_b = _prepare_sample_file(workspace_id, "assignment1.txt", "Assignment 1 spec.\nRequirements...")

    ingest_a = ingest_document(
        workspace_id=workspace_id,
        filename=doc_a.name,
        data=doc_a.read_bytes(),
        save_dir=doc_a.parent,
        write_file=True,
        existing_path=doc_a,
        ocr_mode="off",
        ocr_threshold=50,
        doc_type="course",
    )
    ingest_b = ingest_document(
        workspace_id=workspace_id,
        filename=doc_b.name,
        data=doc_b.read_bytes(),
        save_dir=doc_b.parent,
        write_file=True,
        existing_path=doc_b,
        ocr_mode="off",
        ocr_threshold=50,
        doc_type="course",
    )
    add_lecture_material(lecture_id=lecture_id, doc_id=ingest_a.doc_id, role="notes")
    add_assignment_asset(assignment_id=assignment_id, doc_id=ingest_b.doc_id, role="spec")

    task_id = enqueue_index_assets_task(workspace_id=workspace_id, doc_id=ingest_a.doc_id)
    run_task_by_id(task_id)
    assert get_doc_index_assets(ingest_a.doc_id), "doc_index_assets missing"

    exam = generate_exam_blueprint(workspace_id=workspace_id, course_id=course_id)
    assert exam.get("coverage"), "coverage_json missing"

    project_id = create_project(workspace_id=workspace_id, title="Project A", goal="Test", scope="Scope")
    paper_id = add_paper(
        workspace_id=workspace_id,
        project_id=project_id,
        doc_id=ingest_a.doc_id,
        title="Paper A",
        authors="Anon",
        year="2025",
        venue="Conf",
    )
    generate_paper_card(workspace_id=workspace_id, paper_id=paper_id, doc_id=ingest_a.doc_id)

    idea = create_idea_from_prompt(project_id=project_id, prompt="Novel approach to X")
    confirm_idea_version(idea_id=idea["idea_id"], version=1)
    plan = generate_experiment_plan_from_idea(
        project_id=project_id, idea_id=idea["idea_id"], idea_claim=idea["claim"]
    )
    add_experiment_run(
        project_id=project_id,
        plan_id=plan["plan_id"],
        date="2026-02-05",
        result="ok",
        notes="notes",
        next_action="next",
    )

    coverage = exam.get("coverage")
    generate_deck(
        workspace_id=workspace_id,
        source_kind="course",
        source_ids=[course_id],
        duration=10,
        coverage=coverage,
    )

    for i in range(35):
        add_activity(
            workspace_id=workspace_id,
            type="verify",
            title=f"activity {i}",
            status="succeeded",
            output_ref=json.dumps({"index": i}),
        )
    activity = list_recent_activity(workspace_id)
    assert len(activity) <= 30, "recent_activity FIFO exceeded"

    os.environ["STREAMLIT_TEST_MODE"] = "1"
    st.session_state["workspace_id"] = workspace_id
    st.session_state["task_status_cache_initialized"] = True
    ui_components._collect_task_notifications(workspace_id)  # noqa: SLF001

    print("v3 verify complete")

    # Cleanup test workspace
    _cleanup_test_workspace(workspace_id)


def _cleanup_test_workspace(workspace_id: str) -> None:
    """Clean up the test workspace created during verification."""
    from service.workspace_service import delete_workspace_except

    print("\nCleaning up test workspace...")
    deleted = delete_workspace_except(keep_names=["test1"])
    print(f"Cleaned up {deleted} test workspace(s), keeping 'test1'")


if __name__ == "__main__":
    main()

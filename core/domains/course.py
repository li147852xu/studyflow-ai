from __future__ import annotations

import uuid
from datetime import datetime, timezone

from infra.db import get_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_course(
    *,
    workspace_id: str,
    name: str,
    code: str | None = None,
    instructor: str | None = None,
    semester: str | None = None,
) -> str:
    course_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO courses (id, workspace_id, name, code, instructor, semester, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (course_id, workspace_id, name, code, instructor, semester, _now_iso()),
        )
        connection.commit()
    return course_id


def update_course(
    *,
    course_id: str,
    name: str,
    code: str | None,
    instructor: str | None,
    semester: str | None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE courses
            SET name = ?, code = ?, instructor = ?, semester = ?
            WHERE id = ?
            """,
            (name, code, instructor, semester, course_id),
        )
        connection.commit()


def delete_course(course_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        connection.commit()


def get_course(course_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, workspace_id, name, code, instructor, semester, created_at
            FROM courses
            WHERE id = ?
            """,
            (course_id,),
        ).fetchone()
    return dict(row) if row else None


def list_courses(workspace_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, workspace_id, name, code, instructor, semester, created_at
            FROM courses
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_schedule(
    *,
    course_id: str,
    weekday: str,
    start_time: str,
    end_time: str,
    location: str | None = None,
) -> str:
    schedule_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO course_schedule (id, course_id, weekday, start_time, end_time, location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (schedule_id, course_id, weekday, start_time, end_time, location, _now_iso()),
        )
        connection.commit()
    return schedule_id


def list_schedules(course_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, course_id, weekday, start_time, end_time, location, created_at
            FROM course_schedule
            WHERE course_id = ?
            ORDER BY weekday, start_time
            """,
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_lecture(
    *,
    course_id: str,
    lecture_no: int | None = None,
    date: str | None = None,
    topic: str | None = None,
) -> str:
    lecture_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO lecture (id, course_id, lecture_no, date, topic, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (lecture_id, course_id, lecture_no, date, topic, _now_iso()),
        )
        connection.commit()
    return lecture_id


def list_course_lectures(course_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, course_id, lecture_no, date, topic, created_at
            FROM lecture
            WHERE course_id = ?
            ORDER BY lecture_no, date
            """,
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_lecture_material(
    *,
    lecture_id: str,
    doc_id: str,
    role: str,
) -> str:
    material_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            "UPDATE documents SET doc_type = 'course' WHERE id = ?",
            (doc_id,),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO lecture_material (id, lecture_id, doc_id, role, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (material_id, lecture_id, doc_id, role, _now_iso()),
        )
        connection.commit()
    return material_id


def list_lecture_materials(lecture_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT lecture_material.id, lecture_material.lecture_id, lecture_material.doc_id, lecture_material.role,
                   documents.filename, documents.file_type, documents.size_bytes
            FROM lecture_material
            JOIN documents ON documents.id = lecture_material.doc_id
            WHERE lecture_material.lecture_id = ?
            ORDER BY lecture_material.created_at DESC
            """,
            (lecture_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_assignment(
    *,
    course_id: str,
    title: str,
    due_at: str | None = None,
    status: str = "todo",
) -> str:
    assignment_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO assignment (id, course_id, title, due_at, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (assignment_id, course_id, title, due_at, status, _now_iso()),
        )
        connection.commit()
    return assignment_id


def list_assignments(course_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, course_id, title, due_at, status, created_at
            FROM assignment
            WHERE course_id = ?
            ORDER BY created_at DESC
            """,
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_assignment_asset(
    *,
    assignment_id: str,
    doc_id: str,
    role: str,
) -> str:
    asset_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            "UPDATE documents SET doc_type = 'course' WHERE id = ?",
            (doc_id,),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO assignment_asset (id, assignment_id, doc_id, role, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (asset_id, assignment_id, doc_id, role, _now_iso()),
        )
        connection.commit()
    return asset_id


def link_course_document(*, course_id: str, doc_id: str) -> str:
    link_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            "UPDATE documents SET doc_type = 'course' WHERE id = ?",
            (doc_id,),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO course_documents (id, course_id, doc_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (link_id, course_id, doc_id, _now_iso()),
        )
        connection.commit()
    return link_id


def list_course_documents(course_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT documents.id, documents.filename, documents.file_type, documents.size_bytes,
                   course_documents.created_at
            FROM course_documents
            JOIN documents ON documents.id = course_documents.doc_id
            WHERE course_documents.course_id = ?
            ORDER BY course_documents.created_at DESC
            """,
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_exam_asset(
    *,
    course_id: str,
    blueprint_ref: str | None,
    cheatsheet_ref: str | None,
    coverage_json: str | None,
) -> None:
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM exam_asset WHERE course_id = ?",
            (course_id,),
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE exam_asset
                SET blueprint_ref = ?, cheatsheet_ref = ?, coverage_json = ?, updated_at = ?
                WHERE course_id = ?
                """,
                (blueprint_ref, cheatsheet_ref, coverage_json, _now_iso(), course_id),
            )
        else:
            connection.execute(
                """
                INSERT INTO exam_asset (id, course_id, blueprint_ref, cheatsheet_ref, coverage_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    course_id,
                    blueprint_ref,
                    cheatsheet_ref,
                    coverage_json,
                    _now_iso(),
                ),
            )
        connection.commit()

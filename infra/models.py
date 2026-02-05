from infra.db import get_connection


def _ensure_column(table: str, column: str, column_def: str) -> None:
    with get_connection() as connection:
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {row[1] for row in rows}
        if column not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")
            connection.commit()


def init_db() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                sha256 TEXT,
                page_count INTEGER,
                ocr_mode TEXT,
                ocr_pages_count INTEGER,
                image_pages_count INTEGER,
                file_type TEXT,
                size_bytes INTEGER,
                file_name TEXT,
                file_ext TEXT,
                file_size INTEGER,
                imported_at TEXT,
                source TEXT,
                source_type TEXT,
                source_ref TEXT,
                doc_type TEXT NOT NULL DEFAULT 'other',
                updated_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_tags (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(doc_id) REFERENCES documents(id),
                UNIQUE(doc_id, tag)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ui_settings (
                id TEXT PRIMARY KEY,
                workspace_id TEXT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(workspace_id, key)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ui_history (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                summary TEXT,
                preview TEXT,
                source_ref TEXT,
                run_id TEXT,
                citations_count INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recent_activity (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT,
                status TEXT,
                output_ref TEXT,
                citations_summary TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                progress REAL,
                error TEXT,
                payload_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                name TEXT NOT NULL,
                code TEXT,
                instructor TEXT,
                semester TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS course_schedule (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                weekday TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                location TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(course_id) REFERENCES courses(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lecture (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                lecture_no INTEGER,
                date TEXT,
                topic TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(course_id) REFERENCES courses(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lecture_material (
                id TEXT PRIMARY KEY,
                lecture_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(lecture_id) REFERENCES lecture(id),
                FOREIGN KEY(doc_id) REFERENCES documents(id),
                UNIQUE(lecture_id, doc_id, role)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assignment (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                title TEXT NOT NULL,
                due_at TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(course_id) REFERENCES courses(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assignment_asset (
                id TEXT PRIMARY KEY,
                assignment_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(assignment_id) REFERENCES assignment(id),
                FOREIGN KEY(doc_id) REFERENCES documents(id),
                UNIQUE(assignment_id, doc_id, role)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS exam_asset (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                blueprint_ref TEXT,
                cheatsheet_ref TEXT,
                coverage_json TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(course_id) REFERENCES courses(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS course_documents (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(course_id) REFERENCES courses(id),
                FOREIGN KEY(doc_id) REFERENCES documents(id),
                UNIQUE(course_id, doc_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS timetable_event (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                title TEXT NOT NULL,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                location TEXT,
                linked_course_id TEXT,
                linked_todo_id TEXT,
                kind TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS todo_item (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                due_at TEXT,
                linked_course_id TEXT,
                linked_project_id TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_project (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                title TEXT NOT NULL,
                goal TEXT,
                scope TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                project_id TEXT,
                doc_id TEXT NOT NULL,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                year TEXT NOT NULL,
                venue TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id),
                FOREIGN KEY(doc_id) REFERENCES documents(id),
                UNIQUE(workspace_id, doc_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS paper_card (
                id TEXT PRIMARY KEY,
                paper_id TEXT NOT NULL,
                card_md_ref TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(paper_id) REFERENCES papers(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS idea (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                claim TEXT NOT NULL,
                novelty_type TEXT,
                status TEXT NOT NULL,
                version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES research_project(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS idea_dialogue (
                id TEXT PRIMARY KEY,
                idea_id TEXT NOT NULL,
                turn_no INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(idea_id) REFERENCES idea(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS experiment_plan (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                idea_id TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES research_project(id),
                FOREIGN KEY(idea_id) REFERENCES idea(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS experiment_run (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                plan_id TEXT,
                date TEXT NOT NULL,
                result TEXT,
                notes TEXT,
                next_action TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES research_project(id),
                FOREIGN KEY(plan_id) REFERENCES experiment_plan(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS deck (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                source_ids_json TEXT NOT NULL,
                duration INTEGER,
                deck_md_ref TEXT NOT NULL,
                notes_ref TEXT,
                qa_ref TEXT,
                coverage_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS doc_index_assets (
                doc_id TEXT PRIMARY KEY,
                summary_text TEXT,
                outline_json TEXT,
                entities_json TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(doc_id) REFERENCES documents(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS paper_tags (
                id TEXT PRIMARY KEY,
                paper_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(paper_id) REFERENCES papers(id),
                UNIQUE(paper_id, tag)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                page_start INTEGER NOT NULL,
                page_end INTEGER NOT NULL,
                text TEXT NOT NULL,
                text_source TEXT,
                metadata_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(doc_id) REFERENCES documents(id),
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_pages (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                text_source TEXT,
                ocr_text TEXT,
                image_count INTEGER,
                has_images INTEGER,
                blocks_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(doc_id) REFERENCES documents(id),
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id),
                UNIQUE(doc_id, page_number)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                ref_id TEXT NOT NULL,
                active_version_id TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id),
                UNIQUE(workspace_id, kind, ref_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS asset_versions (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                version_index INTEGER NOT NULL,
                run_id TEXT,
                model TEXT,
                provider TEXT,
                temperature REAL,
                max_tokens INTEGER,
                retrieval_mode TEXT,
                embed_model TEXT,
                seed INTEGER,
                prompt_version TEXT,
                content_path TEXT NOT NULL,
                content_type TEXT NOT NULL,
                citations_json TEXT,
                hits_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(asset_id) REFERENCES assets(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS coach_sessions (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                problem TEXT NOT NULL,
                phase_a_output TEXT,
                phase_b_output TEXT,
                citations_json TEXT,
                hits_json TEXT,
                status TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS external_sources (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                params_json TEXT,
                last_sync_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS external_mappings (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                external_id TEXT NOT NULL,
                external_sub_id TEXT,
                doc_id TEXT,
                status TEXT,
                meta_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(source_id) REFERENCES external_sources(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS concept_cards (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS concept_evidence (
                id TEXT PRIMARY KEY,
                card_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                chunk_id TEXT NOT NULL,
                page_start INTEGER,
                page_end INTEGER,
                snippet TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(card_id) REFERENCES concept_cards(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_processing_marks (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                processor TEXT NOT NULL,
                doc_hash TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(workspace_id, doc_id, processor)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS related_projects (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                comparison_axes_json TEXT,
                current_draft TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS related_sections (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                section_index INTEGER NOT NULL,
                title TEXT NOT NULL,
                bullets_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES related_projects(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS related_candidates (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                section_id TEXT NOT NULL,
                paper_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES related_projects(id),
                FOREIGN KEY(section_id) REFERENCES related_sections(id)
            )
            """
        )
        connection.commit()

    _ensure_column("documents", "sha256", "TEXT")
    _ensure_column("documents", "page_count", "INTEGER")
    _ensure_column("documents", "updated_at", "TEXT")
    _ensure_column("documents", "ocr_mode", "TEXT")
    _ensure_column("documents", "ocr_pages_count", "INTEGER")
    _ensure_column("documents", "image_pages_count", "INTEGER")
    _ensure_column("documents", "file_type", "TEXT")
    _ensure_column("documents", "size_bytes", "INTEGER")
    _ensure_column("documents", "file_name", "TEXT")
    _ensure_column("documents", "file_ext", "TEXT")
    _ensure_column("documents", "file_size", "INTEGER")
    _ensure_column("documents", "imported_at", "TEXT")
    _ensure_column("documents", "source", "TEXT")
    _ensure_column("documents", "source_type", "TEXT")
    _ensure_column("documents", "source_ref", "TEXT")
    _ensure_column("documents", "doc_type", "TEXT NOT NULL DEFAULT 'other'")
    _ensure_column("tasks", "started_at", "TEXT")
    _ensure_column("tasks", "finished_at", "TEXT")
    _ensure_column("courses", "code", "TEXT")
    _ensure_column("courses", "instructor", "TEXT")
    _ensure_column("courses", "semester", "TEXT")
    _ensure_column("papers", "project_id", "TEXT")
    _ensure_column("papers", "venue", "TEXT")
    _ensure_column("ui_history", "run_id", "TEXT")
    _ensure_column("assets", "active_version_id", "TEXT")
    _ensure_column("chunks", "text_source", "TEXT")
    _ensure_column("chunks", "metadata_json", "TEXT")
    _ensure_column("asset_versions", "provider", "TEXT")
    _ensure_column("asset_versions", "temperature", "REAL")
    _ensure_column("asset_versions", "max_tokens", "INTEGER")
    _ensure_column("asset_versions", "retrieval_mode", "TEXT")
    _ensure_column("asset_versions", "embed_model", "TEXT")
    _ensure_column("asset_versions", "seed", "INTEGER")
    _ensure_column("documents", "summary", "TEXT")
    _ensure_column("coach_sessions", "name", "TEXT")

    with get_connection() as connection:
        connection.execute(
            "UPDATE documents SET doc_type = 'other' WHERE doc_type IS NULL OR doc_type = ''"
        )
        connection.execute(
            """
            UPDATE documents
            SET file_type = 'pdf'
            WHERE (file_type IS NULL OR file_type = '')
              AND lower(filename) LIKE '%.pdf'
            """
        )
        connection.execute(
            """
            UPDATE documents
            SET source = 'upload'
            WHERE source IS NULL OR source = ''
            """
        )
        connection.commit()

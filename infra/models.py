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
                source_type TEXT,
                source_ref TEXT,
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
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
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
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                year TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id),
                FOREIGN KEY(doc_id) REFERENCES documents(id),
                UNIQUE(workspace_id, doc_id)
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
        connection.commit()

    _ensure_column("documents", "sha256", "TEXT")
    _ensure_column("documents", "page_count", "INTEGER")
    _ensure_column("documents", "updated_at", "TEXT")
    _ensure_column("documents", "ocr_mode", "TEXT")
    _ensure_column("documents", "ocr_pages_count", "INTEGER")
    _ensure_column("documents", "image_pages_count", "INTEGER")
    _ensure_column("documents", "source_type", "TEXT")
    _ensure_column("documents", "source_ref", "TEXT")
    _ensure_column("ui_history", "run_id", "TEXT")
    _ensure_column("assets", "active_version_id", "TEXT")
    _ensure_column("chunks", "text_source", "TEXT")
    _ensure_column("chunks", "metadata_json", "TEXT")

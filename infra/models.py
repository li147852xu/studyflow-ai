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
                created_at TEXT NOT NULL,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
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
                created_at TEXT NOT NULL,
                FOREIGN KEY(doc_id) REFERENCES documents(id),
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )
            """
        )
        connection.commit()

    _ensure_column("documents", "sha256", "TEXT")
    _ensure_column("documents", "page_count", "INTEGER")

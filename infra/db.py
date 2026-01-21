import os
import sqlite3
from pathlib import Path

DEFAULT_WORKSPACES_DIR = os.getenv("STUDYFLOW_WORKSPACES_DIR", "./workspaces")
DEFAULT_DB_FILENAME = "studyflow.db"


def get_workspaces_dir() -> Path:
    return Path(DEFAULT_WORKSPACES_DIR)


def get_db_path() -> Path:
    workspaces_dir = get_workspaces_dir()
    workspaces_dir.mkdir(parents=True, exist_ok=True)
    return workspaces_dir / DEFAULT_DB_FILENAME


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection

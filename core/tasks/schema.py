from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaskRecord:
    id: str
    workspace_id: str
    type: str
    status: str
    progress: float | None
    error: str | None
    payload_json: str | None
    created_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None

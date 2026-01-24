from __future__ import annotations

from core.tasks.runner import enqueue_task, run_task, cancel_task, retry_task, resume_task
from core.tasks.store import get_task, list_tasks


def enqueue_ingest_task(
    *,
    workspace_id: str,
    path: str,
    ocr_mode: str,
    ocr_threshold: int,
    save_dir: str | None = None,
    write_file: bool = True,
    existing_path: str | None = None,
) -> str:
    return enqueue_task(
        workspace_id=workspace_id,
        type="ingest",
        payload={
            "workspace_id": workspace_id,
            "path": path,
            "ocr_mode": ocr_mode,
            "ocr_threshold": ocr_threshold,
            "save_dir": save_dir,
            "write_file": write_file,
            "existing_path": existing_path,
        },
    )


def enqueue_index_task(
    *,
    workspace_id: str,
    reset: bool = True,
    doc_ids: list[str] | None = None,
    batch_size: int = 32,
) -> str:
    return enqueue_task(
        workspace_id=workspace_id,
        type="index",
        payload={
            "workspace_id": workspace_id,
            "reset": reset,
            "doc_ids": doc_ids,
            "batch_size": batch_size,
        },
    )


def run_task_by_id(task_id: str) -> dict:
    return run_task(task_id)


def cancel_task_by_id(task_id: str) -> None:
    cancel_task(task_id)


def retry_task_by_id(task_id: str) -> dict:
    return retry_task(task_id)


def resume_task_by_id(task_id: str) -> dict:
    return resume_task(task_id)


def get_task_by_id(task_id: str):
    return get_task(task_id)


def list_tasks_for_workspace(
    *, workspace_id: str | None = None, status: str | None = None
):
    return list_tasks(workspace_id=workspace_id, status=status)

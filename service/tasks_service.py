from __future__ import annotations

from core.tasks.executor import submit_task
from core.tasks.runner import cancel_task, enqueue_task, resume_task, retry_task, run_task
from core.tasks.store import get_task, list_tasks


def enqueue_ingest_task(
    *,
    workspace_id: str,
    path: str,
    ocr_mode: str,
    ocr_threshold: int,
    doc_type: str = "other",
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
            "doc_type": doc_type,
            "save_dir": save_dir,
            "write_file": write_file,
            "existing_path": existing_path,
        },
    )


def enqueue_ingest_index_task(
    *,
    workspace_id: str,
    path: str,
    ocr_mode: str,
    ocr_threshold: int,
    doc_type: str = "other",
    save_dir: str | None = None,
    write_file: bool = True,
    existing_path: str | None = None,
) -> str:
    return enqueue_task(
        workspace_id=workspace_id,
        type="ingest_index",
        payload={
            "workspace_id": workspace_id,
            "path": path,
            "ocr_mode": ocr_mode,
            "ocr_threshold": ocr_threshold,
            "doc_type": doc_type,
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


def enqueue_index_assets_task(*, workspace_id: str, doc_id: str) -> str:
    return enqueue_task(
        workspace_id=workspace_id,
        type="index_assets",
        payload={"workspace_id": workspace_id, "doc_id": doc_id},
    )


def run_task_by_id(task_id: str) -> dict:
    return run_task(task_id)


def run_task_in_background(task_id: str) -> bool:
    return submit_task(task_id)


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


def enqueue_generate_task(
    *,
    workspace_id: str,
    action_type: str,
    payload: dict,
    api_mode: str,
    api_base_url: str,
) -> str:
    task_type = f"generate_{action_type}"
    return enqueue_task(
        workspace_id=workspace_id,
        type=task_type,
        payload={
            "workspace_id": workspace_id,
            "action_type": action_type,
            "payload": payload,
            "api_mode": api_mode,
            "api_base_url": api_base_url,
        },
    )


def enqueue_query_task(
    *,
    workspace_id: str,
    query: str,
    mode: str,
    top_k: int,
    api_mode: str,
    api_base_url: str,
) -> str:
    return enqueue_task(
        workspace_id=workspace_id,
        type="ask",
        payload={
            "workspace_id": workspace_id,
            "query": query,
            "mode": mode,
            "top_k": top_k,
            "api_mode": api_mode,
            "api_base_url": api_base_url,
        },
    )

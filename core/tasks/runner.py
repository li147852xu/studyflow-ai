from __future__ import annotations

import json
from pathlib import Path

from core.tasks.store import (
    create_task,
    get_task,
    update_payload,
    update_progress,
    update_status,
)
from service.ingest_service import ingest_pdf
from service.retrieval_service import build_or_refresh_index
from infra.db import get_workspaces_dir
from core.retrieval.bm25_index import build_bm25_index


class TaskError(RuntimeError):
    pass


class TaskCancelled(RuntimeError):
    pass


def _parse_payload(payload_json: str | None) -> dict:
    if not payload_json:
        return {}
    return json.loads(payload_json)


def _progress_cb(task_id: str):
    def _update(current: int, total: int) -> None:
        if total == 0:
            return
        progress = round((current / total) * 100, 2)
        update_progress(task_id, progress)

    return _update


def _stop_check(task_id: str) -> callable:
    def _check() -> bool:
        task = get_task(task_id)
        if task and task.status == "cancelled":
            raise TaskCancelled("Task cancelled.")
        return False

    return _check


def _run_ingest(task_id: str, payload: dict) -> dict:
    pdf_path = Path(payload["path"])
    if not pdf_path.exists():
        raise TaskError("PDF path does not exist.")
    data = pdf_path.read_bytes()
    save_dir = (
        Path(payload["save_dir"])
        if payload.get("save_dir")
        else get_workspaces_dir() / payload["workspace_id"] / "uploads"
    )
    existing_path = (
        Path(payload["existing_path"]) if payload.get("existing_path") else None
    )
    result = ingest_pdf(
        workspace_id=payload["workspace_id"],
        filename=pdf_path.name,
        data=data,
        save_dir=save_dir,
        write_file=payload.get("write_file", True),
        existing_path=existing_path,
        ocr_mode=payload.get("ocr_mode", "off"),
        ocr_threshold=payload.get("ocr_threshold", 50),
        progress_cb=_progress_cb(task_id),
        stop_check=_stop_check(task_id),
    )
    return {
        "doc_id": result.doc_id,
        "page_count": result.page_count,
        "chunk_count": result.chunk_count,
        "skipped": result.skipped,
    }


def _run_index(task_id: str, payload: dict) -> dict:
    workspace_id = payload["workspace_id"]
    doc_ids = payload.get("doc_ids")
    batch_size = payload.get("batch_size", 32)
    result = build_or_refresh_index(
        workspace_id=workspace_id,
        reset=payload.get("reset", True),
        batch_size=batch_size,
        doc_ids=doc_ids,
        progress_cb=_progress_cb(task_id),
        stop_check=_stop_check(task_id),
    )
    build_bm25_index(workspace_id)
    return {
        "indexed_count": result.indexed_count,
        "chunk_count": result.chunk_count,
        "doc_count": result.doc_count,
    }


_TASK_HANDLERS = {
    "ingest": _run_ingest,
    "index": _run_index,
}


def run_task(task_id: str) -> dict:
    task = get_task(task_id)
    if not task:
        raise TaskError("Task not found.")
    if task.status == "cancelled":
        raise TaskCancelled("Task cancelled.")
    if task.status == "running":
        raise TaskError("Task already running.")
    payload = _parse_payload(task.payload_json)
    update_status(task_id, "running")
    try:
        handler = _TASK_HANDLERS.get(task.type)
        if not handler:
            raise TaskError(f"Unsupported task type: {task.type}")
        result = handler(task_id, payload)
        payload["result"] = result
        update_payload(task_id, payload)
        update_progress(task_id, 100.0)
        update_status(task_id, "succeeded")
        return result
    except TaskCancelled:
        update_status(task_id, "cancelled", "cancelled")
        raise
    except Exception as exc:
        update_status(task_id, "failed", str(exc))
        raise


def enqueue_task(*, workspace_id: str, type: str, payload: dict) -> str:
    return create_task(workspace_id=workspace_id, type=type, payload=payload)


def retry_task(task_id: str) -> dict:
    update_status(task_id, "queued")
    update_progress(task_id, 0)
    return run_task(task_id)


def resume_task(task_id: str) -> dict:
    return retry_task(task_id)


def cancel_task(task_id: str) -> None:
    update_status(task_id, "cancelled")

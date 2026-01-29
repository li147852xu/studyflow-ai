from __future__ import annotations

import json
from pathlib import Path

from core.retrieval.bm25_index import build_bm25_index
from core.tasks.store import (
    create_task,
    get_task,
    update_payload,
    update_progress,
    update_status,
)
from infra.db import get_workspaces_dir
from service.ingest_service import ingest_pdf
from service.retrieval_service import build_or_refresh_index


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
        doc_type=payload.get("doc_type", "other"),
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


def _run_ingest_index(task_id: str, payload: dict) -> dict:
    ingest_result = _run_ingest(task_id, payload)
    update_progress(task_id, 50.0)
    index_result = _run_index(
        task_id,
        {
            "workspace_id": payload["workspace_id"],
            "reset": False,
            "doc_ids": [ingest_result["doc_id"]],
            "batch_size": payload.get("batch_size", 32),
        },
    )
    return {"ingest": ingest_result, "index": index_result}


def _run_generate(task_id: str, payload: dict) -> dict:
    from service.api_mode_adapter import ApiModeAdapter
    from service.asset_service import (
        course_explain_ref_id,
        course_ref_id,
        create_asset_version,
        paper_aggregate_ref_id,
        paper_ref_id,
        slides_ref_id,
    )
    from service.recent_activity_service import add_activity

    adapter = ApiModeAdapter(
        payload.get("api_mode", "direct"),
        payload.get("api_base_url", "http://127.0.0.1:8000"),
    )
    action_type = payload.get("action_type", "")
    action_payload = dict(payload.get("payload", {}))
    title = action_payload.pop("title", None)
    output = adapter.generate(action_type=action_type, payload=action_payload)

    content = getattr(output, "content", None)
    if content is None:
        content = getattr(output, "deck", "")
    content_type = "markdown" if action_type == "slides" else "text"

    asset_id = getattr(output, "asset_id", None)
    asset_version_id = getattr(output, "asset_version_id", None)
    if payload.get("api_mode") != "direct" or not asset_version_id:
        if action_type == "course_overview" or action_type == "course_cheatsheet":
            ref_id = course_ref_id(action_payload.get("course_id", ""))
        elif action_type == "course_explain":
            ref_id = course_explain_ref_id(
                action_payload.get("course_id", ""),
                action_payload.get("selection", ""),
                action_payload.get("mode", "plain"),
            )
        elif action_type == "course_qa":
            ref_id = f"course_qa:{action_payload.get('course_id', '')}:{action_payload.get('question', '')[:50]}"
        elif action_type == "paper_card":
            ref_id = paper_ref_id(action_payload.get("doc_id", ""))
        elif action_type == "paper_aggregate":
            ref_id = paper_aggregate_ref_id(
                action_payload.get("doc_ids", []) or [],
                action_payload.get("question", ""),
            )
        elif action_type == "slides":
            ref_id = slides_ref_id(
                action_payload.get("doc_id", ""),
                action_payload.get("duration", "10"),
            )
        else:
            ref_id = action_type
        version = create_asset_version(
            workspace_id=payload["workspace_id"],
            kind=action_type,
            ref_id=ref_id,
            content=content,
            content_type=content_type,
            run_id=getattr(output, "run_id", None),
            model=None,
            provider=None,
            temperature=None,
            max_tokens=None,
            retrieval_mode=action_payload.get("retrieval_mode"),
            embed_model=None,
            seed=None,
            prompt_version="v1",
            hits=[],
        )
        asset_id = version.asset_id
        asset_version_id = version.id

    add_activity(
        workspace_id=payload["workspace_id"],
        type=f"generate_{action_type}",
        title=title or action_type,
        status="succeeded",
        output_ref=json.dumps(
            {
                "asset_version_id": asset_version_id,
                "asset_id": asset_id,
                "source_id": action_payload.get("course_id")
                or action_payload.get("doc_id")
                or action_payload.get("doc_ids"),
                "kind": action_type,
            },
            ensure_ascii=False,
        ),
        citations_summary=None,
    )

    return {
        "action_type": action_type,
        "asset_id": asset_id,
        "asset_version_id": asset_version_id,
        "run_id": getattr(output, "run_id", None),
    }


def _run_ask(task_id: str, payload: dict) -> dict:
    from core.retrieval.retriever import Hit
    from service.api_mode_adapter import ApiModeAdapter
    from service.asset_service import ask_ref_id, create_asset_version

    adapter = ApiModeAdapter(
        payload.get("api_mode", "direct"),
        payload.get("api_base_url", "http://127.0.0.1:8000"),
    )
    result = adapter.query(
        workspace_id=payload["workspace_id"],
        query=payload["query"],
        mode=payload.get("mode", "vector"),
        top_k=payload.get("top_k", 8),
    )
    hits = [
        Hit(
            chunk_id=item.get("chunk_id", ""),
            doc_id=item.get("doc_id", ""),
            workspace_id=item.get("workspace_id", ""),
            filename=item.get("filename", ""),
            page_start=int(item.get("page_start") or 0),
            page_end=int(item.get("page_end") or 0),
            text=item.get("text", ""),
            score=float(item.get("score") or 0),
        )
        for item in result.hits
    ]
    version = create_asset_version(
        workspace_id=payload["workspace_id"],
        kind="ask",
        ref_id=ask_ref_id(payload.get("query", ""), result.run_id),
        content=result.answer,
        content_type="text",
        run_id=result.run_id,
        model=None,
        provider=None,
        temperature=None,
        max_tokens=None,
        retrieval_mode=payload.get("mode", "vector"),
        embed_model=None,
        seed=None,
        prompt_version="v1",
        hits=hits,
    )
    return {
        "asset_id": version.asset_id,
        "asset_version_id": version.id,
        "run_id": result.run_id,
    }


_TASK_HANDLERS = {
    "ingest": _run_ingest,
    "ingest_index": _run_ingest_index,
    "index": _run_index,
    "ask": _run_ask,
    "generate_course_overview": _run_generate,
    "generate_course_cheatsheet": _run_generate,
    "generate_course_explain": _run_generate,
    "generate_course_qa": _run_generate,
    "generate_paper_card": _run_generate,
    "generate_paper_aggregate": _run_generate,
    "generate_slides": _run_generate,
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

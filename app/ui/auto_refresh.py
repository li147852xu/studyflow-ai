from __future__ import annotations

import time

import streamlit as st

from service.tasks_service import list_tasks_for_workspace


def _task_signature(tasks: list[dict]) -> str:
    entries = []
    for task in tasks:
        if isinstance(task, dict):
            task_id = task.get("id")
            status = task.get("status")
            progress = task.get("progress")
        else:
            task_id = getattr(task, "id", None)
            status = getattr(task, "status", None)
            progress = getattr(task, "progress", None)
        entries.append(f"{task_id}:{status}:{progress}")
    return "|".join(entries)


def maybe_auto_refresh(*, workspace_id: str | None, interval_seconds: float = 2.5) -> None:
    if not workspace_id:
        return

    try:
        tasks = list_tasks_for_workspace(workspace_id=workspace_id)
    except Exception:
        return

    running = [
        task
        for task in tasks
        if (task["status"] if isinstance(task, dict) else task.status)
        in {"queued", "running"}
    ]
    signature = _task_signature(running)
    last_signature = st.session_state.get("last_seen_task_state", "")
    now = time.time()

    if signature and signature != last_signature:
        st.session_state["last_seen_task_state"] = signature
        st.session_state["auto_refresh_last"] = now
        st.rerun()

    if signature:
        last_refresh = float(st.session_state.get("auto_refresh_last", 0.0))
        if now - last_refresh >= interval_seconds:
            st.session_state["auto_refresh_last"] = now
            st.rerun()

from __future__ import annotations

import time

import streamlit as st
from streamlit_autorefresh import st_autorefresh

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


def _has_running_tasks(workspace_id: str) -> bool:
    try:
        tasks = list_tasks_for_workspace(workspace_id=workspace_id)
        return any(
            (task["status"] if isinstance(task, dict) else task.status) in {"queued", "running"}
            for task in tasks
        )
    except Exception:
        return False


def inject_auto_refresh(*, workspace_id: str | None, interval_ms: int = 3000) -> None:
    """Enable auto-refresh when tasks are running using streamlit-autorefresh."""
    if not workspace_id:
        return
    if not _has_running_tasks(workspace_id):
        st.session_state["auto_refresh_active"] = False
        return
    st.session_state["auto_refresh_active"] = True
    # This will auto-refresh the page every interval_ms while tasks are running
    st_autorefresh(interval=interval_ms, limit=None, key="auto_refresh_counter")


def maybe_auto_refresh(*, workspace_id: str | None, interval_seconds: float = 2.0) -> None:
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
    prev_running_count = int(st.session_state.get("running_task_count", 0))
    running_count = len(running)
    signature = _task_signature(running)
    last_signature = st.session_state.get("last_seen_task_state", "")
    now = time.time()

    if running_count > 0:
        st.session_state["completion_refresh_done"] = False
        st.session_state["has_active_tasks"] = True

    if signature and signature != last_signature:
        st.session_state["last_seen_task_state"] = signature
        st.session_state["auto_refresh_last"] = now
        st.session_state["running_task_count"] = running_count
        st.rerun()

    if running_count > 0:
        last_refresh = float(st.session_state.get("auto_refresh_last", 0.0))
        if now - last_refresh >= interval_seconds:
            st.session_state["auto_refresh_last"] = now
            st.session_state["running_task_count"] = running_count
            st.rerun()

    if (
        prev_running_count > 0
        and running_count == 0
        and not st.session_state.get("completion_refresh_done", False)
    ):
        st.session_state["completion_refresh_done"] = True
        st.session_state["running_task_count"] = running_count
        st.session_state["has_active_tasks"] = False
        st.session_state["last_completed_task_time"] = now
        st.rerun()

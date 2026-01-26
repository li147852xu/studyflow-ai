from __future__ import annotations

import streamlit as st

from service.tasks_service import (
    cancel_task_by_id,
    list_tasks_for_workspace,
    resume_task_by_id,
    retry_task_by_id,
    run_task_in_background,
)


def render_tasks_center(*, workspace_id: str | None) -> None:
    st.markdown("### Tasks Center")
    if not workspace_id:
        st.info("Select a project to view tasks.")
        return

    status_filter = st.selectbox(
        "Status filter",
        options=["all", "queued", "running", "succeeded", "failed", "cancelled"],
        index=0,
    )
    status = None if status_filter == "all" else status_filter
    tasks = list_tasks_for_workspace(workspace_id=workspace_id, status=status)
    if not tasks:
        st.caption("No tasks yet. Ingest or index to create tasks.")
        return

    for task in tasks:
        task_id = task["id"] if isinstance(task, dict) else task.id
        task_type = task["type"] if isinstance(task, dict) else task.type
        task_status = task["status"] if isinstance(task, dict) else task.status
        task_updated = task["updated_at"] if isinstance(task, dict) else task.updated_at
        task_progress = task.get("progress") if isinstance(task, dict) else task.progress
        task_error = task.get("error") if isinstance(task, dict) else task.error
        with st.container():
            st.markdown(f"**{task_type}** — `{task_id}`")
            st.caption(f"Status: {task_status} • Updated: {task_updated}")
            if task_progress is not None:
                try:
                    progress_value = float(task_progress)
                except (TypeError, ValueError):
                    progress_value = None
                if progress_value is not None:
                    if progress_value > 1:
                        progress_value = progress_value / 100
                    progress_value = max(0.0, min(1.0, progress_value))
                    st.progress(progress_value)
            if task_error:
                st.error(task_error)
            cols = st.columns(4)
            with cols[0]:
                if st.button("Run", key=f"task_run_{task_id}"):
                    run_task_in_background(task_id)
                    st.success("Task scheduled.")
            with cols[1]:
                if st.button("Cancel", key=f"task_cancel_{task_id}"):
                    cancel_task_by_id(task_id)
                    st.success("Task cancelled.")
            with cols[2]:
                if st.button("Retry", key=f"task_retry_{task_id}"):
                    result = retry_task_by_id(task_id)
                    st.success("Task retried.")
            with cols[3]:
                if st.button("Resume", key=f"task_resume_{task_id}"):
                    result = resume_task_by_id(task_id)
                    st.success("Task resumed.")

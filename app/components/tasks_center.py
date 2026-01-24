from __future__ import annotations

import streamlit as st

from service.tasks_service import (
    cancel_task_by_id,
    list_tasks_for_workspace,
    resume_task_by_id,
    retry_task_by_id,
    run_task_by_id,
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
        with st.container():
            st.markdown(f"**{task['type']}** — `{task['id']}`")
            st.caption(f"Status: {task['status']} • Updated: {task['updated_at']}")
            if task.get("progress") is not None:
                st.progress(float(task["progress"]))
            if task.get("error"):
                st.error(task["error"])
            cols = st.columns(4)
            with cols[0]:
                if st.button("Run", key=f"task_run_{task['id']}"):
                    run_task_by_id(task["id"])
                    st.success("Task executed.")
            with cols[1]:
                if st.button("Cancel", key=f"task_cancel_{task['id']}"):
                    cancel_task_by_id(task["id"])
                    st.success("Task cancelled.")
            with cols[2]:
                if st.button("Retry", key=f"task_retry_{task['id']}"):
                    retry_task_by_id(task["id"])
                    st.success("Task retried.")
            with cols[3]:
                if st.button("Resume", key=f"task_resume_{task['id']}"):
                    resume_task_by_id(task["id"])
                    st.success("Task resumed.")

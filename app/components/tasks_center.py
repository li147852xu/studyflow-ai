from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.ui.i18n import t
from service.tasks_service import (
    cancel_task_by_id,
    list_tasks_for_workspace,
    resume_task_by_id,
    retry_task_by_id,
    run_task_in_background,
)


def _format_time(iso_time: str | None) -> str:
    if not iso_time:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return iso_time[:19] if iso_time else "-"


def render_tasks_center(*, workspace_id: str | None) -> None:
    st.markdown(f"### {t('tasks_center_title', workspace_id)}")
    if not workspace_id:
        st.info(t("tasks_select_project", workspace_id))
        return

    status_filter = st.selectbox(
        t("tasks_status_filter", workspace_id),
        options=["all", "queued", "running", "succeeded", "failed", "cancelled"],
        index=0,
        format_func=lambda value: t(f"task_status_{value}", workspace_id)
        if value != "all"
        else t("all_status", workspace_id),
    )
    status = None if status_filter == "all" else status_filter
    tasks = list_tasks_for_workspace(workspace_id=workspace_id, status=status)
    if not tasks:
        st.caption(t("tasks_empty", workspace_id))
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
            st.caption(
                t("tasks_status_line", workspace_id).format(
                    status=t(f"task_status_{task_status}", workspace_id),
                    updated=_format_time(task_updated),
                )
            )
            # Show progress bar based on status
            if task_status == "succeeded":
                st.progress(1.0)  # Full progress for completed tasks
            elif task_status == "running" or task_status == "queued":
                # Show actual progress for running/queued tasks
                if task_progress is not None:
                    try:
                        progress_value = float(task_progress)
                        if progress_value > 1:
                            progress_value = progress_value / 100
                        progress_value = max(0.0, min(1.0, progress_value))
                        st.progress(progress_value)
                    except (TypeError, ValueError):
                        st.progress(0.0)
                else:
                    st.progress(0.0)
            # For failed/cancelled, don't show progress bar (error message is shown instead)
            if task_error:
                st.error(task_error)
            cols = st.columns(4)
            with cols[0]:
                if st.button(t("task_action_run", workspace_id), key=f"task_run_{task_id}"):
                    try:
                        run_task_in_background(task_id)
                        st.success(t("task_scheduled", workspace_id))
                    except Exception as exc:
                        st.error(str(exc))
            with cols[1]:
                if st.button(t("task_action_cancel", workspace_id), key=f"task_cancel_{task_id}"):
                    try:
                        cancel_task_by_id(task_id)
                        st.success(t("task_cancelled_msg", workspace_id))
                    except Exception as exc:
                        st.error(str(exc))
            with cols[2]:
                if st.button(t("task_action_retry", workspace_id), key=f"task_retry_{task_id}"):
                    try:
                        retry_task_by_id(task_id)
                        st.success(t("task_retried", workspace_id))
                    except Exception as exc:
                        st.error(str(exc))
            with cols[3]:
                if st.button(t("task_action_resume", workspace_id), key=f"task_resume_{task_id}"):
                    try:
                        resume_task_by_id(task_id)
                        st.success(t("task_resumed", workspace_id))
                    except Exception as exc:
                        st.error(str(exc))

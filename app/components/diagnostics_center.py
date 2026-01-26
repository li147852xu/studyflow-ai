from __future__ import annotations

import io
from contextlib import redirect_stdout

import streamlit as st

from cli.commands.clean_cmd import _targets
from cli.commands.doctor import doctor
from infra.db import get_workspaces_dir
from service.retrieval_service import index_status, vacuum_index
from service.tasks_service import enqueue_index_task, run_task_in_background
from app.ui.locks import running_task_summary


def render_diagnostics_center(*, workspace_id: str | None) -> None:
    st.markdown("### Diagnostics")
    st.caption("Health checks, index maintenance, and storage hygiene.")

    if st.button("Run doctor (deep)"):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            doctor(deep=True, workspace=workspace_id)
        output = buffer.getvalue()
        st.code(output or "Doctor completed with no output.")

    if not workspace_id:
        st.info("Select a project to run workspace diagnostics.")
        return
    locked, lock_msg = running_task_summary(workspace_id)
    if lock_msg:
        st.info(lock_msg)

    st.markdown("#### Index status")
    try:
        status = index_status(workspace_id)
        st.json(status)
    except Exception as exc:
        st.error(f"Index status failed: {exc}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Rebuild index", disabled=locked, help=lock_msg or None):
            task_id = enqueue_index_task(workspace_id=workspace_id, reset=True)
            run_task_in_background(task_id)
            st.success("Index rebuild queued.")
    with col2:
        if st.button("Vacuum index", disabled=locked, help=lock_msg or None):
            result = vacuum_index(workspace_id)
            st.success(f"Vacuum complete: {result}")

    st.markdown("#### Storage cleanup")
    st.caption("Default is dry-run. Use apply with confirmation to delete files.")
    use_cache = st.checkbox("Cache", value=True)
    use_outputs = st.checkbox("Outputs", value=True)
    use_exports = st.checkbox("Exports", value=True)
    dry_run = st.checkbox("Dry-run", value=True)
    confirm_apply = st.checkbox("Confirm delete", value=False)
    targets = _targets(
        workspace_id,
        [key for key, enabled in {
            "cache": use_cache,
            "outputs": use_outputs,
            "exports": use_exports,
        }.items() if enabled],
    )
    st.caption("Targets:")
    for path in targets:
        st.code(str(path))

    if st.button("Run cleanup", disabled=locked, help=lock_msg or None):
        if dry_run or not confirm_apply:
            st.info("Dry-run only. Toggle off dry-run and confirm delete to apply.")
            return
        for path in targets:
            if path.exists():
                import shutil

                shutil.rmtree(path, ignore_errors=True)
        st.success("Cleanup complete.")

    st.markdown("#### Workspace layout")
    base = get_workspaces_dir() / workspace_id
    st.write(
        {
            "uploads": str(base / "uploads"),
            "index": str(base / "index"),
            "outputs": str(base / "outputs"),
            "exports": str(base / "exports"),
            "runs": str(base / "runs"),
            "cache": str(base / "cache"),
        }
    )

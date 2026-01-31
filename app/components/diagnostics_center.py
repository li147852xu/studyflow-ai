from __future__ import annotations

import io
from contextlib import redirect_stdout

import streamlit as st

from app.ui.i18n import t
from app.ui.locks import running_task_summary
from cli.commands.clean_cmd import _targets
from cli.commands.doctor import doctor
from infra.db import get_workspaces_dir
from service.retrieval_service import index_status, vacuum_index
from service.tasks_service import enqueue_index_task, run_task_in_background


def render_diagnostics_center(*, workspace_id: str | None) -> None:
    st.markdown(f"### {t('diagnostics_title', workspace_id)}")
    st.caption(t("diagnostics_caption", workspace_id))

    if st.button(t("run_doctor_deep", workspace_id)):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            doctor(deep=True, workspace=workspace_id)
        output = buffer.getvalue()
        st.code(output or t("doctor_no_output", workspace_id))

    if not workspace_id:
        st.info(t("diagnostics_select_project", workspace_id))
        return
    locked, lock_msg = running_task_summary(workspace_id)
    if lock_msg:
        st.info(lock_msg)

    st.markdown(f"#### {t('index_status_title', workspace_id)}")
    try:
        status = index_status(workspace_id)
        st.json(status)
    except Exception as exc:
        st.error(t("index_status_failed", workspace_id).format(error=exc))

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("rebuild_index", workspace_id), disabled=locked, help=lock_msg or None):
            task_id = enqueue_index_task(workspace_id=workspace_id, reset=True)
            run_task_in_background(task_id)
            st.success(t("rebuild_index_queued", workspace_id))
    with col2:
        if st.button(t("vacuum_index", workspace_id), disabled=locked, help=lock_msg or None):
            result = vacuum_index(workspace_id)
            st.success(t("vacuum_complete", workspace_id).format(result=result))

    st.markdown(f"#### {t('storage_cleanup_title', workspace_id)}")
    st.caption(t("storage_cleanup_caption", workspace_id))
    use_cache = st.checkbox(t("cleanup_cache", workspace_id), value=True)
    use_outputs = st.checkbox(t("cleanup_outputs", workspace_id), value=True)
    use_exports = st.checkbox(t("cleanup_exports", workspace_id), value=True)
    dry_run = st.checkbox(t("cleanup_dry_run", workspace_id), value=True)
    confirm_apply = st.checkbox(t("cleanup_confirm", workspace_id), value=False)
    targets = _targets(
        workspace_id,
        [key for key, enabled in {
            "cache": use_cache,
            "outputs": use_outputs,
            "exports": use_exports,
        }.items() if enabled],
    )
    st.caption(t("cleanup_targets", workspace_id))
    for path in targets:
        st.code(str(path))

    if st.button(t("run_cleanup", workspace_id), disabled=locked, help=lock_msg or None):
        if dry_run or not confirm_apply:
            st.info(t("cleanup_dry_run_only", workspace_id))
            return
        for path in targets:
            if path.exists():
                import shutil

                shutil.rmtree(path, ignore_errors=True)
        st.success(t("cleanup_complete", workspace_id))

    st.markdown(f"#### {t('workspace_layout', workspace_id)}")
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

from __future__ import annotations

import os
import signal

import streamlit as st

from app.ui.i18n import t
from core.ui_state.storage import get_setting, set_setting
from app.ui.locks import running_task_summary
from core.tasks.executor import shutdown_executor
from service.workspace_service import create_workspace, list_workspaces


NAV_ITEMS = ["Start", "Library", "Create", "Tools", "Help"]


def _clean_exit() -> None:
    """Perform a clean exit by terminating the process."""
    shutdown_executor(wait=False, cancel_futures=True)
    # Send SIGTERM to the current process to terminate cleanly
    os.kill(os.getpid(), signal.SIGTERM)


def render_sidebar() -> tuple[str | None, str]:
    with st.sidebar:
        active_workspace = st.session_state.get("workspace_id")
        st.markdown(f"## {t('app_title', active_workspace)}")
        st.caption(t("projects_caption", active_workspace))

        workspaces = list_workspaces()
        workspace_names = {ws["name"]: ws["id"] for ws in workspaces}
        last_workspace = get_setting(None, "last_workspace_id") or ""
        options = [t("new_project", active_workspace)] + list(workspace_names.keys())
        default_index = 0
        if last_workspace:
            for idx, name in enumerate(options):
                if workspace_names.get(name) == last_workspace:
                    default_index = idx
                    break
        selected_name = st.selectbox(
            t("project", active_workspace),
            options=options,
            index=default_index,
            help=t("project_select_help", active_workspace),
        )

        workspace_id = None
        if selected_name == t("new_project", active_workspace):
            new_name = st.text_input(t("new_project_name", active_workspace))
            if st.button(
                t("create_project", active_workspace),
                disabled=not new_name.strip(),
            ):
                workspace_id = create_workspace(new_name.strip())
                st.session_state["workspace_id"] = workspace_id
                set_setting(None, "last_workspace_id", workspace_id)
                st.success(t("project_created", active_workspace))
        else:
            workspace_id = workspace_names[selected_name]
            st.session_state["workspace_id"] = workspace_id
            set_setting(None, "last_workspace_id", workspace_id)

        st.markdown(f"### {t('navigation', active_workspace)}")
        if "active_nav" not in st.session_state:
            st.session_state["active_nav"] = "Start"
        nav = st.radio(
            t("go_to", active_workspace),
            options=NAV_ITEMS,
            index=NAV_ITEMS.index(st.session_state.get("active_nav", "Start")),
            label_visibility="collapsed",
            format_func=lambda value: t(f"nav_{value.lower()}", active_workspace),
            key="nav_radio",
            on_change=lambda: st.session_state.update({"active_nav": st.session_state["nav_radio"]}),
        )
        nav = st.session_state.get("active_nav", "Start")

        if st.button(t("refresh_app", active_workspace)):
            st.rerun()

        st.divider()
        if st.button(t("settings", active_workspace)):
            st.session_state["active_nav"] = "Tools"
            st.session_state["tools_tab"] = "settings"
            st.rerun()

        st.divider()
        if st.button(t("exit_app", active_workspace), type="primary"):
            locked, lock_msg = running_task_summary(workspace_id)
            if locked:
                st.session_state["exit_has_tasks"] = True
            else:
                st.session_state["exit_has_tasks"] = False
            st.session_state["exit_requested"] = True

        if st.session_state.get("exit_requested"):
            if st.session_state.get("exit_has_tasks"):
                st.warning(t("exit_tasks_running", active_workspace))
            if st.button(t("confirm_exit", active_workspace)):
                _clean_exit()

    return workspace_id, nav


def render_main_columns() -> tuple[st.delta_generator.DeltaGenerator, st.delta_generator.DeltaGenerator]:
    main, inspector = st.columns([2.4, 1.1], gap="large")
    return main, inspector

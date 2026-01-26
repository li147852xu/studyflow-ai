from __future__ import annotations

import streamlit as st

from app.ui.i18n import t
from core.ui_state.storage import get_setting, set_setting
from app.ui.locks import running_task_summary
from core.tasks.executor import shutdown_executor
import os
from service.workspace_service import create_workspace, list_workspaces


NAV_ITEMS = ["Start", "Library", "Create", "Tools"]


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
        nav = st.radio(
            t("go_to", active_workspace),
            options=NAV_ITEMS,
            index=NAV_ITEMS.index(st.session_state.get("active_nav", "Start")),
            label_visibility="collapsed",
            format_func=lambda value: t(f"nav_{value.lower()}", active_workspace),
        )
        st.session_state["active_nav"] = nav

        st.divider()
        if st.button(t("settings", active_workspace)):
            st.session_state["active_nav"] = "Tools"
            st.session_state["tools_tab"] = "settings"
            st.rerun()

        st.divider()
        if st.button(t("exit_app", active_workspace), type="primary"):
            st.session_state["exit_requested"] = True

        if st.session_state.get("exit_requested"):
            locked, lock_msg = running_task_summary(workspace_id)
            if locked:
                st.warning(lock_msg)
                choice = st.radio(
                    t("exit_choice", active_workspace),
                    options=["wait", "force"],
                    format_func=lambda value: t(f"exit_{value}", active_workspace),
                )
                if st.button(t("confirm_exit", active_workspace)):
                    shutdown_executor(wait=choice == "wait")
                    os._exit(0)
            else:
                if st.button(t("confirm_exit", active_workspace)):
                    shutdown_executor(wait=True)
                    os._exit(0)

    return workspace_id, nav


def render_main_columns() -> tuple[st.delta_generator.DeltaGenerator, st.delta_generator.DeltaGenerator]:
    main, inspector = st.columns([2.4, 1.1], gap="large")
    return main, inspector

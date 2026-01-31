from __future__ import annotations

import json

import streamlit as st

from app.ui.i18n import t
from app.ui.locks import running_task_summary
from core.plugins.base import PluginContext
from core.plugins.registry import get_plugin, list_plugins, load_builtin_plugins


def render_plugins_center(*, workspace_id: str | None) -> None:
    st.markdown(f"### {t('plugins_center_title', workspace_id)}")
    if not workspace_id:
        st.info(t("plugins_select_project", workspace_id))
        return
    locked, lock_msg = running_task_summary(workspace_id)
    if lock_msg:
        st.info(lock_msg)

    load_builtin_plugins()
    plugins = list_plugins()
    if not plugins:
        st.caption(t("plugins_empty", workspace_id))
        return

    plugin_names = [plugin.name for plugin in plugins]
    selected = st.selectbox(t("plugin_label", workspace_id), options=plugin_names)
    plugin = get_plugin(selected)

    st.caption(f"{plugin.description} (v{plugin.version})")
    args_text = st.text_area(
        t("plugin_args_label", workspace_id),
        value='{"path": ""}',
        height=120,
        help=t("plugin_args_help", workspace_id),
    )
    if st.button(t("run_plugin", workspace_id), disabled=locked, help=lock_msg or None):
        try:
            args = json.loads(args_text) if args_text.strip() else {}
        except json.JSONDecodeError:
            st.error(t("plugin_args_invalid", workspace_id))
            return
        result = plugin.run(PluginContext(workspace_id=workspace_id, args=args))
        if result.ok:
            st.success(result.message)
            if result.data:
                st.json(result.data)
        else:
            st.error(result.message)

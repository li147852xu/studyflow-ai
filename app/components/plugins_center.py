from __future__ import annotations

import json

import streamlit as st

from core.plugins.base import PluginContext
from core.plugins.registry import get_plugin, list_plugins, load_builtin_plugins
from app.ui.locks import running_task_summary


def render_plugins_center(*, workspace_id: str | None) -> None:
    st.markdown("### Plugins Center")
    if not workspace_id:
        st.info("Select a project to run plugins.")
        return
    locked, lock_msg = running_task_summary(workspace_id)
    if lock_msg:
        st.info(lock_msg)

    load_builtin_plugins()
    plugins = list_plugins()
    if not plugins:
        st.caption("No plugins registered.")
        return

    plugin_names = [plugin.name for plugin in plugins]
    selected = st.selectbox("Plugin", options=plugin_names)
    plugin = get_plugin(selected)

    st.caption(f"{plugin.description} (v{plugin.version})")
    args_text = st.text_area(
        "Arguments (JSON)",
        value='{"path": ""}',
        height=120,
        help="Provide plugin args in JSON format.",
    )
    if st.button("Run plugin", disabled=locked, help=lock_msg or None):
        try:
            args = json.loads(args_text) if args_text.strip() else {}
        except json.JSONDecodeError:
            st.error("Arguments must be valid JSON.")
            return
        result = plugin.run(PluginContext(workspace_id=workspace_id, args=args))
        if result.ok:
            st.success(result.message)
            if result.data:
                st.json(result.data)
        else:
            st.error(result.message)

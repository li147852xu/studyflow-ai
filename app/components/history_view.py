from __future__ import annotations

import streamlit as st

from core.ui_state.storage import list_history, clear_history


def render_history(workspace_id: str) -> None:
    st.sidebar.header("History")
    action_filter = st.sidebar.selectbox(
        "Filter",
        options=["all", "chat", "course_overview", "course_cheatsheet", "paper_card", "paper_aggregate", "slides"],
        index=0,
    )
    entries = list_history(workspace_id, action_filter)
    if not entries:
        st.sidebar.caption("No history yet.")
        return
    for entry in entries:
        st.sidebar.write(f"{entry['created_at']} · {entry['action_type']}")
        st.sidebar.caption(entry.get("summary") or "")
        if entry.get("preview"):
            st.sidebar.caption(entry["preview"][:200])
    confirm = st.sidebar.checkbox("Confirm clear history")
    if st.sidebar.button("Clear history", disabled=not confirm):
        clear_history(workspace_id)
        st.sidebar.success("History cleared.")

import streamlit as st

from infra.models import init_db
from core.ui_state.storage import get_setting


def init_app_state() -> None:
    init_db()
    st.session_state.setdefault("llm_base_url", get_setting(None, "llm_base_url") or "")
    st.session_state.setdefault("llm_model", get_setting(None, "llm_model") or "")
    st.session_state.setdefault("llm_api_key", "")


def require_workspace() -> str | None:
    workspace_id = st.session_state.get("workspace_id")
    if not workspace_id:
        st.warning("Please create or select a workspace in the sidebar.")
        return None
    return workspace_id

import streamlit as st

from infra.models import init_db
from core.ui_state.storage import get_setting


def init_app_state() -> None:
    init_db()
    st.session_state.setdefault("workspace_id", get_setting(None, "last_workspace_id") or "")
    st.session_state.setdefault("llm_base_url", get_setting(None, "llm_base_url") or "")
    st.session_state.setdefault("llm_model", get_setting(None, "llm_model") or "")
    st.session_state.setdefault("llm_api_key", "")
    st.session_state.setdefault(
        "llm_temperature", float(get_setting(None, "llm_temperature") or 0.2)
    )
    st.session_state.setdefault(
        "api_mode", get_setting(None, "api_mode") or "direct"
    )
    st.session_state.setdefault(
        "api_base_url", get_setting(None, "api_base_url") or "http://127.0.0.1:8000"
    )
    st.session_state.setdefault(
        "ocr_mode", get_setting(None, "ocr_mode") or "off"
    )
    st.session_state.setdefault(
        "ocr_threshold", int(get_setting(None, "ocr_threshold") or 50)
    )
    st.session_state.setdefault(
        "prompt_version", get_setting(None, "prompt_version") or "v1"
    )
    st.session_state.setdefault("active_nav", "Home")
    st.session_state.setdefault("retrieval_mode", "vector")


def require_workspace() -> str | None:
    workspace_id = st.session_state.get("workspace_id")
    if not workspace_id:
        st.warning("Please create or select a workspace in the sidebar.")
        return None
    return workspace_id

from __future__ import annotations

import streamlit as st

from infra.models import init_db
from core.ui_state.storage import get_setting


def init_app_state() -> None:
    init_db()
    st.session_state.setdefault("workspace_id", get_setting(None, "last_workspace_id") or "")
    st.session_state.setdefault("llm_base_url", get_setting(None, "llm_base_url") or "")
    st.session_state.setdefault("llm_model", get_setting(None, "llm_model") or "")
    st.session_state.setdefault("llm_api_key", get_setting(None, "llm_api_key") or "")
    st.session_state.setdefault(
        "llm_temperature", float(get_setting(None, "llm_temperature") or 0.2)
    )
    stored_api_mode = get_setting(None, "api_mode") or "direct"
    if stored_api_mode not in {"direct", "api"}:
        stored_api_mode = "direct"
    st.session_state.setdefault("api_mode", stored_api_mode)
    st.session_state.setdefault(
        "api_base_url", get_setting(None, "api_base_url") or "http://127.0.0.1:8000"
    )
    st.session_state.setdefault("ocr_mode", get_setting(None, "ocr_mode") or "auto")
    st.session_state.setdefault(
        "ocr_threshold", int(get_setting(None, "ocr_threshold") or 50)
    )
    st.session_state.setdefault(
        "prompt_version", get_setting(None, "prompt_version") or "v1"
    )
    st.session_state.setdefault("ui_language", get_setting(None, "ui_language") or "en")
    st.session_state.setdefault(
        "output_language", get_setting(None, "output_language") or "en"
    )
    st.session_state.setdefault("active_nav", "Start")
    st.session_state.setdefault("tools_tab", "coach")
    st.session_state.setdefault("create_tab", "course")
    st.session_state.setdefault("retrieval_mode", "auto")
    st.session_state.setdefault("inspector_collapsed", False)
    st.session_state.setdefault("last_seen_task_state", "")
    st.session_state.setdefault("auto_refresh_last", 0.0)


def require_workspace() -> str | None:
    workspace_id = st.session_state.get("workspace_id")
    if not workspace_id:
        st.warning("Please create or select a project to continue.")
        return None
    return workspace_id

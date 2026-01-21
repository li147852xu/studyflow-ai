import streamlit as st

from infra.models import init_db
from service.workspace_service import create_workspace, list_workspaces


def init_app_state() -> None:
    init_db()
    st.session_state.setdefault("llm_base_url", "")
    st.session_state.setdefault("llm_model", "")
    st.session_state.setdefault("llm_api_key", "")


def sidebar_workspace() -> None:
    st.sidebar.header("Workspace")
    workspaces = list_workspaces()
    workspace_names = {ws["name"]: ws["id"] for ws in workspaces}
    selected_name = st.sidebar.selectbox(
        "Select workspace",
        options=["(new)"] + list(workspace_names.keys()),
    )

    if selected_name == "(new)":
        new_name = st.sidebar.text_input("New workspace name")
        if st.sidebar.button("Create workspace"):
            if not new_name.strip():
                st.sidebar.error("Workspace name cannot be empty.")
            else:
                workspace_id = create_workspace(new_name.strip())
                st.session_state["workspace_id"] = workspace_id
                st.sidebar.success("Workspace created.")
    else:
        st.session_state["workspace_id"] = workspace_names[selected_name]

    if "workspace_id" in st.session_state:
        st.sidebar.caption(f"Active workspace: {st.session_state['workspace_id']}")


def sidebar_llm() -> None:
    st.sidebar.header("LLM Provider")
    st.sidebar.text_input(
        "Base URL",
        value=st.session_state.get("llm_base_url", ""),
        key="llm_base_url",
    )
    st.sidebar.text_input(
        "Model",
        value=st.session_state.get("llm_model", ""),
        key="llm_model",
    )
    st.sidebar.text_input(
        "API Key",
        value=st.session_state.get("llm_api_key", ""),
        type="password",
        key="llm_api_key",
    )


def require_workspace() -> str | None:
    workspace_id = st.session_state.get("workspace_id")
    if not workspace_id:
        st.warning("Please create or select a workspace in the sidebar.")
        return None
    return workspace_id

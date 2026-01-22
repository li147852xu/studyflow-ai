from __future__ import annotations

import streamlit as st

from core.ui_state.storage import get_setting, set_setting
from service.workspace_service import (
    create_workspace,
    delete_workspace,
    list_workspaces,
    rename_workspace,
)
from infra.db import get_connection, get_workspaces_dir
from core.retrieval.vector_store import VectorStore, VectorStoreSettings


def _index_status(workspace_id: str) -> dict:
    with get_connection() as connection:
        doc_row = connection.execute(
            "SELECT COUNT(*) as count FROM documents WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
        chunk_row = connection.execute(
            "SELECT COUNT(*) as count FROM chunks WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
    vector_count = 0
    try:
        settings = VectorStoreSettings(
            persist_directory=get_workspaces_dir() / workspace_id / "index" / "chroma",
            collection_name=f"workspace_{workspace_id}",
        )
        vector_count = VectorStore(settings).count()
    except Exception:
        vector_count = 0
    bm25_path = get_workspaces_dir() / workspace_id / "index" / "bm25" / "index.pkl"
    return {
        "documents": int(doc_row["count"]) if doc_row else 0,
        "chunks": int(chunk_row["count"]) if chunk_row else 0,
        "vector_index": vector_count,
        "bm25_index": bm25_path.exists(),
    }


def sidebar_workspace() -> str | None:
    st.sidebar.header("Workspace")
    workspaces = list_workspaces()
    workspace_names = {ws["name"]: ws["id"] for ws in workspaces}
    last_workspace = get_setting(None, "last_workspace_id")
    options = ["(new)"] + list(workspace_names.keys())
    default_index = 0
    if last_workspace:
        for idx, name in enumerate(options):
            if workspace_names.get(name) == last_workspace:
                default_index = idx
                break
    selected_name = st.sidebar.selectbox(
        "Select workspace",
        options=options,
        index=default_index,
        help="Choose an existing workspace or create a new one.",
    )

    workspace_id = None
    if selected_name == "(new)":
        new_name = st.sidebar.text_input("New workspace name")
        if st.sidebar.button("Create workspace"):
            if not new_name.strip():
                st.sidebar.error("Workspace name cannot be empty.")
            else:
                workspace_id = create_workspace(new_name.strip())
                st.session_state["workspace_id"] = workspace_id
                set_setting(None, "last_workspace_id", workspace_id)
                st.sidebar.success("Workspace created.")
    else:
        workspace_id = workspace_names[selected_name]
        st.session_state["workspace_id"] = workspace_id
        set_setting(None, "last_workspace_id", workspace_id)

    if workspace_id:
        st.sidebar.caption(f"Active workspace: {workspace_id}")

        st.sidebar.subheader("Manage")
        rename_to = st.sidebar.text_input("Rename to", value="")
        if st.sidebar.button("Rename workspace"):
            if not rename_to.strip():
                st.sidebar.error("New name cannot be empty.")
            else:
                rename_workspace(workspace_id, rename_to.strip())
                st.sidebar.success("Workspace renamed. Refresh list.")

        confirm = st.sidebar.checkbox("Confirm delete")
        if st.sidebar.button("Delete workspace", disabled=not confirm):
            delete_workspace(workspace_id)
            ws_dir = get_workspaces_dir() / workspace_id
            if ws_dir.exists():
                import shutil

                shutil.rmtree(ws_dir)
            st.sidebar.success("Workspace deleted. Refresh list.")
            st.session_state.pop("workspace_id", None)

        st.sidebar.subheader("Index Status")
        status = _index_status(workspace_id)
        st.sidebar.write(f"Documents: {status['documents']}")
        st.sidebar.write(f"Chunks: {status['chunks']}")
        st.sidebar.write(f"Vector index items: {status['vector_index']}")
        st.sidebar.write(f"BM25 index present: {status['bm25_index']}")

    return workspace_id


def sidebar_llm() -> None:
    st.sidebar.header("LLM Provider")
    base_url = st.sidebar.text_input(
        "Base URL",
        value=st.session_state.get("llm_base_url", ""),
        key="llm_base_url",
        help="Example: https://api.openai.com/v1",
    )
    model = st.sidebar.text_input(
        "Chat Model",
        value=st.session_state.get("llm_model", ""),
        key="llm_model",
        help="Example: gpt-4o-mini or deepseek-chat",
    )
    api_key = st.sidebar.text_input(
        "API Key",
        value=st.session_state.get("llm_api_key", ""),
        type="password",
        key="llm_api_key",
        help="Stored only in session. Prefer environment variables.",
    )
    if base_url:
        set_setting(None, "llm_base_url", base_url)
    if model:
        set_setting(None, "llm_model", model)


def sidebar_retrieval_mode(workspace_id: str | None) -> str:
    st.sidebar.header("Retrieval Mode")
    default_mode = "vector"
    if workspace_id:
        stored = get_setting(workspace_id, "retrieval_mode")
        if stored:
            default_mode = stored
    mode = st.sidebar.selectbox(
        "Mode",
        options=["vector", "bm25", "hybrid"],
        index=["vector", "bm25", "hybrid"].index(default_mode)
        if default_mode in ["vector", "bm25", "hybrid"]
        else 0,
        help="Vector uses embeddings, BM25 uses lexical match, Hybrid fuses both.",
    )
    if workspace_id:
        set_setting(workspace_id, "retrieval_mode", mode)
    return mode

from __future__ import annotations

import streamlit as st

from app.components.dialogs import confirm_action
from core.retrieval.vector_store import VectorStore, VectorStoreSettings
from core.ui_state.storage import get_setting, set_setting
from infra.db import get_connection, get_workspaces_dir
from service.workspace_service import (
    create_workspace,
    delete_workspace,
    list_workspaces,
    rename_workspace,
)

NAV_ITEMS = [
    "Home",
    "Library",
    "Workflows",
    "Coach",
    "Exports",
    "Tasks",
    "Plugins",
    "History",
    "Settings",
    "Help",
    "Diagnostics",
]


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


def render_nav() -> tuple[str | None, str]:
    st.markdown("## StudyFlow-AI")
    st.caption("Projects, navigation, and status.")

    workspaces = list_workspaces()
    workspace_names = {ws["name"]: ws["id"] for ws in workspaces}
    last_workspace = get_setting(None, "last_workspace_id") or ""
    options = ["(new project)"] + list(workspace_names.keys())
    default_index = 0
    if last_workspace:
        for idx, name in enumerate(options):
            if workspace_names.get(name) == last_workspace:
                default_index = idx
                break
    selected_name = st.selectbox(
        "Project",
        options=options,
        index=default_index,
        help="Choose an existing project or create a new one.",
    )

    workspace_id = None
    if selected_name == "(new project)":
        new_name = st.text_input("New project name")
        if st.button("Create project", disabled=not new_name.strip()):
            workspace_id = create_workspace(new_name.strip())
            st.session_state["workspace_id"] = workspace_id
            set_setting(None, "last_workspace_id", workspace_id)
            st.success("Project created.")
    else:
        workspace_id = workspace_names[selected_name]
        st.session_state["workspace_id"] = workspace_id
        set_setting(None, "last_workspace_id", workspace_id)

    if workspace_id:
        st.caption(f"Active project: {workspace_id}")
        with st.expander("Manage project"):
            rename_to = st.text_input("Rename to", value="", key="rename_workspace")
            if st.button("Rename project", disabled=not rename_to.strip()):
                rename_workspace(workspace_id, rename_to.strip())
                st.success("Project renamed. Refresh list.")

            confirm = confirm_action(
                key="confirm_workspace_delete",
                label="Confirm delete",
                help_text="Deletes project metadata and local files.",
            )
            if st.button("Delete project", disabled=not confirm, type="primary"):
                delete_workspace(workspace_id)
                ws_dir = get_workspaces_dir() / workspace_id
                if ws_dir.exists():
                    import shutil

                    shutil.rmtree(ws_dir)
                st.success("Project deleted. Refresh list.")
                st.session_state.pop("workspace_id", None)
                workspace_id = None

        st.subheader("Navigation")
        nav = st.radio(
            "Go to",
            options=NAV_ITEMS,
            index=NAV_ITEMS.index(st.session_state.get("active_nav", "Home")),
            label_visibility="collapsed",
        )
        st.session_state["active_nav"] = nav

        st.subheader("Project status")
        status = _index_status(workspace_id)
        st.metric("Documents", status["documents"])
        st.metric("Chunks", status["chunks"])
        st.caption(f"Search Ready: {status['vector_index'] > 0}")
        st.caption(f"BM25 index present: {status['bm25_index']}")
    else:
        nav = st.radio(
            "Go to",
            options=NAV_ITEMS,
            index=NAV_ITEMS.index("Home"),
            label_visibility="collapsed",
        )
        st.session_state["active_nav"] = nav

    return workspace_id, nav

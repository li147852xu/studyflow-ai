from __future__ import annotations

import streamlit as st

from app.components.inspector import render_download, render_metadata
from app.ui.components import render_answer_with_citations


def render_result_viewer(
    *,
    title: str,
    content: str | None,
    citations: list[str] | None = None,
    download_path: str | None = None,
    run_id: str | None = None,
) -> None:
    st.markdown(f"### {title}")
    if content:
        render_answer_with_citations(
            text=content,
            citations=citations,
            workspace_id=st.session_state.get("workspace_id"),
        )
    else:
        st.caption("No content to preview.")

    if run_id:
        render_metadata({"Run ID": run_id})
    if download_path:
        render_download(download_path)

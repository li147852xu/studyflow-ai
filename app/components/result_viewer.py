from __future__ import annotations

import streamlit as st

from app.components.inspector import render_citations, render_download, render_metadata


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
        st.write(content)
    else:
        st.caption("No content to preview.")

    if run_id:
        render_metadata({"Run ID": run_id})
    if citations:
        render_citations(citations)
    if download_path:
        render_download(download_path)

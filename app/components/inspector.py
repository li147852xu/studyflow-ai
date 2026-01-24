from __future__ import annotations

import streamlit as st

from core.telemetry.run_logger import _run_dir


def render_section_title(title: str) -> None:
    st.markdown(f"#### {title}")


def render_metadata(metadata: dict[str, str]) -> None:
    for key, value in metadata.items():
        st.caption(f"{key}: {value}")


def render_citations(citations: list[str]) -> None:
    if not citations:
        st.caption("No citations yet.")
        return
    for citation in citations:
        st.write(citation)


def render_run_info(workspace_id: str, run_id: str | None) -> None:
    if not run_id:
        return
    st.caption(f"run_id: {run_id}")
    st.caption(f"log: {_run_dir(workspace_id)}/run_{run_id}.json")


def render_download(label: str, content: str, filename: str) -> None:
    st.download_button(label, content, file_name=filename)

from __future__ import annotations

import streamlit as st

from core.telemetry.run_logger import _run_dir
from core.assets.store import get_asset
from service.asset_service import (
    diff_versions,
    export_version_citations,
    list_versions,
    read_version,
    set_active,
)


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


def render_asset_versions(
    *,
    workspace_id: str,
    asset_id: str | None,
) -> None:
    if not asset_id:
        st.caption("No asset versions available.")
        return
    asset = get_asset(asset_id)
    current_version_id = asset.active_version_id
    versions = list_versions(asset_id)
    if not versions:
        st.caption("No versions yet.")
        return
    st.caption(f"asset_id: {asset_id}")
    version_labels = {
        version.id: f"v{version.version_index} · {version.created_at[:19]}"
        for version in versions
    }
    selected_version = st.selectbox(
        "Version",
        options=[version.id for version in versions],
        format_func=lambda vid: version_labels.get(vid, vid),
        index=0,
    )
    view = read_version(asset_id, selected_version)
    st.caption(f"run_id: {view.version.run_id or '-'}")
    st.caption(f"model: {view.version.model or '-'}")
    if st.button("Set as current", disabled=selected_version == current_version_id):
        set_active(asset_id, selected_version)
        st.success("Active version updated.")

    st.markdown("#### Version preview")
    st.write(view.content[:1200] + ("..." if len(view.content) > 1200 else ""))

    st.markdown("#### Compare")
    col_a, col_b = st.columns(2)
    with col_a:
        compare_a = st.selectbox(
            "Compare A",
            options=[version.id for version in versions],
            format_func=lambda vid: version_labels.get(vid, vid),
            index=0,
            key=f"compare_a_{asset_id}",
        )
    with col_b:
        compare_b = st.selectbox(
            "Compare B",
            options=[version.id for version in versions],
            format_func=lambda vid: version_labels.get(vid, vid),
            index=1 if len(versions) > 1 else 0,
            key=f"compare_b_{asset_id}",
        )
    if st.button("Show diff", key=f"diff_{asset_id}"):
        diff = diff_versions(asset_id, compare_a, compare_b)
        st.code(diff or "No differences.")

    st.markdown("#### Export citations")
    if st.button("Export JSON + TXT", key=f"export_citations_{asset_id}"):
        paths = export_version_citations(
            workspace_id=workspace_id,
            asset_id=asset_id,
            version_id=selected_version,
            formats=["json", "txt"],
        )
        st.success("Citations exported.")
        for fmt, path in paths.items():
            st.caption(f"{fmt}: {path}")

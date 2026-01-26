from __future__ import annotations

import json

import streamlit as st

from service.asset_service import read_version_by_id
from service.pack_service import make_pack, PackServiceError
from service.recent_activity_service import list_recent_activity


def _parse_output_ref(output_ref: str | None) -> dict:
    if not output_ref:
        return {}
    try:
        data = json.loads(output_ref)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        if "/" in output_ref or output_ref.endswith((".zip", ".tar", ".gz", ".txt", ".md")):
            return {"path": output_ref}
        return {"asset_version_id": output_ref}


def render_recent_activity(*, workspace_id: str) -> None:
    st.markdown("### Recent Activity")
    entries = list_recent_activity(workspace_id, limit=30)
    if not entries:
        st.caption("No recent activity yet.")
        return
    preferred_id = st.session_state.get("recent_activity_selected_id")
    if preferred_id and preferred_id in [entry["id"] for entry in entries]:
        default_index = [entry["id"] for entry in entries].index(preferred_id)
    else:
        default_index = 0
    selected_id = st.selectbox(
        "Select activity",
        options=[entry["id"] for entry in entries],
        index=default_index,
        format_func=lambda entry_id: next(
            (
                f"{entry['created_at']} · {entry['type']} · {entry.get('title') or '-'}"
                for entry in entries
                if entry["id"] == entry_id
            ),
            entry_id,
        ),
    )
    if preferred_id:
        st.session_state["recent_activity_selected_id"] = selected_id
    selected = next(entry for entry in entries if entry["id"] == selected_id)
    st.write(
        {
            "Type": selected["type"],
            "Title": selected.get("title") or "-",
            "Status": selected.get("status") or "-",
            "Created": selected.get("created_at") or "-",
        }
    )
    if selected.get("citations_summary"):
        st.caption(selected["citations_summary"])

    output_ref = _parse_output_ref(selected.get("output_ref"))
    kind = output_ref.get("kind") or selected.get("type", "")
    if kind.startswith("generate_"):
        kind = kind.replace("generate_", "")
    if kind.startswith("course_"):
        st.caption("Scope: course-only")
    elif kind.startswith("paper_"):
        st.caption("Scope: paper-only")
    elif kind == "slides":
        st.caption("Scope: all-docs")
    if output_ref.get("path"):
        st.caption(f"Output path: {output_ref['path']}")
        return
    version_id = output_ref.get("asset_version_id")
    if not version_id:
        st.caption("No output saved for this activity.")
        return

    try:
        view = read_version_by_id(version_id)
    except Exception as exc:
        st.error(str(exc))
        return

    st.divider()
    st.markdown("#### Output")
    st.text_area("Output", value=view.content, height=260)
    st.download_button(
        "Download output",
        data=view.content,
        file_name=f"{selected['type']}.txt",
    )

    source_id = output_ref.get("source_id")
    kind = output_ref.get("kind")
    pack_type_map = {
        "slides": "slides",
        "course_overview": "exam",
        "course_cheatsheet": "exam",
        "course_explain": "exam",
        "paper_aggregate": "related",
    }
    pack_type = pack_type_map.get(kind or "")
    if source_id and pack_type:
        if st.button("Export pack"):
            try:
                path = make_pack(
                    workspace_id=workspace_id,
                    pack_type=pack_type,
                    source_id=source_id if isinstance(source_id, str) else ",".join(source_id),
                )
                st.success(f"Pack created: {path}")
            except PackServiceError as exc:
                st.error(str(exc))

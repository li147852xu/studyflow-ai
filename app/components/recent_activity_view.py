from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from app.ui.i18n import t
from service.asset_service import read_version_by_id
from service.pack_service import PackServiceError, make_pack
from service.recent_activity_service import list_recent_activity
from service.tasks_service import list_tasks_for_workspace


def _format_time(iso_time: str | None) -> str:
    if not iso_time:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return iso_time[:19] if iso_time else "-"


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
    st.markdown(f"### {t('recent_activity', workspace_id)}")
    tasks = list_tasks_for_workspace(workspace_id=workspace_id)
    active_tasks = []
    for task in tasks:
        task_type = task.type if hasattr(task, "type") else task.get("type")
        task_status = task.status if hasattr(task, "status") else task.get("status")
        if not task_type or not task_type.startswith("generate_"):
            continue
        if task_status not in {"queued", "running"}:
            continue
        payload_json = task.payload_json if hasattr(task, "payload_json") else task.get("payload_json")
        title = None
        if payload_json:
            try:
                payload = json.loads(payload_json)
                title = (payload.get("payload") or {}).get("title")
            except json.JSONDecodeError:
                title = None
        active_tasks.append(
            {
                "type": task_type.replace("generate_", ""),
                "status": task_status,
                "progress": task.progress if hasattr(task, "progress") else task.get("progress"),
                "title": title or task_type,
            }
        )
    if active_tasks:
        st.markdown(f"#### {t('tasks_in_progress', workspace_id)}")
        for task in active_tasks:
            status_label = t(f"task_status_{task['status']}", workspace_id)
            st.caption(f"{task['title']} · {task['type']} · {status_label}")
            if task.get("progress") is not None:
                progress_value = float(task["progress"])
                if progress_value > 1:
                    progress_value = progress_value / 100
                st.progress(max(0.0, min(1.0, progress_value)))

    entries = list_recent_activity(workspace_id, limit=30)
    if not entries:
        st.caption(t("no_recent_activity", workspace_id))
        return
    preferred_id = st.session_state.get("recent_activity_selected_id")
    if preferred_id and preferred_id in [entry["id"] for entry in entries]:
        default_index = [entry["id"] for entry in entries].index(preferred_id)
    else:
        default_index = 0
    selected_id = st.selectbox(
        t("select_activity", workspace_id),
        options=[entry["id"] for entry in entries],
        index=default_index,
        format_func=lambda entry_id: next(
            (
                f"{_format_time(entry['created_at'])} · {entry['type']} · {entry.get('title') or '-'}"
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
            t("activity_type", workspace_id): selected["type"],
            t("activity_title", workspace_id): selected.get("title") or "-",
            t("activity_status", workspace_id): selected.get("status") or "-",
            t("created", workspace_id): _format_time(selected.get("created_at")),
        }
    )
    if selected.get("citations_summary"):
        st.caption(selected["citations_summary"])

    output_ref = _parse_output_ref(selected.get("output_ref"))
    kind = output_ref.get("kind") or selected.get("type", "")
    if kind.startswith("generate_"):
        kind = kind.replace("generate_", "")
    if kind.startswith("course_"):
        st.caption(t("scope_course_only", workspace_id))
    elif kind.startswith("paper_"):
        st.caption(t("scope_paper_only", workspace_id))
    elif kind == "slides":
        st.caption(t("scope_all_docs", workspace_id))
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
    st.markdown(view.content)
    st.download_button(
        "Download output",
        data=view.content,
        file_name=f"{selected['type']}.md",
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

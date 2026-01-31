from __future__ import annotations

import html
import json
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from app.ui.i18n import t
from core.ingest.cite import build_citation
from service.tasks_service import list_tasks_for_workspace


def section_title(text: str) -> None:
    st.markdown(f"<div class='sf-section-title'>{text}</div>", unsafe_allow_html=True)


def muted(text: str) -> None:
    st.markdown(f"<span class='sf-muted'>{text}</span>", unsafe_allow_html=True)


def card_header(title: str, subtitle: str | None = None) -> None:
    st.markdown("<div class='sf-card'>", unsafe_allow_html=True)
    section_title(title)
    if subtitle:
        muted(subtitle)


def card_footer() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_inspector(
    *,
    status: dict | None = None,
    citations: list[str] | None = None,
    exports: list[dict] | None = None,
    history: list[dict] | None = None,
    versions: list[dict] | None = None,
) -> None:
    st.markdown(f"### {t('inspector')}")
    collapsed = st.checkbox(
        t("collapse_inspector"),
        value=st.session_state.get("inspector_collapsed", False),
    )
    st.session_state["inspector_collapsed"] = collapsed
    if collapsed:
        st.caption(t("inspector_collapsed"))
        return

    if status:
        with st.expander(t("status"), expanded=True):
            for key, value in status.items():
                st.write(f"{key}: {value}")

    if citations is not None:
        render_citations_list(citations, st.session_state.get("workspace_id"))

    if exports:
        with st.expander(t("exports"), expanded=False):
            for item in exports:
                st.write(item)

    if versions:
        with st.expander(t("versions"), expanded=False):
            for item in versions:
                st.write(item)

    if history:
        with st.expander(t("history"), expanded=False):
            for item in history:
                st.write(item)


def run_with_progress(
    *,
    label: str,
    work: callable,
    success_label: str | None = None,
    error_label: str | None = None,
    use_status: bool = True,
) -> tuple[bool, object | None]:
    status = st.status(label, expanded=False) if use_status else st.empty()
    progress = st.progress(0.05)
    try:
        result = work()
        progress.progress(1.0)
        if use_status:
            status.update(
                label=success_label or label,
                state="complete",
            )
        else:
            status.success(success_label or label)
        return True, result
    except Exception as exc:
        progress.progress(1.0)
        if use_status:
            status.update(
                label=error_label or label,
                state="error",
            )
        else:
            status.error(error_label or label)
        st.error(str(exc))
        return False, None


def render_answer_with_citations(
    *, text: str, citations: list[str] | None, workspace_id: str | None
) -> None:
    if not text:
        st.caption(t("no_output", workspace_id))
        return
    if citations:
        parsed = _parse_citations(citations)
        rendered = _inject_citation_tooltips(text, parsed)
        st.markdown(rendered, unsafe_allow_html=True)
        _render_citations_expander(parsed, workspace_id)
    else:
        st.markdown(text)


def _inject_citation_tooltips(text: str, parsed: list[dict]) -> str:
    lookup = {item["index"]: item for item in parsed}

    def _replace(match: re.Match) -> str:
        idx = int(match.group(1))
        info = lookup.get(idx)
        if not info:
            return match.group(0)
        tooltip = f"{info['source']} · {info['location']} — {info['snippet']}"
        tooltip = html.escape(tooltip)
        return f"<span class='sf-citation' data-tooltip='{tooltip}'>[{idx}]</span>"

    return re.sub(r"\[(\d+)\]", _replace, text)


def _render_citations_expander(parsed: list[dict], workspace_id: str | None) -> None:
    if not parsed:
        return
    with st.expander(t("citations", workspace_id), expanded=False):
        for item in parsed:
            st.markdown(f"**[{item['index']}] {item['source']} ({item['location']})**")
            st.caption(item["snippet"])


def _parse_citations(citations: list[str]) -> list[dict]:
    parsed: list[dict] = []
    for entry in citations:
        match = re.match(r"^\[(\d+)\]\s*(.*)$", entry.strip(), re.S)
        if not match:
            continue
        idx = int(match.group(1))
        rest = match.group(2).strip()
        header, snippet = rest, ""
        if "\n" in rest:
            header, snippet = rest.split("\n", 1)
        header = header.strip()
        snippet = snippet.strip()
        source = header
        location = "-"
        if header.endswith(")") and " (" in header:
            source, location = header.rsplit(" (", 1)
            location = location[:-1]
        parsed.append(
            {
                "index": idx,
                "source": source,
                "location": location,
                "snippet": snippet,
            }
        )
    return sorted(parsed, key=lambda item: item["index"])


def render_citations_list(citations: list[str] | None, workspace_id: str | None) -> None:
    if not citations:
        st.caption(t("no_citations", workspace_id))
        return
    _render_citations_expander(_parse_citations(citations), workspace_id)


def citations_from_hits_json(hits_json: str | None) -> list[str]:
    if not hits_json:
        return []
    try:
        hits = json.loads(hits_json)
    except json.JSONDecodeError:
        return []
    citations: list[str] = []
    for idx, hit in enumerate(hits, start=1):
        citation = build_citation(
            filename=hit.get("filename") or "-",
            page_start=int(hit.get("page_start") or 0),
            page_end=int(hit.get("page_end") or 0),
            text=hit.get("text") or "",
            file_type=hit.get("file_type"),
        )
        citations.append(f"[{idx}] {citation.render()}")
    return citations


def bind_cmd_enter(*, button_label: str, key: str) -> None:
    label = html.escape(button_label)
    components.html(
        f"""
        <script>
        (function() {{
          const label = "{label}";
          window.__sf_shortcuts = window.__sf_shortcuts || {{}};
          if (window.__sf_shortcuts[label]) {{
            return;
          }}
          window.__sf_shortcuts[label] = true;
          document.addEventListener("keydown", function(event) {{
            if (!(event.metaKey || event.ctrlKey) || event.key !== "Enter") {{
              return;
            }}
            const active = document.activeElement;
            if (!active || (active.tagName !== "TEXTAREA" && active.tagName !== "INPUT")) {{
              return;
            }}
            const buttons = Array.from(window.parent.document.querySelectorAll("button"));
            const target = buttons.find((btn) => btn.innerText.trim() === label);
            if (target) {{
              event.preventDefault();
              target.click();
            }}
          }});
        }})();
        </script>
        """,
        height=0,
        key=key,
    )


def render_global_notifications(workspace_id: str | None) -> None:
    if not workspace_id:
        return
    _collect_task_notifications(workspace_id)
    notifications: list[dict] = st.session_state.get("notifications_queue", [])
    if not notifications:
        return

    visible = notifications[:3]
    for notice in visible:
        _render_notification_card(notice)

    overflow = notifications[3:]
    if overflow:
        with st.expander(t("notification_center", workspace_id), expanded=False):
            for notice in overflow:
                _render_notification_card(notice, compact=True)


def _render_notification_card(notice: dict, compact: bool = False) -> None:
    workspace_id = st.session_state.get("workspace_id")
    title = notice.get("title") or t("notification_task", workspace_id)
    status_label = t(f"task_status_{notice.get('status', 'queued')}", workspace_id)
    summary = notice.get("summary") or "-"
    completed_at = notice.get("completed_at") or "-"
    container = st.container()
    with container:
        st.markdown(f"**{title}** · {status_label}")
        st.caption(f"{summary}")
        st.caption(f"{t('completed_at', workspace_id)}: {completed_at}")
        cols = st.columns([1, 1, 6])
        if cols[0].button(
            t("notification_view", workspace_id),
            key=f"notif_view_{notice['id']}",
        ):
            _apply_notification_target(notice)
        if cols[1].button(
            t("notification_dismiss", workspace_id),
            key=f"notif_dismiss_{notice['id']}",
        ):
            _dismiss_notification(notice["id"])
        if not compact:
            st.divider()


def _dismiss_notification(notification_id: str) -> None:
    queue = st.session_state.get("notifications_queue", [])
    st.session_state["notifications_queue"] = [
        item for item in queue if item.get("id") != notification_id
    ]


def _apply_notification_target(notice: dict) -> None:
    target = notice.get("target") or {}
    nav = target.get("nav")
    if nav:
        st.session_state["active_nav"] = nav
    if target.get("tools_tab"):
        st.session_state["tools_tab"] = target["tools_tab"]
    if target.get("library_doc_id"):
        st.session_state["library_selected_doc"] = target["library_doc_id"]
    _dismiss_notification(notice.get("id", ""))
    st.rerun()


def _collect_task_notifications(workspace_id: str) -> None:
    status_cache = st.session_state.setdefault("task_status_cache", {})
    notifications = st.session_state.setdefault("notifications_queue", [])
    initialized = st.session_state.get("task_status_cache_initialized", False)
    tasks = list_tasks_for_workspace(workspace_id=workspace_id)
    for task in tasks:
        task_id = _task_attr(task, "id")
        status = _task_attr(task, "status")
        if not task_id or not status:
            continue
        prev_status = status_cache.get(task_id)
        status_cache[task_id] = status
        if not initialized:
            continue
        if status not in {"succeeded", "failed"}:
            continue
        if prev_status == status:
            continue
        payload = _task_payload(task)
        notice = _build_notification(task, payload)
        if notice:
            notifications.insert(0, notice)
            notifications[:] = notifications[:20]
    if not initialized:
        st.session_state["task_status_cache_initialized"] = True


def _build_notification(task, payload: dict) -> dict | None:
    workspace_id = st.session_state.get("workspace_id")
    task_type = _task_attr(task, "type") or "task"
    status = _task_attr(task, "status") or "succeeded"
    completed_at = (_task_attr(task, "updated_at") or "").replace("T", " ")[:16]
    title = t(f"task_type_{task_type}", workspace_id)
    summary = _task_summary(task_type, payload)
    target = _task_target(task_type, payload)
    return {
        "id": _task_attr(task, "id"),
        "task_type": task_type,
        "status": status,
        "completed_at": completed_at or "-",
        "title": title,
        "summary": summary,
        "target": target,
    }


def _task_summary(task_type: str, payload: dict) -> str:
    workspace_id = st.session_state.get("workspace_id")
    if task_type in {"ingest", "ingest_index"}:
        name = Path(payload.get("path", "")).name or t("unknown_file", workspace_id)
        return t("notification_ingest_summary", workspace_id).format(name=name)
    if task_type.startswith("generate_"):
        action = payload.get("action_type") or task_type.replace("generate_", "")
        label = t(f"task_action_{action}", workspace_id)
        return t("notification_generate_summary", workspace_id).format(name=label)
    if task_type == "ask":
        return t("notification_ask_summary", workspace_id)
    if task_type == "index":
        return t("notification_index_summary", workspace_id)
    return t("notification_generic_summary", workspace_id)


def _task_target(task_type: str, payload: dict) -> dict:
    if task_type in {"ingest", "ingest_index"}:
        doc_id = (payload.get("result") or {}).get("doc_id")
        return {"nav": "Library", "library_doc_id": doc_id}
    if task_type.startswith("generate_"):
        return {"nav": "Tools", "tools_tab": "recent_activity"}
    if task_type == "ask":
        return {"nav": "Tools", "tools_tab": "tasks"}
    if task_type == "index":
        return {"nav": "Tools", "tools_tab": "tasks"}
    return {"nav": "Tools", "tools_tab": "tasks"}


def _task_attr(task, name: str):
    if isinstance(task, dict):
        return task.get(name)
    return getattr(task, name, None)


def _task_payload(task) -> dict:
    payload_json = _task_attr(task, "payload_json")
    if not payload_json:
        return {}
    try:
        return json.loads(payload_json)
    except json.JSONDecodeError:
        return {}

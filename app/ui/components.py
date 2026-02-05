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


def render_help_link(topic: str = "") -> None:
    """Render a help link that navigates to the help center."""
    workspace_id = st.session_state.get("workspace_id")
    help_label = t("help_link_label", workspace_id)

    if st.button(
        f"❓ {help_label}",
        key=f"help_link_{topic or 'general'}",
        help=t("help_link_tooltip", workspace_id),
    ):
        st.session_state["active_nav"] = "Tools"
        st.session_state["tools_tab"] = "help"
        st.rerun()


def render_section_with_help(title: str, help_topic: str = "") -> None:
    """Render a section title with a help link in the same row."""
    workspace_id = st.session_state.get("workspace_id")
    help_label = t("help", workspace_id)

    col1, col2 = st.columns([6, 1])
    with col1:
        section_title(title)
    with col2:
        if st.button(
            "❓",
            key=f"section_help_{help_topic or title}",
            help=f"{help_label}: {title}",
        ):
            st.session_state["active_nav"] = "Tools"
            st.session_state["tools_tab"] = "help"
            # Push to navigation history
            from app.ui.layout import _push_nav_history
            _push_nav_history("Tools")
            st.rerun()


def render_back_button() -> bool:
    """Render a back button that navigates to the previous page.

    Returns True if the button was clicked and navigation occurred.
    """
    from app.ui.layout import can_go_back, navigate_back

    workspace_id = st.session_state.get("workspace_id")

    if not can_go_back():
        return False

    back_label = t("back_button", workspace_id)
    if st.button(f"← {back_label}", key="global_back_btn"):
        if navigate_back():
            st.rerun()
            return True
    return False


def muted(text: str) -> None:
    st.markdown(f"<span class='sf-muted'>{text}</span>", unsafe_allow_html=True)


def card_header(title: str, subtitle: str | None = None) -> None:
    st.markdown("<div class='sf-card'>", unsafe_allow_html=True)
    section_title(title)
    if subtitle:
        muted(subtitle)


def card_footer() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_content_box(content: str, title: str | None = None) -> None:
    """Render markdown content in a styled box with proper formatting."""
    if not content:
        return
    if title:
        st.markdown(f"**{title}**")
    # Wrap content in styled div and render as markdown
    st.markdown(
        f"<div class='sf-content-box'>{_md_to_html(content)}</div>",
        unsafe_allow_html=True,
    )


def _md_to_html(md_text: str) -> str:
    """Convert basic markdown to HTML for display."""
    import re

    # Escape HTML first
    text = html.escape(md_text)

    # Convert headers
    text = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', text, flags=re.MULTILINE)
    text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)

    # Convert bold and italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # Convert inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

    # Convert bullet lists
    lines = text.split('\n')
    result = []
    in_list = False
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f"<li>{line.strip()[2:]}</li>")
        elif line.strip().startswith('* '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f"<li>{line.strip()[2:]}</li>")
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if line.strip():
                # Check if line is already an HTML tag
                if not line.strip().startswith('<'):
                    result.append(f"<p>{line}</p>")
                else:
                    result.append(line)
            else:
                result.append('')
    if in_list:
        result.append('</ul>')

    return '\n'.join(result)


def render_empty_state(icon: str, title: str, description: str) -> None:
    """Render a centered empty state with icon, title and description."""
    st.markdown(
        f"""
        <div class='sf-empty-state'>
            <div class='sf-empty-icon'>{icon}</div>
            <div class='sf-empty-title'>{title}</div>
            <div class='sf-empty-desc'>{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header_card(title: str, subtitle: str | None = None) -> None:
    """Render a styled header card."""
    subtitle_html = f"<div class='sf-header-subtitle'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div class='sf-header-card'>
            <div class='sf-header-title'>{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_doc_card(filename: str, file_type: str | None, doc_type: str | None, size: int | None = None) -> None:
    """Render a document card for the library."""
    icon = "📄"
    if file_type == "pdf":
        icon = "📕"
    elif file_type in ("docx", "doc"):
        icon = "📘"
    elif file_type in ("pptx", "ppt"):
        icon = "📙"
    elif file_type in ("txt", "md"):
        icon = "📝"

    size_str = ""
    if size:
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"

    st.markdown(
        f"""
        <div class='sf-doc-card'>
            <div class='sf-doc-icon'>{icon}</div>
            <div class='sf-doc-info'>
                <div class='sf-doc-name'>{filename}</div>
                <div class='sf-doc-meta'>{file_type or '-'} · {size_str or '-'}</div>
            </div>
            <div class='sf-doc-type'>{doc_type or 'other'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    with st.expander(t("citations", workspace_id), expanded=True):
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


def render_doc_citations(citations: list[dict] | None, workspace_id: str | None) -> None:
    if not citations:
        st.caption(t("no_citations", workspace_id))
        return
    with st.expander(t("citations", workspace_id), expanded=True):
        for item in citations:
            st.markdown(f"**{item.get('title') or item.get('doc_id')}**")
            if item.get("snippet"):
                st.caption(item["snippet"])


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


def bind_cmd_enter(*, button_label: str, key: str | None = None) -> None:
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
    )


def render_global_notifications(workspace_id: str | None) -> None:
    """Render the notification center with task status and history."""
    if not workspace_id:
        return

    _collect_task_notifications(workspace_id)
    notifications: list[dict] = st.session_state.get("notifications_queue", [])

    # Deduplicate notifications by ID (keep first occurrence)
    seen_ids: set[str] = set()
    deduped_notifications: list[dict] = []
    for n in notifications:
        nid = n.get("id", "")
        if nid and nid not in seen_ids:
            seen_ids.add(nid)
            deduped_notifications.append(n)
        elif not nid:
            # No ID, still include but mark with unique ID
            import uuid
            n["id"] = f"temp_{uuid.uuid4().hex[:8]}"
            deduped_notifications.append(n)

    # Update session state with deduped list
    st.session_state["notifications_queue"] = deduped_notifications

    # Count running notifications from queue
    running_notifications = [n for n in deduped_notifications if n.get("status") == "running"]
    completed_notifications = [n for n in deduped_notifications if n.get("status") != "running"]

    # Check for running tasks from task service
    from service.tasks_service import list_tasks_for_workspace
    try:
        tasks = list_tasks_for_workspace(workspace_id=workspace_id)
        running_tasks = [
            t for t in tasks
            if (t["status"] if isinstance(t, dict) else t.status) in {"queued", "running"}
        ]
    except Exception:
        running_tasks = []

    # Calculate counts
    total_running = len(running_notifications) + len(running_tasks)
    notification_count = len(completed_notifications)

    # Build header with status indicators
    header_parts = ["🔔 " + t("notification_center", workspace_id)]
    if total_running > 0:
        header_parts.append(f"⏳ {total_running}")
    if notification_count > 0:
        header_parts.append(f"📬 {notification_count}")

    header_text = " · ".join(header_parts)

    # Show expanded if there are running tasks or new notifications
    should_expand = total_running > 0 or (notification_count > 0 and notification_count <= 3)

    with st.expander(header_text, expanded=should_expand):
        # Running section - from both notifications queue and task service
        has_running = total_running > 0

        if has_running:
            st.markdown(
                f"""
                <div style="
                    background: var(--warning-light);
                    border: 1px solid var(--warning-color);
                    border-radius: 8px;
                    padding: 10px 14px;
                    margin-bottom: 12px;
                ">
                    <div style="font-weight: 600; color: var(--warning-color); margin-bottom: 8px;">
                        ⏳ {t('running_tasks', workspace_id)} ({total_running})
                    </div>
                """,
                unsafe_allow_html=True,
            )

            # Show running notifications
            for notice in running_notifications:
                title = notice.get("title") or t("notification_task", workspace_id)
                st.markdown(f"<div style='color: var(--text-color); padding: 4px 0;'>• {title}</div>", unsafe_allow_html=True)

            # Show running tasks from service
            for task in running_tasks[:5]:
                task_type = task["type"] if isinstance(task, dict) else task.type
                progress = task["progress"] if isinstance(task, dict) else task.progress
                progress_val = progress if progress else 0
                task_label = t(f'task_type_{task_type}', workspace_id)
                st.markdown(f"<div style='color: var(--text-color); padding: 4px 0;'>• {task_label}</div>", unsafe_allow_html=True)
                if progress_val > 0:
                    st.progress(progress_val / 100 if progress_val <= 100 else 1.0)

            st.markdown("</div>", unsafe_allow_html=True)

        # Completed notifications section
        if not completed_notifications:
            if not has_running:
                st.caption(t("no_notifications", workspace_id))
        else:
            st.markdown(f"**{t('recent_notifications', workspace_id)}**")

            # Pagination
            page_key = "notification_page"
            page_size = 5
            total_pages = max(1, (len(completed_notifications) + page_size - 1) // page_size)
            current_page = st.session_state.get(page_key, 1)
            if current_page > total_pages:
                current_page = 1
                st.session_state[page_key] = current_page

            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, len(completed_notifications))
            visible = completed_notifications[start_idx:end_idx]

            for idx, notice in enumerate(visible):
                _render_notification_card(notice, compact=True, key_suffix=f"_{start_idx + idx}")

            # Pagination controls
            if total_pages > 1:
                cols = st.columns([1, 2, 1])
                if cols[0].button("◀", key="notif_prev", disabled=current_page <= 1):
                    st.session_state[page_key] = current_page - 1
                    st.rerun()
                cols[1].caption(f"{current_page} / {total_pages}")
                if cols[2].button("▶", key="notif_next", disabled=current_page >= total_pages):
                    st.session_state[page_key] = current_page + 1
                    st.rerun()

            # Clear all button
            if st.button(t("clear_all_notifications", workspace_id), key="btn_clear_all_notif", use_container_width=True):
                st.session_state["notifications_queue"] = []
                st.rerun()


def _render_notification_card(notice: dict, compact: bool = False, key_suffix: str = "") -> None:
    workspace_id = st.session_state.get("workspace_id")
    title = notice.get("title") or t("notification_task", workspace_id)
    status = notice.get("status", "queued")
    status_label = t(f"task_status_{status}", workspace_id)
    summary = notice.get("summary") or "-"
    completed_at = notice.get("completed_at") or "-"
    notice_id = notice.get("id", "unknown")

    # Status styling
    status_colors = {
        "running": ("⏳", "var(--warning-color)", "var(--warning-light)"),
        "succeeded": ("✅", "var(--success-color)", "var(--success-light)"),
        "failed": ("❌", "var(--error-color)", "var(--error-light)"),
        "queued": ("📋", "var(--muted-text)", "var(--surface-bg)"),
    }
    icon, color, bg = status_colors.get(status, status_colors["queued"])

    # Render card with HTML for better styling
    st.markdown(
        f"""
        <div style="
            background: {bg};
            border: 1px solid {color};
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
        ">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span>{icon}</span>
                <strong style="color: var(--text-color);">{title}</strong>
                <span style="color: {color}; font-size: 0.85rem;">· {status_label}</span>
            </div>
            <div style="font-size: 0.85rem; color: var(--muted-text); margin-bottom: 4px;">{summary}</div>
            <div style="font-size: 0.8rem; color: var(--muted-text);">{t('completed_at', workspace_id)}: {completed_at}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Buttons in horizontal layout - use unique key with suffix
    unique_key = f"{notice_id}{key_suffix}"
    btn_cols = st.columns([1, 1, 3])
    with btn_cols[0]:
        if st.button(
            t("notification_view", workspace_id),
            key=f"notif_view_{unique_key}",
            use_container_width=True,
        ):
            _apply_notification_target(notice)
    with btn_cols[1]:
        if st.button(
            t("notification_dismiss", workspace_id),
            key=f"notif_dismiss_{unique_key}",
            use_container_width=True,
        ):
            _dismiss_notification(notice["id"])
            st.rerun()


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
            try:
                st.toast(f"{notice.get('title')} · {notice.get('status')}")
            except Exception:
                pass
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
    if task_type == "index_assets":
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


def push_notification(
    *,
    workspace_id: str,
    task_type: str,
    title: str,
    status: str = "succeeded",
    summary: str | None = None,
    target: dict | None = None,
    task_id: str | None = None,
) -> None:
    """Manually push a notification to the notification queue.

    If task_id is provided, also updates the database task status.
    """
    import uuid
    from datetime import datetime

    # Update database task if task_id provided
    if task_id:
        from core.tasks.store import update_progress, update_status
        try:
            # Set progress to 100% on success, 0% on failure
            if status == "succeeded":
                update_progress(task_id, 100.0)
            update_status(task_id, status)
        except Exception:
            pass

    notifications = st.session_state.setdefault("notifications_queue", [])

    # Remove any existing notification with same task_id OR running notification with same task_type
    notifications[:] = [
        n for n in notifications
        if not (
            (task_id and n.get("id") == task_id) or
            (n.get("task_type") == task_type and n.get("status") == "running")
        )
    ]

    notice = {
        "id": task_id or str(uuid.uuid4()),
        "task_type": task_type,
        "status": status,
        "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title": title,
        "summary": summary or t("notification_generic_summary", workspace_id),
        "target": target or {"nav": "Tools", "tools_tab": "recent_activity"},
    }

    notifications.insert(0, notice)
    notifications[:] = notifications[:20]

    # Show toast notification
    try:
        status_icon = "✅" if status == "succeeded" else "❌" if status == "failed" else "📬"
        st.toast(f"{status_icon} {title}")
    except Exception:
        pass


def push_generation_start_notification(
    *,
    workspace_id: str,
    task_type: str,
    title: str,
    create_db_task: bool = True,
) -> str:
    """Push a notification when generation starts. Returns the task ID.

    Also creates a database task entry so it shows in the Task Center.
    """
    import uuid
    from datetime import datetime

    # Create database task if requested
    task_id = None
    if create_db_task:
        from core.tasks.store import create_task, update_status
        try:
            task_id = create_task(
                workspace_id=workspace_id,
                type=task_type,
                payload={"title": title},
            )
            # Mark as running immediately
            update_status(task_id, "running")
        except Exception:
            pass  # Fallback to notification-only mode

    notifications = st.session_state.setdefault("notifications_queue", [])

    # Remove any existing running notification for the same task_type to prevent duplicates
    notifications[:] = [
        n for n in notifications
        if not (n.get("task_type") == task_type and n.get("status") == "running")
    ]

    notif_id = task_id or f"gen_{task_type}_{uuid.uuid4().hex[:8]}"

    notice = {
        "id": notif_id,
        "task_type": task_type,
        "status": "running",
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "completed_at": "-",
        "title": title,
        "summary": t("task_status_running", workspace_id),
        "target": {"nav": "Tools", "tools_tab": "tasks"},
    }

    notifications.insert(0, notice)
    notifications[:] = notifications[:20]

    # Show toast notification
    try:
        st.toast(f"⏳ {title} {t('task_status_running', workspace_id)}")
    except Exception:
        pass

    return notif_id


def update_notification_status(
    *,
    notification_id: str,
    status: str,
    summary: str = "",
    target: dict | None = None,
) -> None:
    """Update an existing notification's status."""
    from datetime import datetime

    notifications = st.session_state.get("notifications_queue", [])

    for notice in notifications:
        if notice.get("id") == notification_id:
            notice["status"] = status
            notice["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            if summary:
                notice["summary"] = summary
            if target:
                notice["target"] = target
            break

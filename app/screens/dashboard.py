from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

from app.ui.components import render_empty_state, render_header_card, render_section_with_help, section_title
from app.ui.labels import L
from app.ui.locks import running_task_summary
from core.domains.timetable import create_event, list_events
from core.domains.todo import create_todo, list_todos, update_todo_status
from core.domains.course import list_courses, list_schedules
from core.domains.research import list_projects
from core.ui_state.guards import llm_ready
from service.recent_activity_service import list_recent_activity
from service.retrieval_service import index_status


def _get_today_weekday() -> str:
    """Get today's weekday in Chinese format."""
    weekday_map = {
        0: "周一",
        1: "周二",
        2: "周三",
        3: "周四",
        4: "周五",
        5: "周六",
        6: "周日",
    }
    return weekday_map[datetime.now().weekday()]


def _get_course_schedules_for_today(courses: list[dict]) -> list[dict]:
    """Get all course schedules that match today's weekday."""
    today_weekday = _get_today_weekday()
    today_weekday_en = {
        "周一": "monday",
        "周二": "tuesday",
        "周三": "wednesday",
        "周四": "thursday",
        "周五": "friday",
        "周六": "saturday",
        "周日": "sunday",
    }[today_weekday].lower()
    
    result = []
    for course in courses:
        schedules = list_schedules(course["id"])
        for sched in schedules:
            weekday = (sched.get("weekday") or "").lower()
            # Match both Chinese and English weekday names
            if today_weekday in weekday or today_weekday_en in weekday:
                result.append({
                    "course_name": course["name"],
                    "course_id": course["id"],
                    "start_time": sched.get("start_time") or "00:00",
                    "end_time": sched.get("end_time") or "00:00",
                    "location": sched.get("location"),
                })
    
    # Sort by start time
    result.sort(key=lambda x: x["start_time"])
    return result


def _today_range() -> tuple[str, str]:
    now = datetime.now().astimezone()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _render_stat_card(icon: str, value: str | int, label: str, color: str = "primary") -> None:
    """Render a styled stat card."""
    color_map = {
        "primary": "var(--primary-color)",
        "success": "var(--success-color)",
        "warning": "var(--warning-color)",
        "error": "var(--error-color)",
    }
    accent = color_map.get(color, color_map["primary"])
    st.markdown(
        f"""
        <div style="
            background: var(--card-bg);
            border: 1.5px solid var(--card-border);
            border-radius: var(--radius-lg);
            padding: var(--space-lg);
            text-align: center;
            transition: all 0.2s ease;
        ">
            <div style="font-size: 2rem; margin-bottom: 8px;">{icon}</div>
            <div style="font-size: 1.75rem; font-weight: 700; color: {accent}; line-height: 1;">{value}</div>
            <div style="font-size: 0.85rem; color: var(--muted-text); margin-top: 6px;">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(*, main_col, inspector_col, workspace_id: str | None) -> None:
    with main_col:
        render_section_with_help(L("仪表盘", "Dashboard"), "dashboard")
        
        if not workspace_id:
            render_empty_state(
                "📊",
                L("请选择工作区", "Select a Workspace"),
                L("在侧边栏选择或创建工作区以查看仪表盘。", "Select or create a workspace in the sidebar to view the dashboard."),
            )
            return

        locked, lock_msg = running_task_summary(workspace_id)
        if locked:
            st.warning(L("⏳ 正在处理任务，请等待...", "⏳ Processing task, please wait..."))

        # Today's date header with greeting
        hour = datetime.now().hour
        if hour < 12:
            greeting = L("早上好", "Good morning")
        elif hour < 18:
            greeting = L("下午好", "Good afternoon")
        else:
            greeting = L("晚上好", "Good evening")
        
        today_str = datetime.now().strftime("%Y年%m月%d日" if L("", "") == "" else "%B %d, %Y")
        weekday = datetime.now().strftime("%A")
        render_header_card(
            f"{greeting} 👋",
            f"{today_str} · {weekday}",
        )

        # Setup status alerts
        status = index_status(workspace_id)
        doc_count = status.get("doc_count", 0)  # Fix: use correct key
        
        # Load LLM settings from storage if not in session state
        from core.ui_state.storage import get_setting
        llm_base_url = st.session_state.get("llm_base_url") or get_setting(workspace_id, "llm_base_url") or ""
        llm_model = st.session_state.get("llm_model") or get_setting(workspace_id, "llm_model") or ""
        llm_api_key = st.session_state.get("llm_api_key") or get_setting(workspace_id, "llm_api_key") or ""
        
        llm_ok, reason = llm_ready(llm_base_url, llm_model, llm_api_key)
        
        # Status alerts in a collapsible section
        alerts = []
        if not llm_ok:
            alerts.append(("warning", reason or L('LLM 未配置，请在设置中配置。', 'LLM not configured. Please configure in Settings.')))
        if doc_count == 0:
            alerts.append(("info", L('尚未导入文档。请在「资料库」页面导入文档开始使用。', 'No documents yet. Import documents in the Library page to get started.')))
        
        if alerts:
            with st.container():
                for alert_type, message in alerts:
                    if alert_type == "warning":
                        st.warning(f"⚠️ {message}")
                    elif alert_type == "info":
                        st.info(f"💡 {message}")

        # Quick stats row
        st.markdown(f"### 📊 {L('快速概览', 'Quick Overview')}")
        
        courses = list_courses(workspace_id)
        projects = list_projects(workspace_id)
        todos = list_todos(workspace_id=workspace_id)
        pending_todos = [t for t in todos if t.get("status") != "done"]
        
        stat_cols = st.columns(4)
        with stat_cols[0]:
            _render_stat_card("📚", len(courses), L("课程", "Courses"), "primary")
        with stat_cols[1]:
            _render_stat_card("🔬", len(projects), L("项目", "Projects"), "success")
        with stat_cols[2]:
            _render_stat_card("📄", doc_count, L("文档", "Documents"), "warning")
        with stat_cols[3]:
            _render_stat_card("✅", len(pending_todos), L("待办", "Pending"), "error" if len(pending_todos) > 5 else "primary")
        
        st.markdown("")  # Spacing

        # Today's Schedule Section (Course schedules + custom events)
        st.markdown(f"### 📅 {L('今日课表与日程', 'Today Timetable & Schedule')}")
        
        # Get course schedules for today
        course_schedules = _get_course_schedules_for_today(courses)
        
        # Get custom events
        start, end = _today_range()
        events = list_events(workspace_id=workspace_id, start_at=start, end_at=end)
        
        has_any_schedule = bool(course_schedules) or bool(events)
        
        if not has_any_schedule:
            st.markdown(
                f"""
                <div style="
                    background: var(--surface-bg);
                    border-radius: var(--radius-md);
                    padding: var(--space-lg);
                    text-align: center;
                    color: var(--muted-text);
                ">
                    <div style="font-size: 2rem; opacity: 0.5; margin-bottom: 8px;">📅</div>
                    <div>{L("今天没有安排的日程", "No scheduled events today")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Show course schedules first (from course_schedule table)
            if course_schedules:
                st.markdown(f"**{L('今日课程', 'Today Classes')}** ({_get_today_weekday()})")
                for sched in course_schedules:
                    time_str = f"{sched['start_time']} - {sched['end_time']}"
                    location_str = f" · 📍 {sched['location']}" if sched.get("location") else ""
                    st.markdown(
                        f"""
                        <div class="sf-list-item" style="background: var(--primary-light); border: 1px solid var(--primary-color); border-radius: var(--radius-md); margin-bottom: 8px;">
                            <div class="sf-list-item-icon">📚</div>
                            <div class="sf-list-item-content">
                                <div class="sf-list-item-title">{sched['course_name']}</div>
                                <div class="sf-list-item-desc">{time_str}{location_str}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            
            # Show custom events
            if events:
                if course_schedules:
                    st.markdown(f"**{L('其他日程', 'Other Events')}**")
                for event in events:
                    time_str = f"{event['start_at'][11:16]} - {event['end_at'][11:16]}"
                    location_str = f" · 📍 {event['location']}" if event.get("location") else ""
                    st.markdown(
                        f"""
                        <div class="sf-list-item" style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); margin-bottom: 8px;">
                            <div class="sf-list-item-icon">🕐</div>
                            <div class="sf-list-item-content">
                                <div class="sf-list-item-title">{event['title']}</div>
                                <div class="sf-list-item-desc">{time_str}{location_str}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        with st.expander(L("➕ 添加日程", "➕ Add Event"), expanded=False):
            title = st.text_input(
                L("标题", "Title"),
                key="event_title",
                placeholder=L("例如：机器学习课程", "e.g. Machine Learning Class"),
            )
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.text_input(
                    L("开始时间", "Start"),
                    key="event_start",
                    placeholder="2026-02-05 09:00",
                )
            with col2:
                end_time = st.text_input(
                    L("结束时间", "End"),
                    key="event_end",
                    placeholder="2026-02-05 10:30",
                )
            location = st.text_input(L("地点", "Location"), key="event_location", placeholder=L("可选", "Optional"))
            
            if courses:
                course_map = {course["name"]: course for course in courses}
                selected_course = st.selectbox(
                    L("关联课程", "Link to Course"),
                    options=["-"] + list(course_map.keys()),
                    key="event_linked_course",
                )
                linked_course_id = course_map[selected_course]["id"] if selected_course != "-" else None
            else:
                linked_course_id = None
            
            if st.button(L("添加", "Add"), disabled=locked or not title.strip(), key="btn_add_event", type="primary"):
                create_event(
                    workspace_id=workspace_id,
                    title=title.strip(),
                    start_at=start_time.strip(),
                    end_at=end_time.strip(),
                    location=location.strip() or None,
                    linked_course_id=linked_course_id,
                    linked_todo_id=None,
                    kind="course" if linked_course_id else "custom",
                )
                st.success(L("✓ 日程已添加", "✓ Event added"))
                st.rerun()

        st.divider()

        # Today's Todos Section
        st.markdown(f"### ✅ {L('今日待办', 'Today Todos')}")
        
        today = datetime.now().date().isoformat()
        today_todos = [
            todo
            for todo in todos
            if not todo.get("due_at") or str(todo["due_at"]).startswith(today)
        ]
        
        if not today_todos:
            st.markdown(
                f"""
                <div style="
                    background: var(--surface-bg);
                    border-radius: var(--radius-md);
                    padding: var(--space-lg);
                    text-align: center;
                    color: var(--muted-text);
                ">
                    <div style="font-size: 2rem; opacity: 0.5; margin-bottom: 8px;">✨</div>
                    <div>{L("太棒了！今天没有待办事项", "Great! No todos for today")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for todo in today_todos:
                col1, col2 = st.columns([0.5, 5])
                with col1:
                    checked = st.checkbox(
                        "",
                        value=todo["status"] == "done",
                        key=f"todo_{todo['id']}",
                        label_visibility="collapsed",
                    )
                with col2:
                    if todo["status"] == "done":
                        st.markdown(f"<span style='text-decoration: line-through; color: var(--muted-text);'>{todo['title']}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color: var(--text-color);'>{todo['title']}</span>", unsafe_allow_html=True)
                
                if checked and todo["status"] != "done":
                    update_todo_status(todo_id=todo["id"], status="done")
                    st.rerun()
                if not checked and todo["status"] == "done":
                    update_todo_status(todo_id=todo["id"], status="todo")
                    st.rerun()

        with st.expander(L("➕ 添加待办", "➕ Add Todo"), expanded=False):
            title = st.text_input(
                L("待办内容", "Todo"),
                key="todo_title",
                placeholder=L("例如：完成作业第一部分", "e.g. Complete assignment part 1"),
            )
            due_at = st.text_input(
                L("截止日期", "Due Date"),
                key="todo_due",
                placeholder="2026-02-10",
            )
            
            course_id = None
            project_id = None
            
            col1, col2 = st.columns(2)
            with col1:
                if courses:
                    course_map = {course["name"]: course for course in courses}
                    selected_course = st.selectbox(
                        L("关联课程", "Link to Course"),
                        options=["-"] + list(course_map.keys()),
                        key="todo_linked_course",
                    )
                    course_id = course_map[selected_course]["id"] if selected_course != "-" else None
            with col2:
                if projects:
                    project_map = {project["title"]: project for project in projects}
                    selected_project = st.selectbox(
                        L("关联项目", "Link to Project"),
                        options=["-"] + list(project_map.keys()),
                        key="todo_linked_project",
                    )
                    project_id = project_map[selected_project]["id"] if selected_project != "-" else None
            
            if st.button(L("添加", "Add"), disabled=locked or not title.strip(), key="btn_add_todo", type="primary"):
                create_todo(
                    workspace_id=workspace_id,
                    title=title.strip(),
                    due_at=due_at.strip() or None,
                    status="todo",
                    linked_course_id=course_id,
                    linked_project_id=project_id,
                )
                st.success(L("✓ 待办已添加", "✓ Todo added"))
                st.rerun()

        st.divider()

        # Recent Activity
        st.markdown(f"### 📋 {L('最近活动', 'Recent Activity')}")
        
        activity = list_recent_activity(workspace_id, limit=10)
        
        if not activity:
            st.markdown(
                f"""
                <div style="
                    background: var(--surface-bg);
                    border-radius: var(--radius-md);
                    padding: var(--space-xl);
                    text-align: center;
                    color: var(--muted-text);
                ">
                    <div style="font-size: 2rem; opacity: 0.5; margin-bottom: 8px;">📋</div>
                    <div>{L("暂无活动记录", "No recent activity")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for item in activity:
                status_icon = {
                    "succeeded": "✅",
                    "failed": "❌",
                    "running": "⏳",
                    "queued": "📋",
                }.get(item.get("status", ""), "📄")
                
                status_color = {
                    "succeeded": "var(--success-color)",
                    "failed": "var(--error-color)",
                    "running": "var(--warning-color)",
                    "queued": "var(--muted-text)",
                }.get(item.get("status", ""), "var(--muted-text)")
                
                time_str = item['created_at'][:16].replace("T", " ")
                
                st.markdown(
                    f"""
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        padding: 10px 14px;
                        border-radius: var(--radius-md);
                        margin-bottom: 6px;
                        background: var(--card-bg);
                        border: 1px solid var(--card-border);
                    ">
                        <span style="font-size: 1.25rem;">{status_icon}</span>
                        <div style="flex: 1;">
                            <div style="font-weight: 500; color: var(--text-color);">{item.get('title') or item['type']}</div>
                        </div>
                        <span style="font-size: 0.8rem; color: var(--muted-text);">{time_str}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with inspector_col:
        st.markdown(f"### {L('系统状态', 'System Status')}")
        
        if workspace_id:
            # System health indicator
            health_ok = llm_ok and doc_count > 0
            health_icon = "🟢" if health_ok else "🟡" if llm_ok else "🔴"
            health_text = L("系统就绪", "System Ready") if health_ok else L("需要配置", "Setup Required") if not llm_ok else L("需要文档", "Documents Needed")
            
            st.markdown(
                f"""
                <div style="
                    background: var(--surface-bg);
                    border-radius: var(--radius-md);
                    padding: var(--space-md);
                    text-align: center;
                    margin-bottom: var(--space-md);
                ">
                    <span style="font-size: 1.5rem;">{health_icon}</span>
                    <span style="margin-left: 8px; font-weight: 500; color: var(--text-color);">{health_text}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Stats grid
            st.markdown(f"#### {L('索引统计', 'Index Stats')}")
            col1, col2 = st.columns(2)
            col1.metric(L("文档", "Docs"), doc_count)
            col2.metric(L("切块", "Chunks"), status.get("chunk_count", 0))
            
            col1, col2 = st.columns(2)
            col1.metric(L("向量", "Vectors"), status.get("vector_count", 0))
            bm25_status = L("就绪", "Ready") if status.get("bm25_exists") else L("缺失", "N/A")
            col2.metric(L("BM25", "BM25"), bm25_status)
            
            st.markdown("")  # Spacing
            
            # LLM status card
            st.markdown(f"#### {L('LLM 状态', 'LLM Status')}")
            if llm_ok:
                model_name = llm_model[:20] + "..." if len(llm_model) > 20 else llm_model
                st.markdown(
                    f"""
                    <div style="
                        background: var(--success-light);
                        border: 1px solid var(--success-color);
                        border-radius: var(--radius-md);
                        padding: var(--space-md);
                    ">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span>✓</span>
                            <span style="font-weight: 500; color: var(--success-color);">{L("已配置", "Configured")}</span>
                        </div>
                        <div style="font-size: 0.85rem; color: var(--muted-text); margin-top: 4px;">{model_name}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="
                        background: var(--error-light);
                        border: 1px solid var(--error-color);
                        border-radius: var(--radius-md);
                        padding: var(--space-md);
                    ">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span>✗</span>
                            <span style="font-weight: 500; color: var(--error-color);">{L("未配置", "Not Configured")}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown("")
                if st.button(L("前往设置", "Go to Settings"), key="btn_goto_settings", type="primary", use_container_width=True):
                    st.session_state["active_nav"] = "Settings"
                    st.rerun()
            
            st.markdown("")  # Spacing
            
            # Quick actions
            st.markdown(f"#### {L('快速操作', 'Quick Actions')}")
            if st.button(L("📚 导入文档", "📚 Import Documents"), key="btn_quick_import", use_container_width=True):
                st.session_state["active_nav"] = "Library"
                st.rerun()
            if st.button(L("📖 管理课程", "📖 Manage Courses"), key="btn_quick_courses", use_container_width=True):
                st.session_state["active_nav"] = "Courses"
                st.rerun()
            if st.button(L("⚙️ 系统设置", "⚙️ Settings"), key="btn_quick_settings", use_container_width=True):
                st.session_state["active_nav"] = "Settings"
                st.rerun()

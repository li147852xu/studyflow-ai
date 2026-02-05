from __future__ import annotations

import streamlit as st

from app.components.diagnostics_center import render_diagnostics_center
from app.components.exports_center import render_exports_center
from app.components.help_center import render_help_center
from app.components.tasks_center import render_tasks_center
from app.ui.components import render_content_box, render_empty_state, render_section_with_help, section_title
from app.ui.labels import L
from core.domains.course import list_courses
from core.domains.research import list_projects
from core.rag import map_reduce_course_query, map_reduce_project_query
from core.ui_state.storage import get_setting
from service.recent_activity_service import list_recent_activity
from service.research_v3_service import generate_deck


def render_tools(*, main_col, inspector_col, workspace_id: str | None) -> None:
    with main_col:
        render_section_with_help(L("工具箱", "Toolbox"), "tools")
        
        if not workspace_id:
            render_empty_state(
                "🧰",
                L("请选择工作区", "Select a Workspace"),
                L("在侧边栏选择或创建工作区以使用工具。", "Select or create a workspace in the sidebar to use tools."),
            )
            return
        
        tabs = st.tabs([
            f"📋 {L('任务', 'Tasks')}",
            f"🔧 {L('诊断', 'Diagnostics')}",
            f"📜 {L('活动', 'Activity')}",
            f"📦 {L('导出', 'Exports')}",
            f"📊 {L('汇报', 'Decks')}",
            f"❓ {L('帮助', 'Help')}",
        ])
        
        # Tasks tab
        with tabs[0]:
            st.markdown(f"#### 📋 {L('任务中心', 'Task Center')}")
            st.caption(L("查看和管理后台任务。", "View and manage background tasks."))
            render_tasks_center(workspace_id=workspace_id)
        
        # Diagnostics tab
        with tabs[1]:
            st.markdown(f"#### 🔧 {L('系统诊断', 'System Diagnostics')}")
            st.caption(L("健康检查、索引维护和清理工具。", "Health checks, index maintenance, and cleanup tools."))
            render_diagnostics_center(workspace_id=workspace_id)
        
        # Recent Activity tab
        with tabs[2]:
            st.markdown(f"#### 📜 {L('最近活动', 'Recent Activity')}")
            st.caption(L("最近 30 条操作记录。", "Last 30 operation records."))
            
            activity = list_recent_activity(workspace_id)
            
            if not activity:
                render_empty_state(
                    "📜",
                    L("暂无活动记录", "No Activity Records"),
                    L("操作后会在此显示记录。", "Records will appear here after operations."),
                )
            else:
                for item in activity:
                    status_icon = {
                        "succeeded": "✅",
                        "failed": "❌",
                        "running": "⏳",
                        "queued": "📋",
                    }.get(item.get("status", ""), "📄")
                    
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        st.caption(item['created_at'][:16].replace("T", " "))
                    with col2:
                        st.write(f"{status_icon} {item.get('title') or item['type']}")
                    with col3:
                        if item.get("status"):
                            st.caption(item["status"])
        
        # Exports tab
        with tabs[3]:
            st.markdown(f"#### 📦 {L('导出中心', 'Export Center')}")
            st.caption(L("导出工作区数据或生成提交包。", "Export workspace data or build submission packs."))
            render_exports_center(workspace_id=workspace_id)
        
        # Decks tab
        with tabs[4]:
            st.markdown(f"#### 📊 {L('汇报生成器', 'Deck Generator')}")
            st.caption(L("基于课程或项目生成演示汇报。", "Generate presentation decks from courses or projects."))
            
            scope = st.selectbox(
                L("范围", "Scope"),
                options=["course", "project", "mixed"],
                format_func=lambda value: {
                    "course": f"📚 {L('课程', 'Course')}",
                    "project": f"🔬 {L('科研', 'Project')}",
                    "mixed": f"🔀 {L('混合', 'Mixed')}",
                }.get(value, value),
                key="tools_deck_scope",
            )
            
            map_tokens = int(get_setting(workspace_id, "rag_map_tokens") or 250)
            reduce_tokens = int(get_setting(workspace_id, "rag_reduce_tokens") or 600)
            source_ids: list[str] = []
            coverage = None
            
            col1, col2 = st.columns(2)
            
            with col1:
                if scope in {"course", "mixed"}:
                    courses = list_courses(workspace_id)
                    course_map = {course["name"]: course for course in courses}
                    if course_map:
                        course_name = st.selectbox(
                            L("选择课程", "Select Course"),
                            options=list(course_map.keys()),
                            key="tools_deck_course",
                        )
                        source_ids.append(course_map[course_name]["id"])
                    else:
                        st.info(L("暂无课程。", "No courses available."))
            
            with col2:
                if scope in {"project", "mixed"}:
                    projects = list_projects(workspace_id)
                    project_map = {proj["title"]: proj for proj in projects}
                    if project_map:
                        project_name = st.selectbox(
                            L("选择项目", "Select Project"),
                            options=list(project_map.keys()),
                            key="tools_deck_project",
                        )
                        source_ids.append(project_map[project_name]["id"])
                    else:
                        st.info(L("暂无项目。", "No projects available."))
            
            duration = st.slider(L("时长（分钟）", "Duration (min)"), min_value=5, max_value=30, value=10, key="tools_deck_duration")
            
            if st.button(L("🚀 生成汇报", "🚀 Generate Deck"), key="btn_tools_gen_deck", type="primary", disabled=not source_ids):
                # Calculate coverage first
                if scope in {"course", "mixed"} and course_map:
                    coverage = map_reduce_course_query(
                        workspace_id=workspace_id,
                        course_id=course_map[course_name]["id"],
                        query="Course deck coverage",
                        map_tokens=map_tokens,
                        reduce_tokens=reduce_tokens,
                    ).coverage
                elif scope in {"project", "mixed"} and project_map:
                    coverage = map_reduce_project_query(
                        workspace_id=workspace_id,
                        project_id=project_map[project_name]["id"],
                        query="Project deck coverage",
                        map_tokens=map_tokens,
                        reduce_tokens=reduce_tokens,
                    ).coverage
                
                deck = generate_deck(
                    workspace_id=workspace_id,
                    source_kind=scope,
                    source_ids=source_ids,
                    duration=duration,
                    coverage=coverage,
                )
                
                st.markdown(f"**{L('生成的汇报', 'Generated Deck')} (Marp)**")
                render_content_box(deck["content"])
                
                if coverage:
                    with st.expander(L("📊 覆盖率报告", "📊 Coverage Report"), expanded=False):
                        col1, col2, col3 = st.columns(3)
                        col1.metric(L("已包含", "Included"), coverage.get("included_docs", 0))
                        col2.metric(L("缺失", "Missing"), len(coverage.get("missing_docs", [])))
                        col3.metric(L("总数", "Total"), coverage.get("total_docs", 0))
        
        # Help tab
        with tabs[5]:
            st.markdown(f"#### ❓ {L('帮助中心', 'Help Center')}")
            st.caption(L("使用指南和常见问题解答。", "User guide and FAQs."))
            render_help_center(workspace_id=workspace_id)

    with inspector_col:
        st.markdown(f"### {L('快速操作', 'Quick Actions')}")
        
        if st.button(L("🔄 刷新任务状态", "🔄 Refresh Task Status"), key="btn_refresh_tasks"):
            st.rerun()
        
        if st.button(L("🧹 清理缓存", "🧹 Clear Cache"), key="btn_clear_cache"):
            st.info(L("请在「诊断」标签页中执行清理。", "Please use the Diagnostics tab for cleanup."))
        
        st.divider()
        st.markdown(f"### {L('提示', 'Tips')}")
        st.caption(L(
            "• 任务会在后台自动执行\n"
            "• 可以切换页面而不影响任务\n"
            "• 定期运行诊断保持系统健康",
            "• Tasks run automatically in background\n"
            "• You can switch pages without affecting tasks\n"
            "• Run diagnostics regularly for system health",
        ))

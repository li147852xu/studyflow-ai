from __future__ import annotations

import streamlit as st

from app.ui.components import (
    render_answer_with_citations,
    render_content_box,
    render_doc_citations,
    render_empty_state,
    render_header_card,
    render_section_with_help,
    section_title,
)
from app.ui.labels import L
from app.ui.locks import running_task_summary
from core.domains.course import list_courses
from core.domains.research import list_projects, list_project_papers
from core.rag import classify_query, map_reduce_course_query, map_reduce_project_query
from core.ui_state.storage import get_setting
from service.course_v3_service import course_docs_for_qa
from service.rag_service import course_query, project_query


def render_assistant(*, main_col, inspector_col, workspace_id: str | None) -> None:
    with main_col:
        render_section_with_help(L("AI 助手", "AI Assistant"), "assistant")
        
        if not workspace_id:
            render_empty_state(
                "🤖",
                L("请选择工作区", "Select a Workspace"),
                L("在侧边栏选择或创建工作区以使用 AI 助手。", "Select or create a workspace in the sidebar to use AI Assistant."),
            )
            return

        locked, _ = running_task_summary(workspace_id)
        if locked:
            st.warning(L("⏳ 正在处理任务，请等待...", "⏳ Processing task, please wait..."))

        render_header_card(
            L("智能问答助手", "Smart Q&A Assistant"),
            L("基于你的资料进行精准回答，支持课程和科研范围限定", "Precise answers based on your materials with course and research scope filtering"),
        )

        # Scope selection
        st.markdown(f"#### 🎯 {L('选择范围', 'Select Scope')}")
        st.caption(L("限定范围可以获得更精准的回答。", "Limiting scope provides more accurate answers."))
        
        scope = st.selectbox(
            L("回答范围", "Answer Scope"),
            options=["course", "project", "mixed"],
            format_func=lambda value: {
                "course": f"📚 {L('仅课程', 'Course Only')}",
                "project": f"🔬 {L('仅科研', 'Research Only')}",
                "mixed": f"🔀 {L('混合范围', 'Mixed Scope')}",
            }.get(value, value),
            key="assistant_scope_select",
        )
        
        course = None
        project = None
        
        col1, col2 = st.columns(2)
        
        with col1:
            if scope in {"course", "mixed"}:
                courses = list_courses(workspace_id)
                course_map = {c["name"]: c for c in courses}
                if course_map:
                    course_name = st.selectbox(
                        L("选择课程", "Select Course"),
                        options=list(course_map.keys()),
                        key="assistant_course_select",
                    )
                    course = course_map[course_name]
                else:
                    st.info(L("暂无课程。请先在「课程」页面创建。", "No courses. Create one in the Courses page first."))
        
        with col2:
            if scope in {"project", "mixed"}:
                projects = list_projects(workspace_id)
                proj_map = {p["title"]: p for p in projects}
                if proj_map:
                    project_name = st.selectbox(
                        L("选择项目", "Select Project"),
                        options=list(proj_map.keys()),
                        key="assistant_project_select",
                    )
                    project = proj_map[project_name]
                else:
                    st.info(L("暂无项目。请先在「科研」页面创建。", "No projects. Create one in the Research page first."))

        st.divider()

        # Question input
        st.markdown(f"#### 💬 {L('提问', 'Ask a Question')}")
        
        question = st.text_area(
            L("你的问题", "Your Question"),
            key="assistant_question",
            placeholder=L(
                "例如：这门课的主要知识点有哪些？最近的研究进展如何？",
                "e.g. What are the key concepts in this course? What are recent research advances?",
            ),
            height=100,
        )
        
        # Advanced settings
        with st.expander(L("⚙️ 高级设置", "⚙️ Advanced Settings"), expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                map_tokens = st.number_input(
                    L("Map Token 预算", "Map Token Budget"),
                    min_value=100,
                    max_value=1000,
                    value=int(get_setting(workspace_id, "rag_map_tokens") or 250),
                    help=L("每个文档的 token 预算。", "Token budget per document."),
                    key="rag_map_tokens_input",
                )
            with col2:
                reduce_tokens = st.number_input(
                    L("Reduce Token 预算", "Reduce Token Budget"),
                    min_value=200,
                    max_value=2000,
                    value=int(get_setting(workspace_id, "rag_reduce_tokens") or 600),
                    help=L("最终汇总的 token 预算。", "Token budget for final summary."),
                    key="rag_reduce_tokens_input",
                )

        # Ask button
        can_ask = question.strip() and not locked
        if scope == "course" and not course:
            can_ask = False
        if scope == "project" and not project:
            can_ask = False
        if scope == "mixed" and not (course or project):
            can_ask = False

        if st.button(L("🚀 提问", "🚀 Ask"), disabled=not can_ask, key="btn_assistant_ask", type="primary"):
            _handle_question(
                workspace_id=workspace_id,
                scope=scope,
                course=course,
                project=project,
                question=question,
                map_tokens=map_tokens,
                reduce_tokens=reduce_tokens,
            )

        # Coverage action buttons
        st.divider()
        st.markdown(f"#### 🔧 {L('覆盖率工具', 'Coverage Tools')}")
        st.caption(L("如果回答不完整，可以尝试以下操作。", "If answers are incomplete, try these actions."))
        
        cols = st.columns(3)
        with cols[0]:
            if st.button(L("📥 导入缺失", "📥 Import Missing"), key="assistant_import_missing"):
                st.session_state["active_nav"] = "Library"
                st.rerun()
        with cols[1]:
            if st.button(L("🔄 重建索引", "🔄 Rebuild Index"), key="assistant_rebuild_index"):
                st.session_state["active_nav"] = "Tools"
                st.rerun()
        with cols[2]:
            if st.button(L("🔍 扩展范围", "🔍 Expand Scope"), key="assistant_expand_scope"):
                st.info(L("切换到「混合范围」可以扩展搜索。", "Switch to 'Mixed Scope' to expand search."))

    with inspector_col:
        st.markdown(f"### {L('当前范围', 'Current Scope')}")
        
        scope_labels = {
            "course": L("课程范围", "Course Scope"),
            "project": L("科研范围", "Research Scope"),
            "mixed": L("混合范围", "Mixed Scope"),
        }
        st.markdown(f"**{scope_labels.get(scope, scope)}**")
        
        if course:
            st.markdown(f"📚 {course['name']}")
        if project:
            st.markdown(f"🔬 {project['title']}")
        
        st.divider()
        st.markdown(f"### {L('使用提示', 'Tips')}")
        st.caption(L(
            "• 选择具体范围可以获得更精准的答案\n"
            "• 全局问题会触发 Map-Reduce 流程\n"
            "• 查看覆盖率报告了解回答的完整性",
            "• Select specific scope for accurate answers\n"
            "• Global questions trigger Map-Reduce flow\n"
            "• Check coverage report for answer completeness",
        ))


def _handle_question(
    workspace_id: str,
    scope: str,
    course: dict | None,
    project: dict | None,
    question: str,
    map_tokens: int,
    reduce_tokens: int,
) -> None:
    """Handle the question and display results."""
    query_type = classify_query(question)
    
    st.markdown(f"### {L('回答', 'Answer')}")
    
    if scope == "course" and course:
        result = course_query(
            workspace_id=workspace_id,
            course_id=course["id"],
            query=question,
            doc_ids=course_docs_for_qa(course["id"]),
        )
        _display_result(result, workspace_id)
        
    elif scope == "project" and project:
        doc_ids = [paper["doc_id"] for paper in list_project_papers(project["id"])]
        result = project_query(
            workspace_id=workspace_id,
            project_id=project["id"],
            query=question,
            doc_ids=doc_ids,
        )
        _display_result(result, workspace_id)
        
    elif scope == "mixed":
        if query_type == "global":
            results = []
            if course:
                results.append(
                    map_reduce_course_query(
                        workspace_id=workspace_id,
                        course_id=course["id"],
                        query=question,
                        map_tokens=map_tokens,
                        reduce_tokens=reduce_tokens,
                    )
                )
            if project:
                results.append(
                    map_reduce_project_query(
                        workspace_id=workspace_id,
                        project_id=project["id"],
                        query=question,
                        map_tokens=map_tokens,
                        reduce_tokens=reduce_tokens,
                    )
                )
            
            combined = "\n\n".join([item.answer for item in results])
            render_content_box(combined, L("综合回答", "Combined Answer"))
            
            for i, item in enumerate(results):
                with st.expander(f"{L('覆盖率报告', 'Coverage Report')} #{i+1}", expanded=True):
                    _display_coverage(item.coverage)
                    render_doc_citations(item.citations, workspace_id)
        else:
            doc_ids = []
            if course:
                doc_ids.extend(course_docs_for_qa(course["id"]))
            if project:
                doc_ids.extend([paper["doc_id"] for paper in list_project_papers(project["id"])])
            
            result = course_query(
                workspace_id=workspace_id,
                course_id=course["id"] if course else "",
                query=question,
                doc_ids=doc_ids,
            )
            render_answer_with_citations(
                text=result["answer"],
                citations=result.get("citations"),
                workspace_id=workspace_id,
            )
    else:
        st.warning(L("请先选择有效的范围。", "Please select a valid scope first."))


def _display_result(result: dict, workspace_id: str) -> None:
    """Display query result with appropriate formatting."""
    if result.get("query_type") == "global":
        render_content_box(result["answer"])
        
        coverage = result.get("coverage")
        if coverage:
            with st.expander(L("📊 覆盖率报告", "📊 Coverage Report"), expanded=True):
                _display_coverage(coverage)
        
        render_doc_citations(result.get("citations"), workspace_id)
    else:
        render_answer_with_citations(
            text=result["answer"],
            citations=result.get("citations"),
            workspace_id=workspace_id,
        )


def _display_coverage(coverage: dict) -> None:
    """Display coverage metrics."""
    if not coverage:
        return
    
    col1, col2, col3 = st.columns(3)
    col1.metric(L("已包含", "Included"), coverage.get("included_docs", 0))
    col2.metric(L("缺失", "Missing"), len(coverage.get("missing_docs", [])))
    col3.metric(L("总数", "Total"), coverage.get("total_docs", 0))
    
    missing = coverage.get("missing_docs", [])
    if missing:
        st.warning(f"⚠️ {L('以下文档未被覆盖', 'The following documents were not covered')}: {', '.join(missing[:5])}")
        if len(missing) > 5:
            st.caption(f"... {L('及其他', 'and')} {len(missing) - 5} {L('个', 'more')}")

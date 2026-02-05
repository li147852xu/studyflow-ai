from __future__ import annotations

import streamlit as st

from app.ui.components import render_empty_state, render_section_with_help
from app.ui.labels import L
from app.ui.locks import running_task_summary
from core.domains.course import (
    add_assignment_asset,
    add_lecture_material,
    list_assignments,
    list_course_lectures,
    list_courses,
)
from core.domains.research import add_paper, list_projects
from infra.db import get_connection
from service.document_service import count_documents, get_document, list_documents, set_document_type


def _doc_associations(doc_id: str) -> dict:
    with get_connection() as connection:
        lecture_rows = connection.execute(
            """
            SELECT lecture.id, lecture.topic, lecture.lecture_no, courses.name as course_name
            FROM lecture_material
            JOIN lecture ON lecture.id = lecture_material.lecture_id
            JOIN courses ON courses.id = lecture.course_id
            WHERE lecture_material.doc_id = ?
            """,
            (doc_id,),
        ).fetchall()
        assignment_rows = connection.execute(
            """
            SELECT assignment.id, assignment.title, courses.name as course_name
            FROM assignment_asset
            JOIN assignment ON assignment.id = assignment_asset.assignment_id
            JOIN courses ON courses.id = assignment.course_id
            WHERE assignment_asset.doc_id = ?
            """,
            (doc_id,),
        ).fetchall()
        paper_rows = connection.execute(
            """
            SELECT papers.id, papers.title, research_project.title as project_title
            FROM papers
            LEFT JOIN research_project ON research_project.id = papers.project_id
            WHERE papers.doc_id = ?
            """,
            (doc_id,),
        ).fetchall()
        course_rows = connection.execute(
            """
            SELECT courses.id, courses.name
            FROM course_documents
            JOIN courses ON courses.id = course_documents.course_id
            WHERE course_documents.doc_id = ?
            """,
            (doc_id,),
        ).fetchall()
    return {
        "lectures": [dict(row) for row in lecture_rows],
        "assignments": [dict(row) for row in assignment_rows],
        "papers": [dict(row) for row in paper_rows],
        "courses": [dict(row) for row in course_rows],
    }


def _get_file_icon(file_type: str | None) -> str:
    icons = {
        "pdf": "📕",
        "docx": "📘",
        "doc": "📘",
        "pptx": "📙",
        "ppt": "📙",
        "txt": "📝",
        "md": "📝",
        "html": "🌐",
        "jpg": "🖼️",
        "jpeg": "🖼️",
        "png": "🖼️",
    }
    return icons.get(file_type or "", "📄")


def _format_size(size: int | None) -> str:
    if not size:
        return "-"
    if size > 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    elif size > 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} B"


def render_library(*, main_col, inspector_col, workspace_id: str | None) -> None:
    with main_col:
        render_section_with_help(L("资料库", "Library"), "library")

        if not workspace_id:
            render_empty_state(
                "📚",
                L("请选择工作区", "Select a Workspace"),
                L("在侧边栏选择或创建工作区以管理文档。", "Select or create a workspace in the sidebar to manage documents."),
            )
            return

        locked, _ = running_task_summary(workspace_id)
        if locked:
            st.warning(L("⏳ 正在处理任务，请等待...", "⏳ Processing task, please wait..."))

        # Header with stats
        total_docs = count_documents(workspace_id)
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, var(--primary-light) 0%, transparent 100%);
                border: 1.5px solid rgba(59, 130, 246, 0.2);
                border-radius: var(--radius-lg);
                padding: var(--space-md) var(--space-lg);
                margin-bottom: var(--space-lg);
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <div>
                    <div style="font-size: 0.9rem; color: var(--muted-text);">{L("文档总数", "Total Documents")}</div>
                    <div style="font-size: 1.75rem; font-weight: 700; color: var(--text-color);">{total_docs}</div>
                </div>
                <div style="font-size: 2.5rem; opacity: 0.5;">📚</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Filters in an expander for cleaner look
        with st.expander(L("🔍 筛选与排序", "🔍 Filters & Sorting"), expanded=True):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                doc_type = st.selectbox(
                    L("文档类型", "Doc Type"),
                    options=["all", "course", "paper", "other"],
                    format_func=lambda v: {
                        "all": L("全部类型", "All Types"),
                        "course": L("📚 课程资料", "📚 Course"),
                        "paper": L("📄 论文", "📄 Paper"),
                        "other": L("📁 其他", "📁 Other"),
                    }.get(v, v),
                    key="library_doc_type_filter",
                )

            with col2:
                # Get available file types
                with get_connection() as connection:
                    rows = connection.execute(
                        "SELECT DISTINCT file_type FROM documents WHERE workspace_id = ? AND file_type IS NOT NULL ORDER BY file_type",
                        (workspace_id,),
                    ).fetchall()
                file_types = ["all"] + [row["file_type"] for row in rows if row["file_type"]]
                file_type = st.selectbox(
                    L("文件格式", "File Format"),
                    options=file_types,
                    format_func=lambda v: L("全部格式", "All Formats") if v == "all" else v.upper(),
                    key="library_file_type_filter",
                )

            with col3:
                sort_by = st.selectbox(
                    L("排序", "Sort By"),
                    options=["created_at", "filename", "size_bytes"],
                    format_func=lambda v: {
                        "created_at": L("📅 导入时间", "📅 Import Date"),
                        "filename": L("📝 文件名", "📝 Filename"),
                        "size_bytes": L("📊 文件大小", "📊 File Size"),
                    }.get(v, v),
                    key="library_sort_by",
                )

            with col4:
                sort_order = st.selectbox(
                    L("顺序", "Order"),
                    options=["desc", "asc"],
                    format_func=lambda v: L("↓ 降序", "↓ Desc") if v == "desc" else L("↑ 升序", "↑ Asc"),
                    key="library_sort_order",
                )

            # Search
            search = st.text_input(
                L("搜索文件名", "Search by filename"),
                key="library_search",
                placeholder=L("输入关键词搜索...", "Enter keywords to search..."),
            )

        # Get documents
        total = count_documents(
            workspace_id,
            doc_type=None if doc_type == "all" else doc_type,
            search=search or None,
        )

        page_size = 12
        total_pages = max(1, (total + page_size - 1) // page_size)

        # Pagination controls at top
        pag_col1, pag_col2, pag_col3 = st.columns([1, 2, 1])
        with pag_col1:
            if st.button("◀", key="lib_prev_page", disabled=st.session_state.get("library_page", 1) <= 1):
                st.session_state["library_page"] = max(1, st.session_state.get("library_page", 1) - 1)
                st.rerun()
        with pag_col2:
            page = st.session_state.get("library_page", 1)
            st.markdown(
                f"<div style='text-align: center; padding: 8px;'>{L('第', 'Page ')} <strong>{page}</strong> / {total_pages}</div>",
                unsafe_allow_html=True,
            )
        with pag_col3:
            if st.button("▶", key="lib_next_page", disabled=st.session_state.get("library_page", 1) >= total_pages):
                st.session_state["library_page"] = min(total_pages, st.session_state.get("library_page", 1) + 1)
                st.rerun()

        page = st.session_state.get("library_page", 1)
        offset = (int(page) - 1) * page_size
        docs = list_documents(
            workspace_id,
            limit=page_size,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            doc_type=None if doc_type == "all" else doc_type,
            search=search or None,
        )

        if file_type != "all":
            docs = [doc for doc in docs if doc.get("file_type") == file_type]

        if not docs:
            render_empty_state(
                "📂",
                L("暂无文档", "No Documents"),
                L("请导入文档或调整筛选条件。", "Please import documents or adjust filters."),
            )
        else:
            # Document grid
            st.markdown(
                """
                <div style="
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: var(--space-md);
                    margin-top: var(--space-md);
                ">
                """,
                unsafe_allow_html=True,
            )

            # Use columns for grid layout
            cols = st.columns(3)
            for idx, doc in enumerate(docs):
                icon = _get_file_icon(doc.get("file_type"))
                size_str = _format_size(doc.get("size_bytes") or doc.get("file_size"))
                doc_type_label = {
                    "course": L("课程", "Course"),
                    "paper": L("论文", "Paper"),
                    "other": L("其他", "Other"),
                }.get(doc.get("doc_type", "other"), doc.get("doc_type", "-"))

                type_color = {
                    "course": "var(--primary-color)",
                    "paper": "var(--success-color)",
                    "other": "var(--muted-text)",
                }.get(doc.get("doc_type", "other"), "var(--muted-text)")

                imported = doc.get("imported_at") or doc.get("created_at") or "-"
                if len(imported) > 10:
                    imported = imported[:10]

                filename_display = doc["filename"]
                if len(filename_display) > 28:
                    filename_display = filename_display[:25] + "..."

                with cols[idx % 3]:
                    # Card with click handler
                    selected = st.session_state.get("library_selected_doc") == doc["id"]
                    border_color = "var(--primary-color)" if selected else "var(--card-border)"
                    bg_color = "var(--primary-light)" if selected else "var(--card-bg)"

                    st.markdown(
                        f"""
                        <div style="
                            background: {bg_color};
                            border: 1.5px solid {border_color};
                            border-radius: var(--radius-lg);
                            padding: var(--space-md);
                            margin-bottom: var(--space-sm);
                            cursor: pointer;
                            transition: all 0.15s ease;
                        ">
                            <div style="display: flex; align-items: flex-start; gap: 12px;">
                                <span style="font-size: 2rem; line-height: 1;">{icon}</span>
                                <div style="flex: 1; min-width: 0;">
                                    <div style="font-weight: 600; color: var(--text-color); margin-bottom: 4px; word-break: break-word;" title="{doc["filename"]}">{filename_display}</div>
                                    <div style="font-size: 0.8rem; color: var(--muted-text);">{doc.get('file_type') or '-'} · {size_str}</div>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--card-border);">
                                <span style="
                                    display: inline-block;
                                    padding: 3px 10px;
                                    border-radius: var(--radius-full);
                                    font-size: 0.75rem;
                                    font-weight: 600;
                                    background: {type_color}20;
                                    color: {type_color};
                                ">{doc_type_label}</span>
                                <span style="font-size: 0.75rem; color: var(--muted-text);">{imported}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(L("查看", "View"), key=f"doc_btn_{doc['id']}", use_container_width=True):
                        st.session_state["library_selected_doc"] = doc["id"]
                        st.rerun()

        # Bottom pagination info
        st.caption(f"{L('共', 'Total ')} {total} {L('份文档', ' documents')}")

    with inspector_col:
        st.markdown(f"### {L('文档详情', 'Document Details')}")

        doc_id = st.session_state.get("library_selected_doc")
        if not doc_id:
            st.markdown(
                f"""
                <div style="
                    background: var(--surface-bg);
                    border: 2px dashed var(--card-border);
                    border-radius: var(--radius-lg);
                    padding: var(--space-xl);
                    text-align: center;
                    color: var(--muted-text);
                ">
                    <div style="font-size: 3rem; opacity: 0.4; margin-bottom: 12px;">👆</div>
                    <div style="font-weight: 500; color: var(--text-color); margin-bottom: 8px;">{L("选择文档", "Select a Document")}</div>
                    <div style="font-size: 0.9rem;">{L("点击左侧文档查看详情", "Click a document on the left to view details")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        doc = get_document(doc_id)
        if not doc:
            st.error(L("文档不存在", "Document not found"))
            return

        # Document header card
        icon = _get_file_icon(doc.get("file_type"))
        filename_display = doc['filename']
        if len(filename_display) > 30:
            filename_display = filename_display[:27] + "..."

        st.markdown(
            f"""
            <div style="
                background: var(--surface-bg);
                border-radius: var(--radius-lg);
                padding: var(--space-lg);
                text-align: center;
                margin-bottom: var(--space-md);
            ">
                <div style="font-size: 3rem; margin-bottom: 8px;">{icon}</div>
                <div style="font-weight: 600; color: var(--text-color); word-break: break-word;" title="{doc['filename']}">{filename_display}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Basic info in a clean grid
        st.markdown(f"#### {L('基本信息', 'Basic Info')}")
        info_cols = st.columns(2)
        with info_cols[0]:
            st.metric(L("类型", "Type"), doc.get('file_type') or '-')
        with info_cols[1]:
            st.metric(L("大小", "Size"), _format_size(doc.get('size_bytes') or doc.get('file_size')))

        info_cols2 = st.columns(2)
        with info_cols2[0]:
            st.metric(L("页数", "Pages"), doc.get('page_count') or '-')
        with info_cols2[1]:
            imported = (doc.get('imported_at') or doc.get('created_at') or '-')[:10]
            st.metric(L("导入", "Imported"), imported)

        # Document type selector
        st.markdown(f"#### {L('文档分类', 'Document Type')}")
        type_options = ["course", "paper", "other"]
        current_type = doc.get("doc_type") or "other"
        try:
            type_index = type_options.index(current_type)
        except ValueError:
            type_index = 2

        new_type = st.selectbox(
            L("类型", "Type"),
            options=type_options,
            index=type_index,
            format_func=lambda v: {
                "course": L("📚 课程资料", "📚 Course"),
                "paper": L("📄 论文", "📄 Paper"),
                "other": L("📁 其他", "📁 Other"),
            }.get(v, v),
            key="library_inspector_doc_type",
            label_visibility="collapsed",
        )

        if st.button(L("保存类型", "Save Type"), disabled=locked, key="btn_save_doc_type"):
            set_document_type(doc_id=doc_id, doc_type=new_type)
            st.success(L("✓ 已更新", "✓ Updated"))
            st.rerun()

        # Associations
        associations = _doc_associations(doc_id)

        st.markdown(f"#### {L('关联信息', 'Associations')}")

        has_associations = False

        if associations["courses"]:
            has_associations = True
            st.markdown(f"**{L('关联课程', 'Linked Courses')}:**")
            for course in associations["courses"]:
                st.write(f"  📚 {course['name']}")

        if associations["lectures"]:
            has_associations = True
            st.markdown(f"**{L('关联讲次', 'Linked Lectures')}:**")
            for lecture in associations["lectures"]:
                st.write(f"  📖 {lecture.get('course_name')} - {L('第', 'Lecture ')}{lecture.get('lecture_no')}{L('讲', '')}")

        if associations["assignments"]:
            has_associations = True
            st.markdown(f"**{L('关联作业', 'Linked Assignments')}:**")
            for assignment in associations["assignments"]:
                st.write(f"  📝 {assignment.get('course_name')} - {assignment.get('title')}")

        if associations["papers"]:
            has_associations = True
            st.markdown(f"**{L('关联论文', 'Linked Papers')}:**")
            for paper in associations["papers"]:
                project = paper.get('project_title') or L('无项目', 'No project')
                st.write(f"  📄 {paper.get('title')} ({project})")

        if not has_associations:
            st.caption(L("暂无关联", "No associations"))

        # Quick link section
        st.divider()
        st.markdown(f"#### {L('快速关联', 'Quick Link')}")

        # Link to course
        courses = list_courses(workspace_id)
        if courses:
            with st.expander(L("关联到课程", "Link to Course"), expanded=False):
                course_map = {c["name"]: c for c in courses}
                course_choice = st.selectbox(
                    L("选择课程", "Select Course"),
                    options=list(course_map.keys()),
                    key="library_attach_course",
                    label_visibility="collapsed",
                )

                lectures = list_course_lectures(course_map[course_choice]["id"])
                if lectures:
                    lecture_map = {f"{L('第', 'Lecture ')}{lec.get('lecture_no')}{L('讲', '')}": lec for lec in lectures}
                    lecture_choice = st.selectbox(
                        L("选择讲次", "Select Lecture"),
                        options=list(lecture_map.keys()),
                        key="library_attach_lecture",
                        label_visibility="collapsed",
                    )
                    role = st.selectbox(
                        L("材料类型", "Material Type"),
                        options=["slides", "notes", "reading", "other"],
                        format_func=lambda v: {
                            "slides": L("📊 课件", "📊 Slides"),
                            "notes": L("📝 讲义", "📝 Notes"),
                            "reading": L("📖 阅读", "📖 Reading"),
                            "other": L("📄 其他", "📄 Other"),
                        }.get(v, v),
                        key="library_attach_lecture_role",
                        label_visibility="collapsed",
                    )
                    if st.button(L("关联到讲次", "Link to Lecture"), disabled=locked, key="btn_attach_to_lecture", type="primary"):
                        add_lecture_material(
                            lecture_id=lecture_map[lecture_choice]["id"],
                            doc_id=doc_id,
                            role=role,
                        )
                        st.success(L("✓ 已关联", "✓ Linked"))
                        st.rerun()

                assignments = list_assignments(course_map[course_choice]["id"])
                if assignments:
                    st.markdown("---")
                    assign_map = {item["title"]: item for item in assignments}
                    assign_choice = st.selectbox(
                        L("选择作业", "Select Assignment"),
                        options=list(assign_map.keys()),
                        key="library_attach_assignment",
                        label_visibility="collapsed",
                    )
                    assign_role = st.selectbox(
                        L("资源类型", "Asset Type"),
                        options=["spec", "solution_draft", "reference", "other"],
                        format_func=lambda v: {
                            "spec": L("📋 题目", "📋 Problem"),
                            "solution_draft": L("✏️ 草稿", "✏️ Draft"),
                            "reference": L("📖 参考", "📖 Reference"),
                            "other": L("📄 其他", "📄 Other"),
                        }.get(v, v),
                        key="library_attach_assign_role",
                        label_visibility="collapsed",
                    )
                    if st.button(L("关联到作业", "Link to Assignment"), disabled=locked, key="btn_attach_to_assignment", type="primary"):
                        add_assignment_asset(
                            assignment_id=assign_map[assign_choice]["id"],
                            doc_id=doc_id,
                            role=assign_role,
                        )
                        st.success(L("✓ 已关联", "✓ Linked"))
                        st.rerun()

        # Link to project as paper
        projects = list_projects(workspace_id)
        if projects:
            with st.expander(L("关联为项目论文", "Link as Project Paper"), expanded=False):
                proj_map = {p["title"]: p for p in projects}
                proj_choice = st.selectbox(
                    L("选择项目", "Select Project"),
                    options=list(proj_map.keys()),
                    key="library_attach_project",
                    label_visibility="collapsed",
                )
                title = st.text_input(L("论文标题", "Paper Title"), key="library_paper_title", value=doc.get("filename", "").rsplit(".", 1)[0])
                authors = st.text_input(L("作者", "Authors"), key="library_paper_authors", placeholder="Author 1, Author 2")
                col1, col2 = st.columns(2)
                with col1:
                    year = st.text_input(L("年份", "Year"), key="library_paper_year", placeholder="2026")
                with col2:
                    venue = st.text_input(L("期刊/会议", "Venue"), key="library_paper_venue")

                if st.button(L("关联为论文", "Link as Paper"), disabled=locked, key="btn_attach_as_paper", type="primary"):
                    add_paper(
                        workspace_id=workspace_id,
                        doc_id=doc_id,
                        title=title.strip() or doc.get("filename") or "Paper",
                        authors=authors.strip() or "-",
                        year=year.strip() or "-",
                        venue=venue.strip() or None,
                        project_id=proj_map[proj_choice]["id"],
                    )
                    st.success(L("✓ 已关联到项目", "✓ Linked to project"))
                    st.rerun()

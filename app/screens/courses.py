from __future__ import annotations

import streamlit as st

from app.ui.components import (
    push_generation_start_notification,
    push_notification,
    render_answer_with_citations,
    render_content_box,
    render_doc_citations,
    render_empty_state,
    render_header_card,
    render_section_with_help,
)
from app.ui.labels import L
from app.ui.locks import running_task_summary
from core.domains.course import (
    add_assignment_asset,
    add_lecture_material,
    create_assignment,
    create_course,
    create_lecture,
    create_schedule,
    link_course_document,
    list_assignments,
    list_course_documents,
    list_course_lectures,
    list_courses,
    list_lecture_materials,
    list_schedules,
    update_course,
)
from service.course_v3_service import (
    course_docs_for_qa,
    generate_assignment_analysis,
    generate_course_cheatsheet,
    generate_course_overview,
    generate_exam_blueprint,
    get_persisted_course_cheatsheet,
    get_persisted_course_overview,
)
from service.document_service import list_documents
from service.rag_service import course_query


def render_courses(*, main_col, inspector_col, workspace_id: str | None) -> None:
    with main_col:
        render_section_with_help(L("课程管理", "Course Management"), "courses")

        if not workspace_id:
            render_empty_state(
                "📚",
                L("请选择工作区", "Select a Workspace"),
                L("在侧边栏选择或创建工作区以开始管理课程。", "Select or create a workspace in the sidebar to start managing courses."),
            )
            return

        locked, _ = running_task_summary(workspace_id)
        if locked:
            st.warning(L("⏳ 正在处理任务，请等待...", "⏳ Processing task, please wait..."))

        # Course selector and create button
        courses = list_courses(workspace_id)

        # Header row with course selector
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            if courses:
                course_names = [c["name"] for c in courses]
                selected_name = st.selectbox(
                    L("选择课程", "Select Course"),
                    options=course_names,
                    key="courses_main_selector",
                    label_visibility="collapsed",
                )
                course = next((c for c in courses if c["name"] == selected_name), None)
            else:
                course = None

        with col2:
            if st.button(L("➕ 新建", "➕ New"), key="btn_show_create_course", use_container_width=True, type="primary"):
                st.session_state["show_create_course"] = True

        with col3:
            total_courses = len(courses)
            st.markdown(
                f"<div style='padding: 8px 0; text-align: center; color: var(--muted-text); font-size: 0.9rem;'>{total_courses} {L('门课程', ' courses')}</div>",
                unsafe_allow_html=True,
            )

        if not courses:
            render_empty_state(
                "📚",
                L("暂无课程", "No Courses Yet"),
                L("点击上方「新建」按钮创建第一门课程。", "Click the 'New' button above to create your first course."),
            )
            st.session_state["show_create_course"] = True

        # Create course dialog
        if st.session_state.get("show_create_course"):
            st.markdown(
                """
                <div style="
                    background: var(--primary-light);
                    border: 1.5px solid var(--primary-color);
                    border-radius: var(--radius-lg);
                    padding: var(--space-lg);
                    margin: var(--space-md) 0;
                ">
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f"#### {L('创建新课程', 'Create New Course')}")

            name = st.text_input(L("课程名称", "Course Name"), key="new_course_name", placeholder=L("例如：机器学习导论", "e.g. Introduction to Machine Learning"))
            col_a, col_b = st.columns(2)
            with col_a:
                code = st.text_input(L("课程代码", "Course Code"), key="new_course_code", placeholder="CS229")
                instructor = st.text_input(L("授课教师", "Instructor"), key="new_course_instructor")
            with col_b:
                semester = st.text_input(L("学期", "Semester"), key="new_course_semester", placeholder="2026 Spring")

            col_btn1, col_btn2, _ = st.columns([1, 1, 2])
            with col_btn1:
                if st.button(L("✓ 创建", "✓ Create"), disabled=locked or not name.strip(), key="btn_create_course", type="primary", use_container_width=True):
                    create_course(
                        workspace_id=workspace_id,
                        name=name.strip(),
                        code=code.strip() or None,
                        instructor=instructor.strip() or None,
                        semester=semester.strip() or None,
                    )
                    st.success(L("✓ 课程创建成功！", "✓ Course created successfully!"))
                    st.session_state["show_create_course"] = False
                    st.rerun()
            with col_btn2:
                if st.button(L("取消", "Cancel"), key="btn_cancel_create_course", use_container_width=True):
                    st.session_state["show_create_course"] = False
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        if not course:
            return

        # Course header card
        meta_parts = []
        if course.get('code'):
            meta_parts.append(course['code'])
        if course.get('instructor'):
            meta_parts.append(f"👤 {course['instructor']}")
        if course.get('semester'):
            meta_parts.append(f"📅 {course['semester']}")

        render_header_card(
            course["name"],
            " · ".join(meta_parts) if meta_parts else L("课程详情", "Course details"),
        )

        # Tabs - reorganized for clarity
        tabs = st.tabs([
            L("📖 概览", "📖 Overview"),
            L("⚙️ 课程信息", "⚙️ Course Info"),
            L("📁 资料", "📁 Materials"),
            L("📚 讲次", "📚 Lectures"),
            L("📝 作业", "📝 Assignments"),
            L("📋 考试", "📋 Exam"),
            L("💬 问答", "💬 Q&A"),
        ])

        # Tab 0: Overview - Generated content only (no edit)
        with tabs[0]:
            _render_overview_tab(workspace_id, course, locked)

        # Tab 1: Course Info - Schedule and edit info
        with tabs[1]:
            _render_course_info_tab(workspace_id, course, locked)

        # Tab 2: Materials - Separate materials management
        with tabs[2]:
            _render_materials_tab(workspace_id, course, locked)

        # Tab 3: Lectures
        with tabs[3]:
            _render_lectures_tab(workspace_id, course, locked)

        # Tab 4: Assignments
        with tabs[4]:
            _render_assignments_tab(workspace_id, course, locked)

        # Tab 5: Exam
        with tabs[5]:
            _render_exam_tab(workspace_id, course, locked)

        # Tab 6: Q&A
        with tabs[6]:
            _render_qa_tab(workspace_id, course, locked)

    with inspector_col:
        st.markdown(f"### {L('课程详情', 'Course Details')}")
        if course:
            # Course info card
            st.markdown(
                f"""
                <div style="
                    background: var(--surface-bg);
                    border-radius: var(--radius-lg);
                    padding: var(--space-md);
                    text-align: center;
                    margin-bottom: var(--space-md);
                ">
                    <div style="font-size: 2.5rem; margin-bottom: 8px;">📚</div>
                    <div style="font-weight: 600; color: var(--text-color); font-size: 1.1rem;">{course['name']}</div>
                    <div style="font-size: 0.85rem; color: var(--muted-text); margin-top: 4px;">{course.get('code') or '-'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Basic info in compact form
            st.markdown(f"#### {L('基本信息', 'Basic Info')}")
            info_items = [
                (L("教师", "Instructor"), course.get('instructor') or '-'),
                (L("学期", "Semester"), course.get('semester') or '-'),
            ]
            for label, value in info_items:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--card-border);">
                        <span style="color: var(--muted-text); font-size: 0.9rem;">{label}</span>
                        <span style="color: var(--text-color); font-weight: 500; font-size: 0.9rem;">{value}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("")  # Spacing

            # Quick stats
            docs = list_course_documents(course["id"])
            lectures = list_course_lectures(course["id"])
            assignments = list_assignments(course["id"])

            st.markdown(f"#### {L('统计', 'Statistics')}")
            col1, col2 = st.columns(2)
            col1.metric(L("资料", "Materials"), len(docs))
            col2.metric(L("讲次", "Lectures"), len(lectures))

            col1, col2 = st.columns(2)
            col1.metric(L("作业", "Assignments"), len(assignments))
            pending = sum(1 for a in assignments if a.get("status") != "done")
            col2.metric(L("待完成", "Pending"), pending)

            st.markdown("")  # Spacing

            # Quick actions
            st.markdown(f"#### {L('快速操作', 'Quick Actions')}")
            if st.button(L("📁 关联资料", "📁 Link Materials"), key="quick_link_materials", use_container_width=True):
                pass  # Will switch to materials tab
            if st.button(L("📚 添加讲次", "📚 Add Lecture"), key="quick_add_lecture", use_container_width=True):
                pass  # Will switch to lectures tab


def _render_overview_tab(workspace_id: str, course: dict, locked: bool) -> None:
    """Overview tab - course summary and AI-generated overview/cheatsheet."""

    # Load persisted content
    persisted_overview = get_persisted_course_overview(workspace_id, course["id"])
    persisted_cheatsheet = get_persisted_course_cheatsheet(workspace_id, course["id"])

    # Course Overview Section
    st.markdown(f"### {L('课程概览', 'Course Overview')}")

    if persisted_overview and persisted_overview.get("content"):
        render_content_box(persisted_overview["content"])
        st.caption(f"📅 {L('生成时间', 'Generated')}: {persisted_overview.get('created_at', '-')[:19]}")
    else:
        render_empty_state(
            "📝",
            L("尚未生成课程概览", "No Course Overview Yet"),
            L("点击下方按钮生成 AI 课程概览。", "Click the button below to generate an AI course overview."),
        )

    if st.button(
        L("🔄 生成/更新课程概览", "🔄 Generate/Update Overview"),
        disabled=locked,
        key="btn_gen_overview",
        type="primary" if not persisted_overview else "secondary",
    ):
        task_id = push_generation_start_notification(
            workspace_id=workspace_id,
            task_type="generate_course_overview",
            title=L("课程概览", "Course Overview"),
        )
        with st.spinner(L("正在生成课程概览...", "Generating course overview...")):
            result = generate_course_overview(workspace_id=workspace_id, course_id=course["id"])
            if result.get("error") == "missing_materials":
                push_notification(
                    workspace_id=workspace_id,
                    task_type="generate_course_overview",
                    title=L("课程概览", "Course Overview"),
                    status="failed",
                    summary=L("缺少资料", "Missing materials"),
                    task_id=task_id,
                )
                st.error(L("❌ 请先在「资料」标签页关联课程资料。", "❌ Please link course materials in the 'Materials' tab first."))
            else:
                push_notification(
                    workspace_id=workspace_id,
                    task_type="generate_course_overview",
                    title=L("课程概览", "Course Overview"),
                    status="succeeded",
                    summary=L("课程概览生成完成", "Course overview generated"),
                    target={"nav": "Courses"},
                    task_id=task_id,
                )
                st.success(L("✓ 课程概览已生成！", "✓ Course overview generated!"))
                st.rerun()

    st.divider()

    # Cheat Sheet Section
    st.markdown(f"### {L('速记表', 'Cheat Sheet')}")

    if persisted_cheatsheet and persisted_cheatsheet.get("content"):
        render_content_box(persisted_cheatsheet["content"])
        st.caption(f"📅 {L('生成时间', 'Generated')}: {persisted_cheatsheet.get('created_at', '-')[:19]}")
    else:
        render_empty_state(
            "📋",
            L("尚未生成速记表", "No Cheat Sheet Yet"),
            L("点击下方按钮生成考试速记表。", "Click the button below to generate an exam cheat sheet."),
        )

    if st.button(
        L("🔄 生成/更新速记表", "🔄 Generate/Update Cheat Sheet"),
        disabled=locked,
        key="btn_gen_cheatsheet",
        type="primary" if not persisted_cheatsheet else "secondary",
    ):
        task_id = push_generation_start_notification(
            workspace_id=workspace_id,
            task_type="generate_course_cheatsheet",
            title=L("速记表", "Cheat Sheet"),
        )
        with st.spinner(L("正在生成速记表...", "Generating cheat sheet...")):
            result = generate_course_cheatsheet(workspace_id=workspace_id, course_id=course["id"])
            if result.get("error") == "missing_materials":
                push_notification(
                    workspace_id=workspace_id,
                    task_type="generate_course_cheatsheet",
                    title=L("速记表", "Cheat Sheet"),
                    status="failed",
                    summary=L("缺少资料", "Missing materials"),
                    task_id=task_id,
                )
                st.error(L("❌ 请先在「资料」标签页关联课程资料。", "❌ Please link course materials in the 'Materials' tab first."))
            else:
                push_notification(
                    workspace_id=workspace_id,
                    task_type="generate_course_cheatsheet",
                    title=L("速记表", "Cheat Sheet"),
                    status="succeeded",
                    summary=L("速记表生成完成", "Cheat sheet generated"),
                    target={"nav": "Courses"},
                    task_id=task_id,
                )
                st.success(L("✓ 速记表已生成！", "✓ Cheat sheet generated!"))
                st.rerun()



def _render_course_info_tab(workspace_id: str, course: dict, locked: bool) -> None:
    """Course Info tab - schedule and basic info editing."""

    # Edit course info section
    st.markdown(f"### {L('课程基本信息', 'Course Basic Info')}")

    edit_name = st.text_input(L("课程名称", "Course Name"), value=course["name"], key="edit_course_name")
    col1, col2 = st.columns(2)
    with col1:
        edit_code = st.text_input(L("课程代码", "Course Code"), value=course.get("code") or "", key="edit_course_code", placeholder="e.g. CS229")
        edit_instructor = st.text_input(L("授课教师", "Instructor"), value=course.get("instructor") or "", key="edit_course_instructor")
    with col2:
        edit_semester = st.text_input(L("学期", "Semester"), value=course.get("semester") or "", key="edit_course_semester", placeholder="e.g. 2025 Spring")

    if st.button(L("💾 保存课程信息", "💾 Save Course Info"), disabled=locked, key="btn_save_course", type="primary", use_container_width=True):
        update_course(
            course_id=course["id"],
            name=edit_name.strip(),
            code=edit_code.strip() or None,
            instructor=edit_instructor.strip() or None,
            semester=edit_semester.strip() or None,
        )
        st.success(L("✓ 课程信息已更新", "✓ Course info updated"))
        st.rerun()

    st.divider()

    # Course Schedule Section
    st.markdown(f"### {L('课程时间安排', 'Course Schedule')}")
    st.caption(L("设置每周上课时间，将自动同步到仪表盘的课程表中。", "Set weekly class times. They will automatically appear in your dashboard timetable."))

    schedules = list_schedules(course["id"])
    if schedules:
        for item in schedules:
            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                st.markdown(f"🕐 **{item['weekday']}**")
            with col2:
                st.markdown(f"{item['start_time']} - {item['end_time']} @ {item.get('location') or '-'}")
            with col3:
                if st.button("🗑️", key=f"del_sched_{item['id']}", help=L("删除", "Delete")):
                    # Delete schedule
                    from infra.db import get_connection
                    with get_connection() as connection:
                        connection.execute("DELETE FROM course_schedule WHERE id = ?", (item['id'],))
                        connection.commit()
                    st.rerun()
    else:
        render_empty_state(
            "📅",
            L("暂无课程时间", "No Schedule Set"),
            L("添加每周上课时间。", "Add weekly class times."),
        )

    st.markdown("---")
    st.markdown(f"**{L('添加上课时间', 'Add Class Time')}**")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        weekday_options = [
            L("周一", "Monday"),
            L("周二", "Tuesday"),
            L("周三", "Wednesday"),
            L("周四", "Thursday"),
            L("周五", "Friday"),
            L("周六", "Saturday"),
            L("周日", "Sunday"),
        ]
        weekday = st.selectbox(L("星期", "Day"), options=weekday_options, key="sched_weekday")
    with col2:
        start_time = st.time_input(L("开始时间", "Start"), key="sched_start")
    with col3:
        end_time = st.time_input(L("结束时间", "End"), key="sched_end")
    with col4:
        location = st.text_input(L("地点", "Location"), key="sched_location", placeholder="Room 101")

    if st.button(L("➕ 添加时间", "➕ Add Schedule"), disabled=locked, key="btn_add_schedule", type="primary"):
        create_schedule(
            course_id=course["id"],
            weekday=weekday,
            start_time=start_time.strftime("%H:%M"),
            end_time=end_time.strftime("%H:%M"),
            location=location.strip() or None,
        )
        st.success(L("✓ 时间已添加", "✓ Schedule added"))
        st.rerun()


def _render_materials_tab(workspace_id: str, course: dict, locked: bool) -> None:
    """Materials tab - manage course documents separately."""

    st.markdown(f"### {L('课程资料', 'Course Materials')}")
    st.caption(L("关联资料库中的文档到本课程，用于生成概览、速记表和问答。", "Link documents from the library to this course for generating overviews, cheat sheets, and Q&A."))

    linked_docs = list_course_documents(course["id"])

    if linked_docs:
        st.markdown(f"**{L('已关联资料', 'Linked Materials')}** ({len(linked_docs)})")
        for doc in linked_docs:
            icon = "📕" if doc.get("file_type") == "pdf" else "📄"
            st.markdown(f"{icon} **{doc['filename']}** · {doc.get('file_type') or '-'}")
    else:
        render_empty_state(
            "📂",
            L("暂无关联资料", "No Materials Linked"),
            L("从下方的资料库中选择文档关联到本课程。", "Select documents from the library below to link to this course."),
        )

    st.divider()

    # Link documents from library
    st.markdown(f"### {L('从资料库关联', 'Link from Library')}")

    docs = list_documents(workspace_id)
    if not docs:
        st.info(L("资料库为空。请先在「资料库」页面导入文档。", "Library is empty. Please import documents in the 'Library' page first."))
    else:
        # Filter out already linked docs
        linked_ids = {doc["id"] for doc in linked_docs}
        available_docs = [doc for doc in docs if doc["id"] not in linked_ids]

        if not available_docs:
            st.info(L("所有文档都已关联到本课程。", "All documents are already linked to this course."))
        else:
            doc_map = {doc["filename"]: doc for doc in available_docs}

            col1, col2 = st.columns([3, 1])
            with col1:
                selected_doc = st.selectbox(
                    L("选择文档", "Select Document"),
                    options=list(doc_map.keys()),
                    key="materials_link_doc_select",
                    label_visibility="collapsed",
                )
            with col2:
                if st.button(L("➕ 关联", "➕ Link"), disabled=locked or not selected_doc, key="btn_link_course_doc", use_container_width=True, type="primary"):
                    link_course_document(course_id=course["id"], doc_id=doc_map[selected_doc]["id"])
                    st.success(L("✓ 已关联资料", "✓ Material linked"))
                    st.rerun()


def _render_lectures_tab(workspace_id: str, course: dict, locked: bool) -> None:
    """Lectures tab - manage lecture structure and per-lecture materials."""

    st.markdown(f"### {L('讲次管理', 'Lecture Management')}")
    st.caption(L("按讲次组织课程内容，为每讲关联对应的课件、讲义和阅读材料。", "Organize course content by lectures, and link slides, notes, and readings for each lecture."))

    lectures = list_course_lectures(course["id"])

    if not lectures:
        render_empty_state(
            "📚",
            L("暂无讲次", "No Lectures Yet"),
            L("创建讲次以组织课程内容。", "Create lectures to organize course content."),
        )
    else:
        for lecture in lectures:
            with st.expander(f"**{L('第', 'Lecture ')} {lecture.get('lecture_no') or '-'} {L('讲', '')}** · {lecture.get('topic') or L('未命名', 'Untitled')}", expanded=False):
                st.caption(f"📅 {lecture.get('date') or L('日期未设置', 'Date not set')}")

                materials = list_lecture_materials(lecture["id"])
                if materials:
                    st.markdown(f"**{L('关联材料', 'Materials')}:**")
                    for item in materials:
                        role_label = {
                            "slides": "📊 " + L("课件", "Slides"),
                            "notes": "📝 " + L("讲义", "Notes"),
                            "reading": "📖 " + L("阅读", "Reading"),
                            "other": "📄 " + L("其他", "Other"),
                        }.get(item["role"], item["role"])
                        st.write(f"  {role_label}: {item['filename']}")
                else:
                    st.caption(L("暂无关联材料", "No materials linked"))

                # Link material to this lecture
                st.markdown("---")
                docs = list_documents(workspace_id)
                if docs:
                    doc_map = {doc["filename"]: doc for doc in docs}
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        doc_name = st.selectbox(
                            L("选择文档", "Select"),
                            options=list(doc_map.keys()),
                            key=f"lec_mat_doc_{lecture['id']}",
                            label_visibility="collapsed",
                        )
                    with col2:
                        role = st.selectbox(
                            L("类型", "Type"),
                            options=["slides", "notes", "reading", "other"],
                            key=f"lec_mat_role_{lecture['id']}",
                            label_visibility="collapsed",
                        )
                    with col3:
                        if st.button(L("关联", "Link"), key=f"btn_link_lec_mat_{lecture['id']}", disabled=locked):
                            add_lecture_material(
                                lecture_id=lecture["id"],
                                doc_id=doc_map[doc_name]["id"],
                                role=role,
                            )
                            st.success(L("✓ 已关联", "✓ Linked"))
                            st.rerun()

    st.divider()

    # Add lecture form
    st.markdown(f"### {L('添加讲次', 'Add Lecture')}")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        lecture_no = st.number_input(L("序号", "No."), min_value=1, step=1, value=len(lectures) + 1, key="add_lecture_no")
    with col2:
        date = st.text_input(L("日期", "Date"), key="lecture_date", placeholder="2026-02-05")
    with col3:
        topic = st.text_input(L("主题", "Topic"), key="lecture_topic", placeholder=L("例如：神经网络基础", "e.g. Neural Networks Basics"))

    if st.button(L("➕ 创建讲次", "➕ Create Lecture"), disabled=locked, key="btn_create_lecture", type="primary"):
        create_lecture(
            course_id=course["id"],
            lecture_no=int(lecture_no),
            date=date.strip() or None,
            topic=topic.strip() or None,
        )
        st.success(L("✓ 讲次已创建", "✓ Lecture created"))
        st.rerun()


def _render_assignments_tab(workspace_id: str, course: dict, locked: bool) -> None:
    """Assignments tab - manage homework and get AI analysis."""

    st.markdown(f"### {L('作业管理', 'Assignment Management')}")

    assignments = list_assignments(course["id"])

    if not assignments:
        render_empty_state(
            "📝",
            L("暂无作业", "No Assignments Yet"),
            L("添加作业以跟踪进度和获取 AI 分析。", "Add assignments to track progress and get AI analysis."),
        )
    else:
        for assignment in assignments:
            status_icon = {"todo": "⬜", "doing": "🟡", "done": "✅"}.get(assignment["status"], "⬜")

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"{status_icon} **{assignment['title']}**")
                if assignment.get("due_at"):
                    st.caption(f"📅 {L('截止', 'Due')}: {assignment['due_at']}")
            with col2:
                new_status = st.selectbox(
                    L("状态", "Status"),
                    options=["todo", "doing", "done"],
                    index=["todo", "doing", "done"].index(assignment["status"]),
                    key=f"assign_status_{assignment['id']}",
                    label_visibility="collapsed",
                )
                if new_status != assignment["status"] and not locked:
                    from infra.db import get_connection
                    with get_connection() as connection:
                        connection.execute("UPDATE assignment SET status = ? WHERE id = ?", (new_status, assignment["id"]))
                        connection.commit()
                    st.rerun()
            with col3:
                if st.button(L("🤖 分析", "🤖 Analyze"), key=f"btn_analyze_{assignment['id']}", disabled=locked):
                    with st.spinner(L("分析中...", "Analyzing...")):
                        result = generate_assignment_analysis(
                            workspace_id=workspace_id,
                            assignment_id=assignment["id"],
                            title=assignment["title"],
                        )
                        st.session_state[f"analysis_{assignment['id']}"] = result["content"]

            # Show analysis if available
            if st.session_state.get(f"analysis_{assignment['id']}"):
                with st.expander(L("AI 分析结果", "AI Analysis"), expanded=True):
                    render_content_box(st.session_state[f"analysis_{assignment['id']}"])

            st.markdown("---")

    st.divider()

    # Add assignment form
    st.markdown(f"### {L('添加作业', 'Add Assignment')}")
    col1, col2 = st.columns([3, 1])
    with col1:
        title = st.text_input(L("作业标题", "Title"), key="assign_title", placeholder=L("例如：第一次编程作业", "e.g. Programming Assignment 1"))
    with col2:
        due_at = st.text_input(L("截止日期", "Due Date"), key="assign_due", placeholder="2026-02-15")

    if st.button(L("➕ 创建作业", "➕ Create Assignment"), disabled=locked or not title.strip(), key="btn_create_assignment", type="primary"):
        create_assignment(
            course_id=course["id"],
            title=title.strip(),
            due_at=due_at.strip() or None,
            status="todo",
        )
        st.success(L("✓ 作业已创建", "✓ Assignment created"))
        st.rerun()

    # Link assignment assets
    if assignments:
        st.divider()
        st.markdown(f"### {L('关联作业资源', 'Link Assignment Assets')}")
        st.caption(L("将题目文档、参考资料等关联到作业。", "Link problem sets, references, etc. to assignments."))

        assignment_map = {item["title"]: item for item in assignments}
        docs = list_documents(workspace_id)

        if docs:
            doc_map = {doc["filename"]: doc for doc in docs}
            col1, col2 = st.columns(2)
            with col1:
                selected_assign = st.selectbox(L("选择作业", "Assignment"), options=list(assignment_map.keys()), key="assign_asset_select")
                selected_doc = st.selectbox(L("选择文档", "Document"), options=list(doc_map.keys()), key="assign_asset_doc_select")
            with col2:
                role = st.selectbox(
                    L("资源类型", "Asset Type"),
                    options=["spec", "solution_draft", "reference", "other"],
                    format_func=lambda x: {
                        "spec": L("题目", "Problem Set"),
                        "solution_draft": L("解答草稿", "Solution Draft"),
                        "reference": L("参考资料", "Reference"),
                        "other": L("其他", "Other"),
                    }.get(x, x),
                    key="assign_asset_role_select",
                )
                if st.button(L("关联资源", "Link Asset"), disabled=locked, key="btn_attach_assign_asset", type="primary"):
                    add_assignment_asset(
                        assignment_id=assignment_map[selected_assign]["id"],
                        doc_id=doc_map[selected_doc]["id"],
                        role=role,
                    )
                    st.success(L("✓ 资源已关联", "✓ Asset linked"))
                    st.rerun()


def _render_exam_tab(workspace_id: str, course: dict, locked: bool) -> None:
    """Exam tab - generate exam blueprints with coverage report."""

    st.markdown(f"### {L('考试大纲', 'Exam Blueprint')}")
    st.caption(L("基于课程资料自动生成考试大纲，包含知识点、题型建议和覆盖率报告。", "Generate exam blueprints based on course materials, including topics, question types, and coverage reports."))

    if st.button(L("🔄 生成考试大纲", "🔄 Generate Exam Blueprint"), disabled=locked, key="btn_gen_exam_blueprint", type="primary"):
        task_id = push_generation_start_notification(
            workspace_id=workspace_id,
            task_type="generate_exam_blueprint",
            title=L("考试大纲", "Exam Blueprint"),
        )
        with st.spinner(L("正在生成考试大纲...", "Generating exam blueprint...")):
            result = generate_exam_blueprint(workspace_id=workspace_id, course_id=course["id"])
            st.session_state["exam_blueprint"] = result
            push_notification(
                workspace_id=workspace_id,
                task_type="generate_exam_blueprint",
                title=L("考试大纲", "Exam Blueprint"),
                status="succeeded",
                summary=L("考试大纲生成完成", "Exam blueprint generated"),
                target={"nav": "Courses"},
                task_id=task_id,
            )

    if st.session_state.get("exam_blueprint"):
        result = st.session_state["exam_blueprint"]

        st.markdown(f"#### {L('大纲内容', 'Blueprint')}")
        render_content_box(result["answer"])

        st.markdown(f"#### {L('覆盖率报告', 'Coverage Report')}")
        coverage = result.get("coverage") or {}

        # Handle different coverage formats - included_docs could be int or list
        included_docs = coverage.get("included_docs", 0)
        if isinstance(included_docs, list):
            included_docs = len(included_docs)

        missing_docs = coverage.get("missing_docs", [])
        if isinstance(missing_docs, int):
            missing_docs_count = missing_docs
        else:
            missing_docs_count = len(missing_docs) if missing_docs else 0

        missing_lectures = coverage.get("missing_lectures", [])
        if isinstance(missing_lectures, int):
            missing_lectures_count = missing_lectures
        else:
            missing_lectures_count = len(missing_lectures) if missing_lectures else 0

        col1, col2, col3 = st.columns(3)
        col1.metric(L("覆盖文档", "Covered Docs"), included_docs)
        col2.metric(L("缺失文档", "Missing Docs"), missing_docs_count)
        col3.metric(L("缺失讲次", "Missing Lectures"), missing_lectures_count)

        if coverage.get("missing_docs") or coverage.get("missing_lectures"):
            st.warning(L("⚠️ 覆盖不完整，部分讲次或文档未被索引。", "⚠️ Coverage incomplete. Some lectures or documents are not indexed."))

            col1, col2, col3 = st.columns(3)
            col1.button(L("📥 导入缺失", "📥 Import Missing"), key="exam_import_missing")
            col2.button(L("🔄 重建索引", "🔄 Rebuild Index"), key="exam_rebuild_index")
            col3.button(L("📂 扩展范围", "📂 Expand Scope"), key="exam_expand_scope")

        with st.expander(L("详细覆盖数据", "Detailed Coverage"), expanded=False):
            st.json(coverage)

        render_doc_citations(result.get("citations"), workspace_id)


def _render_qa_tab(workspace_id: str, course: dict, locked: bool) -> None:
    """Q&A tab - ask questions within course scope."""

    st.markdown(f"### {L('课程问答', 'Course Q&A')}")
    st.caption(L("在课程范围内提问，AI 将基于已关联的资料回答。", "Ask questions within the course scope. AI will answer based on linked materials."))

    question = st.text_area(
        L("输入问题", "Enter Question"),
        key="course_qa_question",
        placeholder=L("例如：什么是反向传播算法？它的主要步骤是什么？", "e.g. What is backpropagation? What are its main steps?"),
        height=100,
    )

    if st.button(L("🔍 提问", "🔍 Ask"), disabled=locked or not question.strip(), key="btn_course_qa_ask", type="primary"):
        with st.spinner(L("正在检索并生成回答...", "Retrieving and generating answer...")):
            doc_ids = course_docs_for_qa(course["id"])
            if not doc_ids:
                st.error(L("❌ 请先关联课程资料。", "❌ Please link course materials first."))
            else:
                result = course_query(
                    workspace_id=workspace_id,
                    course_id=course["id"],
                    query=question,
                    doc_ids=doc_ids,
                )
                st.session_state["qa_result"] = result

    if st.session_state.get("qa_result"):
        result = st.session_state["qa_result"]

        st.markdown(f"#### {L('回答', 'Answer')}")

        if result.get("query_type") == "global":
            render_content_box(result["answer"])

            coverage = result.get("coverage") or {}
            if coverage.get("missing_docs") or coverage.get("missing_lectures"):
                st.warning(L("⚠️ 覆盖不完整", "⚠️ Coverage incomplete"))

            with st.expander(L("覆盖率报告", "Coverage Report"), expanded=False):
                st.json(coverage)

            render_doc_citations(result.get("citations"), workspace_id)
        else:
            render_answer_with_citations(
                text=result["answer"],
                citations=result.get("citations"),
                workspace_id=workspace_id,
            )

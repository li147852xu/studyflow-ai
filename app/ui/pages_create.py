from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from app.ui.components import (
    citations_from_hits_json,
    render_answer_with_citations,
    render_inspector,
    section_title,
)
from app.ui.i18n import t
from app.ui.locks import running_task_summary
from core.ui_state.guards import llm_ready
from service.api_mode_adapter import ApiModeAdapter
from service.asset_service import read_version_by_id
from service.course_service import (
    create_course,
    link_document,
    list_course_documents,
    list_courses,
)
from service.document_service import list_documents
from service.recent_activity_service import list_recent_activity
from service.retrieval_service import index_status
from service.tasks_service import enqueue_generate_task, list_tasks_for_workspace, run_task_in_background


def _format_time(iso_time: str | None) -> str:
    if not iso_time:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return iso_time[:19] if iso_time else "-"


def _auto_retrieval_mode(workspace_id: str) -> str:
    status = index_status(workspace_id)
    if status.get("vector_count", 0) > 0:
        return "hybrid"
    return "bm25"


def _latest_generate_task(*, workspace_id: str, type_prefix: str | None = None) -> dict | None:
    """Return the most recent generate task (active or recently completed).

    Args:
        workspace_id: The workspace ID
        type_prefix: Optional prefix to filter tasks by type (e.g., "course", "paper", "slides")
    """
    tasks = list_tasks_for_workspace(workspace_id=workspace_id)
    latest_completed = None
    for task in tasks:
        task_type = task.type if hasattr(task, "type") else task.get("type")
        task_status = task.status if hasattr(task, "status") else task.get("status")
        if not task_type or not task_type.startswith("generate_"):
            continue
        # Filter by type prefix if specified
        if type_prefix:
            action_type = task_type.replace("generate_", "")
            if not action_type.startswith(type_prefix):
                continue
        payload_json = task.payload_json if hasattr(task, "payload_json") else task.get("payload_json")
        title = None
        if payload_json:
            try:
                payload = json.loads(payload_json)
                title = (payload.get("payload") or {}).get("title")
            except json.JSONDecodeError:
                title = None
        task_info = {
            "id": task.id if hasattr(task, "id") else task.get("id"),
            "type": task_type.replace("generate_", ""),
            "status": task_status,
            "progress": task.progress if hasattr(task, "progress") else task.get("progress"),
            "error": task.error if hasattr(task, "error") else task.get("error"),
            "title": title or task_type,
            "updated_at": task.updated_at if hasattr(task, "updated_at") else task.get("updated_at"),
        }
        if task_status in {"queued", "running"}:
            return task_info
        if latest_completed is None:
            latest_completed = task_info
    return latest_completed


def render_create_page(
    *,
    main_col: st.delta_generator.DeltaGenerator,
    inspector_col: st.delta_generator.DeltaGenerator,
    workspace_id: str | None,
    api_adapter: ApiModeAdapter,
) -> None:
    with main_col:
        st.markdown(f"## {t('create_title', workspace_id)}")
        st.caption(t("create_caption", workspace_id))

        if not workspace_id:
            st.info(t("create_select_project", workspace_id))
            return

        locked, lock_msg = running_task_summary(workspace_id)
        if lock_msg:
            st.info(lock_msg)
        docs = list_documents(workspace_id)
        doc_map = {doc["id"]: doc["filename"] for doc in docs}
        course_docs = [doc for doc in docs if doc.get("doc_type") == "course"]
        paper_docs = [doc for doc in docs if doc.get("doc_type") == "paper"]
        slides_docs = sorted(
            docs,
            key=lambda doc: {"course": 0, "paper": 1, "other": 2}.get(
                doc.get("doc_type") or "other", 2
            ),
        )
        ready, reason = llm_ready(
            st.session_state.get("llm_base_url", ""),
            st.session_state.get("llm_model", ""),
            st.session_state.get("llm_api_key", ""),
        )
        if st.session_state.get("api_mode") == "api":
            ready = True
            reason = ""

        tab_keys = ["course", "paper", "presentation"]
        if "create_tab" not in st.session_state:
            st.session_state["create_tab"] = "course"
        st.radio(
            t("create_tabs", workspace_id),
            options=tab_keys,
            index=tab_keys.index(st.session_state.get("create_tab", "course"))
            if st.session_state.get("create_tab", "course") in tab_keys
            else 0,
            format_func=lambda value: t(f"{value}_tab", workspace_id),
            horizontal=True,
            label_visibility="collapsed",
            key="create_tab_radio",
            on_change=lambda: st.session_state.update({"create_tab": st.session_state["create_tab_radio"]}),
        )
        selected_tab = st.session_state.get("create_tab", "course")

        if selected_tab == "course":
            section_title(t("step1_select_or_create_course", workspace_id))
            courses = list_courses(workspace_id)
            course_options = {course["name"]: course["id"] for course in courses}
            selected_course_id = None
            selected_course_name = None
            if course_options:
                selected_course_name = st.selectbox(
                    t("course_label", workspace_id),
                    options=list(course_options.keys()),
                    key="create_course_select",
                    help=t("course_label_help", workspace_id),
                )
                selected_course_id = course_options[selected_course_name]
            new_course_name = st.text_input(
                t("new_course_name", workspace_id),
                key="create_course_name",
                help=t("new_course_name_help", workspace_id),
            )
            if st.button(t("create_course", workspace_id), disabled=not new_course_name.strip()):
                selected_course_id = create_course(
                    workspace_id=workspace_id,
                    name=new_course_name.strip(),
                )
                selected_course_name = new_course_name.strip()
                st.success(t("course_created", workspace_id))

            linked_docs: list[dict] = []
            if selected_course_id:
                linked_docs = list_course_documents(selected_course_id)
                st.caption(
                    t("linked_pdfs_count", workspace_id).format(count=len(linked_docs))
                )
                if linked_docs:
                    st.write([doc["filename"] for doc in linked_docs])

            section_title(t("step2_link_documents", workspace_id))
            if not course_docs:
                st.info(t("import_course_docs", workspace_id))
            else:
                selected_docs = st.multiselect(
                    t("select_lecture_pdfs", workspace_id),
                    options=[doc["id"] for doc in course_docs],
                    format_func=lambda doc_id: doc_map.get(doc_id, doc_id),
                    key="create_course_docs",
                    help=t("select_lecture_help", workspace_id),
                )
                if st.button(
                    t("link_documents_to_course", workspace_id),
                    disabled=locked or not selected_course_id or not selected_docs,
                    help=lock_msg or None,
                ):
                    for doc_id in selected_docs:
                        try:
                            link_document(course_id=selected_course_id, doc_id=doc_id)
                        except Exception as exc:
                            st.error(str(exc))
                    st.success(t("documents_linked", workspace_id))

            section_title(t("step3_generate", workspace_id))
            retrieval_mode = _auto_retrieval_mode(workspace_id)

            # Course Overview
            with st.expander(t("course_overview", workspace_id), expanded=False):
                st.caption(t("course_overview_help", workspace_id))
                if st.button(
                    t("generate_overview_btn", workspace_id),
                    disabled=locked or not ready or not selected_course_id or not linked_docs,
                    help=lock_msg or reason,
                    key="btn_course_overview",
                ):
                    task_id = enqueue_generate_task(
                        workspace_id=workspace_id,
                        action_type="course_overview",
                        payload={
                            "workspace_id": workspace_id,
                            "course_id": selected_course_id,
                            "retrieval_mode": retrieval_mode,
                            "title": selected_course_name,
                        },
                        api_mode=st.session_state.get("api_mode", "direct"),
                        api_base_url=st.session_state.get(
                            "api_base_url", "http://127.0.0.1:8000"
                        ),
                    )
                    run_task_in_background(task_id)
                    st.success(t("task_queued", workspace_id))

            # Cheat Sheet
            with st.expander(t("cheat_sheet", workspace_id), expanded=False):
                st.caption(t("cheat_sheet_help", workspace_id))
                if st.button(
                    t("generate_cheatsheet_btn", workspace_id),
                    disabled=locked or not ready or not selected_course_id or not linked_docs,
                    help=lock_msg or reason,
                    key="btn_course_cheatsheet",
                ):
                    task_id = enqueue_generate_task(
                        workspace_id=workspace_id,
                        action_type="course_cheatsheet",
                        payload={
                            "workspace_id": workspace_id,
                            "course_id": selected_course_id,
                            "retrieval_mode": retrieval_mode,
                            "title": selected_course_name,
                        },
                        api_mode=st.session_state.get("api_mode", "direct"),
                        api_base_url=st.session_state.get(
                            "api_base_url", "http://127.0.0.1:8000"
                        ),
                    )
                    run_task_in_background(task_id)
                    st.success(t("task_queued", workspace_id))

            # Knowledge Q&A (new feature)
            with st.expander(t("course_qa", workspace_id), expanded=False):
                st.caption(t("course_qa_help", workspace_id))
                course_question = st.text_area(
                    t("course_question_label", workspace_id),
                    key="create_course_question",
                    height=100,
                    placeholder=t("course_question_placeholder", workspace_id),
                    help=t("course_question_help", workspace_id),
                )
                if st.button(
                    t("answer_question_btn", workspace_id),
                    disabled=locked
                    or not ready
                    or not selected_course_id
                    or not linked_docs
                    or not course_question.strip(),
                    help=lock_msg or reason,
                    key="btn_course_qa",
                ):
                    task_id = enqueue_generate_task(
                        workspace_id=workspace_id,
                        action_type="course_qa",
                        payload={
                            "workspace_id": workspace_id,
                            "course_id": selected_course_id,
                            "question": course_question.strip(),
                            "retrieval_mode": retrieval_mode,
                            "title": selected_course_name,
                        },
                        api_mode=st.session_state.get("api_mode", "direct"),
                        api_base_url=st.session_state.get(
                            "api_base_url", "http://127.0.0.1:8000"
                        ),
                    )
                    run_task_in_background(task_id)
                    st.success(t("task_queued", workspace_id))

            # Explain Selection
            with st.expander(t("explain_selection", workspace_id), expanded=False):
                st.caption(t("explain_selection_help", workspace_id))
                explain_options = ["concept", "proof", "example", "summary"]
                explain_mode = st.selectbox(
                    t("explain_mode", workspace_id),
                    options=explain_options,
                    key="create_course_explain_mode",
                    format_func=lambda value: t(f"explain_mode_{value}", workspace_id),
                    help=t("explain_mode_help", workspace_id),
                )
                selection = st.text_area(
                    t("selection_to_explain", workspace_id),
                    key="create_course_selection",
                    height=120,
                    help=t("selection_help", workspace_id),
                )
                if st.button(
                    t("explain_selection_btn", workspace_id),
                    disabled=locked
                    or not ready
                    or not selected_course_id
                    or not linked_docs
                    or not selection.strip(),
                    help=lock_msg or reason,
                    key="btn_course_explain",
                ):
                    task_id = enqueue_generate_task(
                        workspace_id=workspace_id,
                        action_type="course_explain",
                        payload={
                            "workspace_id": workspace_id,
                            "course_id": selected_course_id,
                            "selection": selection.strip(),
                            "mode": explain_mode,
                            "retrieval_mode": retrieval_mode,
                            "title": selected_course_name,
                        },
                        api_mode=st.session_state.get("api_mode", "direct"),
                        api_base_url=st.session_state.get(
                            "api_base_url", "http://127.0.0.1:8000"
                        ),
                    )
                    run_task_in_background(task_id)
                    st.success(t("task_queued", workspace_id))

        if selected_tab == "paper":
            if not paper_docs:
                st.info(t("import_papers_to_continue", workspace_id))
            else:
                # Single paper card generation
                with st.expander(t("paper_card_section", workspace_id), expanded=True):
                    st.caption(t("paper_card_help", workspace_id))
                    selected_doc = st.selectbox(
                        t("paper_source", workspace_id),
                        options=[doc["id"] for doc in paper_docs],
                        format_func=lambda doc_id: doc_map.get(doc_id, doc_id),
                        key="create_paper_doc",
                        help=t("paper_source_help", workspace_id),
                    )
                    if st.button(
                        t("generate_paper_card", workspace_id),
                        disabled=locked or not ready,
                        help=lock_msg or reason,
                    ):
                        task_id = enqueue_generate_task(
                            workspace_id=workspace_id,
                            action_type="paper_card",
                            payload={
                                "workspace_id": workspace_id,
                                "doc_id": selected_doc,
                                "retrieval_mode": _auto_retrieval_mode(workspace_id),
                                "title": doc_map.get(selected_doc, ""),
                            },
                            api_mode=st.session_state.get("api_mode", "direct"),
                            api_base_url=st.session_state.get(
                                "api_base_url", "http://127.0.0.1:8000"
                            ),
                        )
                        run_task_in_background(task_id)
                        st.success(t("task_queued", workspace_id))

                # Multi-paper aggregation
                with st.expander(t("paper_aggregate_section", workspace_id), expanded=False):
                    st.caption(t("paper_aggregate_help", workspace_id))
                    multi_docs = st.multiselect(
                        t("select_papers_to_compare", workspace_id),
                        options=[doc["id"] for doc in paper_docs],
                        format_func=lambda doc_id: doc_map.get(doc_id, doc_id),
                        key="create_paper_compare_docs",
                        help=t("select_papers_help", workspace_id),
                    )
                    question = st.text_input(
                        t("aggregation_question", workspace_id),
                        key="create_paper_question",
                        placeholder=t("aggregation_question_placeholder", workspace_id),
                        help=t("aggregation_question_help", workspace_id),
                    )
                    if st.button(
                        t("aggregate_papers", workspace_id),
                        disabled=locked or not ready or len(multi_docs) < 2 or not question.strip(),
                        help=t("aggregate_button_help", workspace_id) if len(multi_docs) < 2 else (lock_msg or reason),
                    ):
                        task_id = enqueue_generate_task(
                            workspace_id=workspace_id,
                            action_type="paper_aggregate",
                            payload={
                                "workspace_id": workspace_id,
                                "doc_ids": multi_docs,
                                "question": question.strip(),
                                "retrieval_mode": _auto_retrieval_mode(workspace_id),
                                "title": question.strip(),
                            },
                            api_mode=st.session_state.get("api_mode", "direct"),
                            api_base_url=st.session_state.get(
                                "api_base_url", "http://127.0.0.1:8000"
                            ),
                        )
                        run_task_in_background(task_id)
                        st.success(t("task_queued", workspace_id))

        if selected_tab == "presentation":
            section_title(t("step1_choose_source", workspace_id))
            if not slides_docs:
                st.info(t("import_docs_for_slides", workspace_id))
            else:
                doc_type_groups = {"course": [], "paper": [], "other": []}
                for doc in slides_docs:
                    dtype = doc.get("doc_type") or "other"
                    doc_type_groups.get(dtype, doc_type_groups["other"]).append(doc)
                if "slides_source_type" not in st.session_state:
                    st.session_state["slides_source_type"] = "all"
                st.radio(
                    t("doc_type_filter", workspace_id),
                    options=["all", "course", "paper", "other"],
                    index=["all", "course", "paper", "other"].index(st.session_state.get("slides_source_type", "all")),
                    horizontal=True,
                    format_func=lambda v: t(f"doc_type_{v}", workspace_id) if v != "all" else t("all_docs", workspace_id),
                    key="slides_source_type_radio",
                    on_change=lambda: st.session_state.update({"slides_source_type": st.session_state["slides_source_type_radio"]}),
                    help=t("slides_source_filter_help", workspace_id),
                )
                source_type = st.session_state.get("slides_source_type", "all")
                selected_doc = None
                if source_type == "all":
                    filtered_docs = slides_docs
                    if filtered_docs:
                        selected_doc = st.selectbox(
                            t("slides_source", workspace_id),
                            options=[doc["id"] for doc in filtered_docs],
                            format_func=lambda doc_id: doc_map.get(doc_id, doc_id),
                            key="create_slides_doc_all",
                            help=t("slides_source_help", workspace_id),
                        )
                elif source_type == "course":
                    courses = list_courses(workspace_id)
                    course_options = {course["name"]: course["id"] for course in courses}
                    course_filter = st.selectbox(
                        t("filter_by_course", workspace_id),
                        options=["all_course_docs"] + list(course_options.keys()),
                        format_func=lambda v: t("all_course_docs_label", workspace_id) if v == "all_course_docs" else v,
                        key="create_slides_course_filter",
                        help=t("course_filter_help", workspace_id),
                    )
                    if course_filter == "all_course_docs":
                        filtered_docs = doc_type_groups.get("course", [])
                    else:
                        course_id = course_options.get(course_filter)
                        linked_docs = list_course_documents(course_id) if course_id else []
                        linked_ids = {doc["id"] for doc in linked_docs}
                        filtered_docs = [doc for doc in doc_type_groups.get("course", []) if doc["id"] in linked_ids]
                    if filtered_docs:
                        selected_doc = st.selectbox(
                            t("slides_source", workspace_id),
                            options=[doc["id"] for doc in filtered_docs],
                            format_func=lambda doc_id: doc_map.get(doc_id, doc_id),
                            key="create_slides_doc_course",
                            help=t("slides_source_help", workspace_id),
                        )
                    else:
                        st.caption(t("no_docs_in_category", workspace_id))
                else:
                    filtered_docs = doc_type_groups.get(source_type, [])
                    if filtered_docs:
                        selected_doc = st.selectbox(
                            t("slides_source", workspace_id),
                            options=[doc["id"] for doc in filtered_docs],
                            format_func=lambda doc_id: doc_map.get(doc_id, doc_id),
                            key=f"create_slides_doc_{source_type}",
                            help=t("slides_source_help", workspace_id),
                        )
                    else:
                        st.caption(t("no_docs_in_category", workspace_id))
                duration = st.slider(
                    t("duration_minutes", workspace_id),
                    min_value=1,
                    max_value=30,
                    value=10,
                    step=1,
                    help=t("duration_help", workspace_id),
                )
                if selected_doc and st.button(
                    t("generate_slides", workspace_id),
                    disabled=locked or not ready,
                    help=lock_msg or reason,
                ):
                    task_id = enqueue_generate_task(
                        workspace_id=workspace_id,
                        action_type="slides",
                        payload={
                            "workspace_id": workspace_id,
                            "doc_id": selected_doc,
                            "duration": str(duration),
                            "retrieval_mode": _auto_retrieval_mode(workspace_id),
                            "title": doc_map.get(selected_doc, ""),
                        },
                        api_mode=st.session_state.get("api_mode", "direct"),
                        api_base_url=st.session_state.get(
                            "api_base_url", "http://127.0.0.1:8000"
                        ),
                    )
                    run_task_in_background(task_id)
                    st.success(t("task_queued", workspace_id))

        # Filter task and output by selected tab
        task_type_prefix = {
            "course": "course",
            "paper": "paper",
            "presentation": "slides",
        }.get(selected_tab, None)
        latest_task = _latest_generate_task(workspace_id=workspace_id, type_prefix=task_type_prefix)
        if latest_task:
            st.divider()
            st.markdown(f"### {t('generation_status', workspace_id)}")
            status_label = t(f"task_status_{latest_task['status']}", workspace_id)
            st.caption(f"{latest_task['title']} · {latest_task['type']} · {status_label}")
            if latest_task["status"] in {"queued", "running"}:
                progress_value = latest_task.get("progress")
                if progress_value is None:
                    progress_value = 0.0
                progress_value = float(progress_value)
                if progress_value > 1:
                    progress_value = progress_value / 100
                st.progress(max(0.0, min(1.0, progress_value)))
            elif latest_task["status"] == "succeeded":
                st.success(t("task_completed", workspace_id))
            elif latest_task["status"] == "failed":
                st.error(t("task_failed", workspace_id))
                if latest_task.get("error"):
                    st.caption(latest_task["error"])
            elif latest_task["status"] == "cancelled":
                st.warning(t("task_cancelled", workspace_id))

        st.divider()
        st.markdown(f"### {t('latest_output', workspace_id)}")
        activity = list_recent_activity(workspace_id, limit=20)
        desired_prefix = {
            "course": "generate_course_",
            "paper": "generate_paper_",
            "presentation": "generate_slides",
        }.get(selected_tab, "")
        source_label = {
            "course": t("course_tab", workspace_id),
            "paper": t("paper_tab", workspace_id),
            "presentation": t("presentation_tab", workspace_id),
        }.get(selected_tab, selected_tab or "-")
        match = next(
            (entry for entry in activity if entry["type"].startswith(desired_prefix)),
            None,
        )
        if not match:
            st.caption(t("no_recent_activity", workspace_id))
        else:
            output_ref = match.get("output_ref")
            try:
                ref = json.loads(output_ref) if output_ref else {}
            except json.JSONDecodeError:
                ref = {"asset_version_id": output_ref}
            version_id = ref.get("asset_version_id")
            if version_id:
                view = read_version_by_id(version_id)
                st.caption(
                    f"{_format_time(match['created_at'])} · {source_label} · {match.get('title') or match['type']}"
                )
                citations = citations_from_hits_json(view.version.hits_json)
                render_answer_with_citations(
                    text=view.content,
                    citations=citations,
                    workspace_id=workspace_id,
                )
                st.download_button(
                    t("download_output", workspace_id),
                    data=view.content,
                    file_name=f"{match['type']}.md",
                )
                if st.button(t("open_recent_activity", workspace_id)):
                    st.session_state["active_nav"] = "Tools"
                    st.session_state["tools_tab"] = "recent_activity"
                    st.session_state["recent_activity_selected_id"] = match["id"]
                    st.rerun()
            else:
                st.caption(t("no_recent_activity", workspace_id))

    with inspector_col:
        if not workspace_id:
            return
        render_inspector(
            status={
                t("project", workspace_id): workspace_id,
                t("retrieval_label", workspace_id): _auto_retrieval_mode(workspace_id),
            },
            citations=None,
        )

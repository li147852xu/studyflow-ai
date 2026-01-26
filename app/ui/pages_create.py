from __future__ import annotations

import streamlit as st

from app.ui.components import render_inspector, section_title
from app.ui.i18n import t
from core.ui_state.guards import llm_ready
from service.api_mode_adapter import ApiModeAdapter
from service.course_service import (
    create_course,
    link_document,
    list_course_documents,
    list_courses,
)
from service.document_service import list_documents
from service.retrieval_service import index_status
from app.ui.locks import running_task_summary
from service.tasks_service import enqueue_generate_task, run_task_in_background


def _auto_retrieval_mode(workspace_id: str) -> str:
    status = index_status(workspace_id)
    if status.get("vector_count", 0) > 0:
        return "hybrid"
    return "bm25"


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
        selected_tab = st.radio(
            t("create_tabs", workspace_id),
            options=tab_keys,
            index=tab_keys.index(st.session_state.get("create_tab", "course"))
            if st.session_state.get("create_tab", "course") in tab_keys
            else 0,
            format_func=lambda value: t(f"{value}_tab", workspace_id),
            horizontal=True,
            label_visibility="collapsed",
        )
        st.session_state["create_tab"] = selected_tab

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
                )
                selected_course_id = course_options[selected_course_name]
            new_course_name = st.text_input(t("new_course_name", workspace_id), key="create_course_name")
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
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button(
                    t("course_overview", workspace_id),
                    disabled=locked or not ready or not selected_course_id or not linked_docs,
                    help=lock_msg or reason,
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
            with col_b:
                if st.button(
                    t("cheat_sheet", workspace_id),
                    disabled=locked or not ready or not selected_course_id or not linked_docs,
                    help=lock_msg or reason,
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
            with col_c:
                explain_options = ["concept", "proof", "example", "summary"]
                explain_mode = st.selectbox(
                    t("explain_mode", workspace_id),
                    options=explain_options,
                    key="create_course_explain_mode",
                    format_func=lambda value: t(f"explain_mode_{value}", workspace_id),
                )
                selection = st.text_area(
                    t("selection_to_explain", workspace_id),
                    key="create_course_selection",
                    height=120,
                )
                if st.button(
                    t("explain_selection", workspace_id),
                    disabled=locked
                    or not ready
                    or not selected_course_id
                    or not linked_docs
                    or not selection.strip(),
                    help=lock_msg or reason,
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
            section_title(t("step1_pick_paper", workspace_id))
            if not paper_docs:
                st.info(t("import_papers_to_continue", workspace_id))
            else:
                selected_doc = st.selectbox(
                    t("paper_source", workspace_id),
                    options=[doc["id"] for doc in paper_docs],
                    format_func=lambda doc_id: doc_map.get(doc_id, doc_id),
                    key="create_paper_doc",
                )
                section_title(t("step2_generate", workspace_id))
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(
                        t("paper_card", workspace_id),
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
                with col_b:
                    question = st.text_input(t("comparison_question", workspace_id), key="create_paper_question")
                    multi_docs = st.multiselect(
                        t("compare_papers", workspace_id),
                        options=[doc["id"] for doc in paper_docs],
                        format_func=lambda doc_id: doc_map.get(doc_id, doc_id),
                        key="create_paper_compare_docs",
                    )
                    if st.button(
                        t("aggregate_papers", workspace_id),
                        disabled=locked or not ready or not multi_docs or not question.strip(),
                        help=lock_msg or reason,
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
                selected_doc = st.selectbox(
                    t("slides_source", workspace_id),
                    options=[doc["id"] for doc in slides_docs],
                    format_func=lambda doc_id: doc_map.get(doc_id, doc_id),
                    key="create_slides_doc",
                )
                duration = st.selectbox(
                    t("duration_minutes", workspace_id),
                    options=["3", "5", "10", "20"],
                    index=2,
                )
                if st.button(
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
                            "duration": duration,
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

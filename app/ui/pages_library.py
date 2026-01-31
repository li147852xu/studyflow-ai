from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.adapters import facade
from app.ui.components import card_footer, card_header, render_inspector, run_with_progress, section_title
from app.ui.i18n import t
from app.ui.locks import running_task_summary
from core.ingest.pdf_reader import read_pdf
from core.parsing.metadata import PaperMetadata, extract_metadata
from core.plugins.base import PluginContext
from core.plugins.registry import get_plugin, load_builtin_plugins
from service.course_service import link_document, list_courses
from service.document_service import list_documents
from service.paper_service import ensure_paper
from service.tasks_service import enqueue_index_task, list_tasks_for_workspace, run_task_in_background


def _doc_status(chunk_count: int, vector_ready: bool, running: bool) -> str:
    if running:
        return t("status_processing")
    if chunk_count == 0:
        return t("status_imported")
    return t("status_search_ready") if vector_ready else t("status_indexing")


def _collect_running_tasks(workspace_id: str) -> bool:
    try:
        tasks = list_tasks_for_workspace(workspace_id=workspace_id)
        return any(
            (task["status"] if isinstance(task, dict) else task.status)
            in {"queued", "running"}
            for task in tasks
        )
    except Exception:
        return False


def _classify_document(doc: dict) -> tuple[str, PaperMetadata | None]:
    filename = (doc.get("filename") or "").lower()
    course_keywords = ("lecture", "week", "chapter", "lesson", "slides", "course", "seminar")
    if any(keyword in filename for keyword in course_keywords):
        return "course", None

    path = doc.get("path")
    file_type = (doc.get("file_type") or "").lower()
    if path and file_type == "pdf":
        try:
            parsed = read_pdf(Path(path))
            text = "\n".join(page.text for page in parsed.pages[:2])
            metadata = extract_metadata(text)
            if metadata and metadata.title and metadata.title != "unknown":
                return "paper", metadata
        except Exception:
            pass

    return "other", None


def _infer_doc_type_from_name(name: str) -> str:
    lower = name.lower()
    if any(keyword in lower for keyword in ["lecture", "week", "chapter", "lesson", "course", "slides"]):
        return "course"
    if any(keyword in lower for keyword in ["paper", "arxiv", "doi", "journal", "proceedings"]):
        return "paper"
    return "other"


def render_library_page(
    *,
    main_col: st.delta_generator.DeltaGenerator,
    inspector_col: st.delta_generator.DeltaGenerator,
    workspace_id: str | None,
) -> None:
    with main_col:
        st.markdown(f"## {t('library_title', workspace_id)}")
        st.caption(t("library_caption", workspace_id))

        if not workspace_id:
            st.info(t("library_select_project", workspace_id))
            return

        status_result = facade.workspace_status(workspace_id)
        status_payload = status_result.data if status_result.ok else {}
        if status_payload:
            cols = st.columns(4)
            cols[0].metric(t("documents", workspace_id), status_payload.get("doc_count", 0))
            cols[1].metric(t("chunks", workspace_id), status_payload.get("chunk_count", 0))
            cols[2].metric(t("vector_items", workspace_id), status_payload.get("vector_count", 0))
            cols[3].metric(
                "BM25",
                t("bm25_ready", workspace_id)
                if status_payload.get("bm25_exists")
                else t("bm25_missing", workspace_id),
            )

        st.divider()
        locked, lock_msg = running_task_summary(workspace_id)
        if lock_msg:
            st.info(lock_msg)

        with st.expander(t("import_section", workspace_id), expanded=False):
            card_header(
                t("import_auto_title", workspace_id),
                t("import_auto_subtitle_library", workspace_id),
            )
            default_type = st.session_state.get("library_doc_type") or st.session_state.get(
                "last_doc_type", "course"
            )
            doc_type = st.selectbox(
                t("doc_type_label", workspace_id),
                options=["course", "paper", "other"],
                index=["course", "paper", "other"].index(
                    default_type if default_type in ["course", "paper", "other"] else "course"
                ),
                format_func=lambda value: t(f"doc_type_{value}", workspace_id),
                help=t("doc_type_help", workspace_id),
            )
            st.session_state["library_doc_type"] = doc_type
            if "library_import_source" not in st.session_state:
                st.session_state["library_import_source"] = "upload"
            st.radio(
                t("import_source_label", workspace_id),
                options=["upload", "folder", "arxiv", "zotero"],
                index=["upload", "folder", "arxiv", "zotero"].index(st.session_state.get("library_import_source", "upload")),
                format_func=lambda value: t(f"import_source_{value}", workspace_id),
                horizontal=True,
                key="library_import_source_radio",
                on_change=lambda: st.session_state.update({"library_import_source": st.session_state["library_import_source_radio"]}),
                help=t("import_source_help", workspace_id),
            )
            source = st.session_state.get("library_import_source", "upload")
            before_ids = {doc["id"] for doc in list_documents(workspace_id)}
            if source == "upload":
                uploads = st.file_uploader(
                    t("upload_documents", workspace_id),
                    type=["pdf", "txt", "md", "docx", "pptx", "html", "htm", "png", "jpg", "jpeg"],
                    accept_multiple_files=True,
                    help=t("upload_documents_help", workspace_id),
                )
                if uploads:
                    suggestion = _infer_doc_type_from_name(uploads[0].name)
                    st.caption(
                        t("doc_type_suggested", workspace_id).format(
                            value=t(f"doc_type_{suggestion}", workspace_id)
                        )
                    )
                if st.button(
                    t("import_now", workspace_id),
                    disabled=locked or not uploads,
                    help=lock_msg or None,
                ):
                    for file in uploads:
                        result = facade.import_and_process(
                            workspace_id=workspace_id,
                            filename=file.name,
                            data=file.getvalue(),
                            ocr_mode=st.session_state.get("ocr_mode", "auto"),
                            ocr_threshold=int(st.session_state.get("ocr_threshold", 50)),
                            doc_type=doc_type,
                        )
                        if result.ok:
                            st.session_state["last_doc_type"] = doc_type
                            st.success(t("imported_doc", workspace_id).format(name=file.name))
                        else:
                            st.error(result.error or t("import_failed_error", workspace_id))
            elif source == "zotero":
                data_dir = st.text_input(
                    t("zotero_data_dir", workspace_id),
                    key="library_zotero_dir",
                    placeholder=t("zotero_path_placeholder", workspace_id),
                    help=t("zotero_path_help", workspace_id),
                )
                st.caption(
                    t("doc_type_suggested", workspace_id).format(
                        value=t("doc_type_paper", workspace_id)
                    )
                )
                if st.button(
                    t("import_from_zotero", workspace_id),
                    disabled=locked or not data_dir.strip(),
                    help=lock_msg or None,
                ):
                    def _work() -> None:
                        load_builtin_plugins()
                        plugin = get_plugin("importer_zotero")
                        result = plugin.run(
                            PluginContext(
                                workspace_id=workspace_id,
                                args={
                                    "data_dir": data_dir.strip(),
                                    "ocr_mode": st.session_state.get("ocr_mode", "auto"),
                                    "ocr_threshold": int(st.session_state.get("ocr_threshold", 50)),
                                    "copy": True,
                                    "doc_type": doc_type,
                                },
                            )
                        )
                        if result.ok:
                            index_task_id = enqueue_index_task(workspace_id=workspace_id, reset=False)
                            run_task_in_background(index_task_id)
                            st.session_state["last_doc_type"] = doc_type
                            st.success(result.message)
                        else:
                            raise RuntimeError(result.message)

                    run_with_progress(
                        label=t("importing_processing", workspace_id),
                        work=_work,
                        success_label=t("import_complete", workspace_id),
                        error_label=t("import_failed", workspace_id),
                        use_status=False,
                    )
            elif source == "folder":
                folder = st.text_input(
                    t("folder_path", workspace_id),
                    key="library_folder_path",
                    placeholder=t("folder_path_placeholder", workspace_id),
                    help=t("folder_path_help", workspace_id),
                )
                st.caption(
                    t("doc_type_suggested", workspace_id).format(
                        value=t(f"doc_type_{doc_type}", workspace_id)
                    )
                )
                if st.button(
                    t("import_from_folder", workspace_id),
                    disabled=locked or not folder.strip(),
                    help=lock_msg or None,
                ):
                    def _work() -> None:
                        load_builtin_plugins()
                        plugin = get_plugin("importer_folder_sync")
                        result = plugin.run(
                            PluginContext(
                                workspace_id=workspace_id,
                                args={
                                    "path": folder.strip(),
                                    "ocr_mode": st.session_state.get("ocr_mode", "auto"),
                                    "ocr_threshold": int(st.session_state.get("ocr_threshold", 50)),
                                    "copy": True,
                                    "doc_type": doc_type,
                                },
                            )
                        )
                        if result.ok:
                            index_task_id = enqueue_index_task(workspace_id=workspace_id, reset=False)
                            run_task_in_background(index_task_id)
                            st.session_state["last_doc_type"] = doc_type
                            st.success(result.message)
                        else:
                            raise RuntimeError(result.message)

                    run_with_progress(
                        label=t("importing_processing", workspace_id),
                        work=_work,
                        success_label=t("import_complete", workspace_id),
                        error_label=t("import_failed", workspace_id),
                        use_status=False,
                    )
            else:
                source_value = st.text_input(
                    t("source_id_label", workspace_id),
                    key="library_source",
                    placeholder=t("source_id_placeholder", workspace_id),
                    help=t("source_id_help", workspace_id),
                )
                st.caption(
                    t("doc_type_suggested", workspace_id).format(
                        value=t("doc_type_paper", workspace_id)
                    )
                )
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(
                        t("import_from_arxiv", workspace_id),
                        disabled=locked or not source_value.strip(),
                        help=lock_msg or None,
                    ):
                        def _work() -> None:
                            load_builtin_plugins()
                            plugin = get_plugin("importer_arxiv")
                            result = plugin.run(
                                PluginContext(
                                    workspace_id=workspace_id,
                                    args={"arxiv_id": source_value.strip(), "ocr_mode": "auto", "doc_type": doc_type},
                                )
                            )
                            if result.ok:
                                index_task_id = enqueue_index_task(workspace_id=workspace_id, reset=False)
                                run_task_in_background(index_task_id)
                                st.session_state["last_doc_type"] = doc_type
                                st.success(result.message)
                            else:
                                raise RuntimeError(result.message)

                        run_with_progress(
                            label=t("importing_processing", workspace_id),
                            work=_work,
                            success_label=t("import_complete", workspace_id),
                            error_label=t("import_failed", workspace_id),
                            use_status=False,
                        )
                with col2:
                    if st.button(
                        t("import_from_doi", workspace_id),
                        disabled=locked or not source_value.strip(),
                        help=lock_msg or None,
                    ):
                        def _work() -> None:
                            load_builtin_plugins()
                            plugin = get_plugin("importer_doi")
                            result = plugin.run(
                                PluginContext(
                                    workspace_id=workspace_id,
                                    args={"doi": source_value.strip(), "ocr_mode": "auto", "doc_type": doc_type},
                                )
                            )
                            if result.ok:
                                index_task_id = enqueue_index_task(workspace_id=workspace_id, reset=False)
                                run_task_in_background(index_task_id)
                                st.session_state["last_doc_type"] = doc_type
                                st.success(result.message)
                            else:
                                raise RuntimeError(result.message)

                        run_with_progress(
                            label=t("importing_processing", workspace_id),
                            work=_work,
                            success_label=t("import_complete", workspace_id),
                            error_label=t("import_failed", workspace_id),
                            use_status=False,
                        )
                with col3:
                    if st.button(
                        t("import_from_url", workspace_id),
                        disabled=locked or not source_value.strip(),
                        help=lock_msg or None,
                    ):
                        def _work() -> None:
                            load_builtin_plugins()
                            plugin = get_plugin("importer_url")
                            result = plugin.run(
                                PluginContext(
                                    workspace_id=workspace_id,
                                    args={"url": source_value.strip(), "ocr_mode": "auto", "doc_type": doc_type},
                                )
                            )
                            if result.ok:
                                index_task_id = enqueue_index_task(workspace_id=workspace_id, reset=False)
                                run_task_in_background(index_task_id)
                                st.session_state["last_doc_type"] = doc_type
                                st.success(result.message)
                            else:
                                raise RuntimeError(result.message)

                        run_with_progress(
                            label=t("importing_processing", workspace_id),
                            work=_work,
                            success_label=t("import_complete", workspace_id),
                            error_label=t("import_failed", workspace_id),
                            use_status=False,
                        )
            card_footer()

            after_docs = list_documents(workspace_id)
            new_docs = [doc for doc in after_docs if doc["id"] not in before_ids]
            if new_docs:
                results = st.session_state.get("library_import_results", [])
                existing_ids = {item["doc_id"] for item in results}
                for doc in new_docs:
                    if doc["id"] in existing_ids:
                        continue
                    category, metadata = _classify_document(doc)
                    results.append(
                        {
                            "doc_id": doc["id"],
                            "filename": doc.get("filename") or "-",
                            "path": doc.get("path"),
                            "category": doc.get("doc_type") or category,
                            "metadata": metadata,
                        }
                    )
                st.session_state["library_import_results"] = results

        import_results = st.session_state.get("library_import_results", [])
        if import_results:
            st.markdown(f"### {t('import_attach_title', workspace_id)}")
            st.caption(t("classification_notes", workspace_id))
            courses = list_courses(workspace_id)
            course_options = {course["name"]: course["id"] for course in courses}
            attached_ids = st.session_state.get("library_attached_ids", set())
            for item in import_results:
                doc_id = item["doc_id"]
                filename = item["filename"]
                category = item["category"]
                metadata = item.get("metadata")
                if doc_id in attached_ids:
                    continue
                st.markdown(f"**{filename}**")
                st.caption(
                    t("import_classified_as", workspace_id).format(
                        category=t(f"category_{category}", workspace_id)
                    )
                )
                if category == "course":
                    if not course_options:
                        st.info(t("no_courses", workspace_id))
                    else:
                        selected_course = st.selectbox(
                            t(
                                "attach_course",
                                workspace_id,
                            ),
                            options=list(course_options.keys()),
                            index=0,
                            key=f"attach_course_{doc_id}",
                        )
                        if st.button(
                            t("attach_now", workspace_id),
                            key=f"attach_course_btn_{doc_id}",
                            disabled=locked,
                            help=lock_msg or None,
                        ):
                            try:
                                link_document(
                                    course_id=course_options[selected_course],
                                    doc_id=doc_id,
                                )
                                attached_ids.add(doc_id)
                                st.session_state["library_attached_ids"] = attached_ids
                                st.success(t("attached_success", workspace_id))
                            except Exception:
                                st.error(t("attach_failed", workspace_id))
                elif category == "paper":
                    if not metadata:
                        metadata = PaperMetadata(
                            title=filename, authors="unknown", year="unknown"
                        )
                    st.caption(
                        f"{metadata.title} · {metadata.authors} · {metadata.year}"
                    )
                    if st.button(
                        t("attach_now", workspace_id),
                        key=f"attach_paper_btn_{doc_id}",
                        disabled=locked,
                        help=lock_msg or None,
                    ):
                        try:
                            ensure_paper(
                                workspace_id=workspace_id,
                                doc_id=doc_id,
                                metadata=metadata,
                            )
                            attached_ids.add(doc_id)
                            st.session_state["library_attached_ids"] = attached_ids
                            st.success(t("attached_success", workspace_id))
                        except Exception:
                            st.error(t("attach_failed", workspace_id))
                else:
                    st.caption(t("doc_type_other_note", workspace_id))

            # Jump to Create button
            st.divider()
            if st.button(
                t("jump_to_create", workspace_id),
                help=t("jump_to_create_help", workspace_id),
            ):
                st.session_state["active_nav"] = "Create"
                st.rerun()

        toolbar = st.columns([2.6, 2, 1.4, 1.2])
        search = toolbar[0].text_input(
            t("search_documents", workspace_id),
            key="library_search",
            placeholder=t("search_documents_placeholder", workspace_id),
        )
        sort_choice = toolbar[1].selectbox(
            t("sort_by", workspace_id),
            options=[
                "created_desc",
                "created_asc",
                "filename_asc",
                "filename_desc",
                "size_asc",
                "size_desc",
            ],
            format_func=lambda value: t(f"sort_{value}", workspace_id),
            key="library_sort",
        )
        doc_type_filter = toolbar[2].selectbox(
            t("material_type", workspace_id),
            options=["all", "course", "paper", "other"],
            format_func=lambda value: t(f"doc_type_{value}", workspace_id)
            if value != "all"
            else t("all_types", workspace_id),
            key="library_doc_type_filter",
            help=t("material_type_help", workspace_id),
        )
        page_size = toolbar[3].selectbox(
            t("page_size", workspace_id),
            options=[5, 10, 20, 50],
            key="library_page_size",
        )

        sort_map = {
            "created_desc": ("created_at", "desc"),
            "created_asc": ("created_at", "asc"),
            "filename_asc": ("filename", "asc"),
            "filename_desc": ("filename", "desc"),
            "size_asc": ("size_bytes", "asc"),
            "size_desc": ("size_bytes", "desc"),
        }
        sort_by, sort_order = sort_map.get(sort_choice, ("created_at", "desc"))
        filter_signature = (search or "", doc_type_filter, sort_choice, page_size)
        if st.session_state.get("library_filter_signature") != filter_signature:
            st.session_state["library_filter_signature"] = filter_signature
            st.session_state["library_page"] = 1

        count_result = facade.count_documents_for_filter(
            workspace_id=workspace_id,
            doc_type=None if doc_type_filter == "all" else doc_type_filter,
            search=search,
        )
        total_docs = int(count_result.data or 0) if count_result.ok else 0
        if total_docs == 0:
            if search or doc_type_filter != "all":
                st.caption(t("no_docs_match", workspace_id))
            else:
                st.info(t("no_documents_yet", workspace_id))
            return

        total_pages = max(1, (total_docs + page_size - 1) // page_size)
        page = st.number_input(
            t("page_number", workspace_id),
            min_value=1,
            max_value=total_pages,
            value=min(st.session_state.get("library_page", 1), total_pages),
            step=1,
            key="library_page",
        )
        st.caption(
            t("page_summary", workspace_id).format(
                current=page, total=total_pages, count=total_docs
            )
        )
        offset = (page - 1) * page_size

        docs_result = facade.list_documents_with_tags(
            workspace_id,
            limit=page_size,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            doc_type=None if doc_type_filter == "all" else doc_type_filter,
            search=search,
        )
        if not docs_result.ok:
            st.error(docs_result.error or t("failed_load_documents", workspace_id))
            return
        docs = docs_result.data or []
        if not docs:
            st.caption(t("no_docs_match", workspace_id))
            return

        chunk_counts = facade.doc_chunk_counts(workspace_id)
        running = _collect_running_tasks(workspace_id)
        vector_ready = bool(
            status_payload
            and status_payload.get("vector_count", 0) >= status_payload.get("chunk_count", 0)
        )

        section_title(t("documents", workspace_id))
        options = {doc["id"]: doc for doc in docs}

        def _file_type_label(doc: dict) -> str:
            file_type = (doc.get("file_type") or "").lower()
            icons = {
                "pdf": "📄 PDF",
                "docx": "📝 DOCX",
                "pptx": "📊 PPTX",
                "txt": "🗒️ TXT",
                "md": "🧾 MD",
                "html": "🌐 HTML",
                "htm": "🌐 HTML",
                "png": "🖼️ IMG",
                "jpg": "🖼️ IMG",
                "jpeg": "🖼️ IMG",
            }
            return icons.get(file_type, file_type.upper() if file_type else "-")

        def _short_time(value: str | None) -> str:
            if not value:
                return "-"
            return value.replace("T", " ")[:16]

        for doc_id, doc in options.items():
            chunk_count = chunk_counts.get(doc_id, 0)
            status = _doc_status(chunk_count, vector_ready, running)
            pages = doc.get("page_count") or "-"
            row = st.columns([5.2, 1.5, 1.3], vertical_alignment="center")
            label = f"{doc['filename']}"
            if row[0].button(
                label,
                key=f"select_doc_{doc_id}",
                type="primary"
                if st.session_state.get("library_selected_doc") == doc_id
                else "secondary",
                use_container_width=True,
            ):
                st.session_state["library_selected_doc"] = doc_id
            row[0].caption(f"{status} · {pages} {t('pages_label', workspace_id)}")
            row[1].caption(_short_time(doc.get("created_at")))
            row[2].caption(_file_type_label(doc))
            st.divider()

        selected_doc_id = st.session_state.get("library_selected_doc")
        selected_doc = options.get(selected_doc_id) if selected_doc_id else None
        if selected_doc:
            st.markdown(f"#### {t('document_details', workspace_id)}")
            if selected_doc.get("summary"):
                st.caption(f"📝 {selected_doc['summary']}")
            st.write(
                {
                    t("filename", workspace_id): selected_doc["filename"],
                    t("doc_id", workspace_id): selected_doc["id"],
                    t("doc_type_label", workspace_id): selected_doc.get("doc_type") or "other",
                    t("source", workspace_id): selected_doc.get("source") or "-",
                    t("created", workspace_id): selected_doc.get("created_at", "")[:19],
                }
            )

    with inspector_col:
        if not workspace_id:
            return
        history_result = facade.recent_history(workspace_id=workspace_id, limit=10)
        render_inspector(
            status=status_payload,
            history=(history_result.data if history_result.ok else None),
        )
        selected_doc = st.session_state.get("library_selected_doc")
        if not selected_doc:
            return
        doc_result = facade.get_document_detail(selected_doc)
        if not doc_result.ok or not doc_result.data:
            st.caption(t("select_document_to_inspect", workspace_id))
            return
        doc = doc_result.data
        st.markdown(f"### {t('document', workspace_id)}")
        st.write(
            {
                t("filename", workspace_id): doc.get("filename"),
                t("path", workspace_id): doc.get("path"),
                t("pages", workspace_id): doc.get("page_count") or "-",
                t("doc_type_label", workspace_id): doc.get("doc_type") or "other",
                t("created", workspace_id): doc.get("created_at", "")[:19],
            }
        )
        # Document summary
        summary = doc.get("summary")
        if summary:
            st.info(f"**{t('summary_label', workspace_id)}**: {summary}")
        else:
            if st.button(t("generate_summary", workspace_id), key="generate_summary_btn"):
                from service.summary_service import SummaryError, generate_summary
                try:
                    generated = generate_summary(doc["id"])
                    st.success(f"{t('summary_label', workspace_id)}: {generated}")
                except SummaryError as exc:
                    st.error(str(exc))
        doc_type_value = doc.get("doc_type") or "other"
        new_doc_type = st.selectbox(
            t("doc_type_label", workspace_id),
            options=["course", "paper", "other"],
            index=["course", "paper", "other"].index(doc_type_value),
            format_func=lambda value: t(f"doc_type_{value}", workspace_id),
            key="library_doc_type_update",
        )
        if st.button(
            t("update_doc_type", workspace_id),
            disabled=locked or new_doc_type == doc_type_value,
            help=lock_msg or None,
        ):
            result = facade.update_document_type(doc_id=doc["id"], doc_type=new_doc_type)
            if result.ok:
                index_task_id = enqueue_index_task(
                    workspace_id=workspace_id,
                    reset=False,
                    doc_ids=[doc["id"]],
                )
                run_task_in_background(index_task_id)
                st.success(t("doc_type_updated", workspace_id))
            else:
                st.error(result.error or t("doc_type_update_failed", workspace_id))
        needs_rebuild = bool(
            status_payload
            and status_payload.get("vector_count", 0) != status_payload.get("chunk_count", 0)
        )
        with st.expander(t("actions", workspace_id), expanded=True):
            if needs_rebuild:
                if st.button(
                    t("rebuild_index", workspace_id),
                    disabled=locked,
                    help=lock_msg or None,
                ):
                    result = facade.rebuild_index(workspace_id=workspace_id)
                    if result.ok:
                        st.success(t("rebuild_index_queued", workspace_id))
                    else:
                        st.error(result.error or t("rebuild_index_failed", workspace_id))
            confirm_delete = st.checkbox(
                t("confirm_delete", workspace_id),
                key="library_confirm_delete",
            )
            if st.button(
                t("delete_document", workspace_id),
                disabled=locked or not confirm_delete,
                help=lock_msg or None,
            ):
                result = facade.delete_document(workspace_id=workspace_id, doc_id=doc["id"])
                if result.ok:
                    st.success(t("document_deleted", workspace_id))
                else:
                    st.error(result.error or t("delete_failed", workspace_id))

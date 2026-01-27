from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from app.ui import apply_theme, init_app_state
from app.ui.layout import render_main_columns, render_sidebar
from app.ui.pages_start import render_start_page
from app.ui.pages_library import render_library_page
from app.ui.pages_create import render_create_page
from app.ui.pages_tools import render_tools_page
from app.ui.pages_help import render_help_page
from app.ui.auto_refresh import maybe_auto_refresh, inject_auto_refresh
from app.components.dialogs import confirm_action
from app.components.inspector import (
    render_citations,
    render_download,
    render_metadata,
    render_asset_versions,
    render_run_info,
    render_section_title,
)
from app.components.shell import app_shell
from app.components.nav import render_nav
from app.components.library_panel import render_library_panel
from app.components.workflow_wizard import render_workflow_selector, render_workflow_steps
from app.components.tasks_center import render_tasks_center
from app.components.plugins_center import render_plugins_center
from app.components.settings_center import render_settings_center
from app.components.exports_center import render_exports_center
from app.components.diagnostics_center import render_diagnostics_center
from app.components.workbench_view import render_workbench_list
from core.config.loader import load_config, apply_profile, ConfigError
from core.ui_state.guards import llm_ready
from core.ui_state.storage import (
    add_history,
    clear_history,
    get_setting,
    list_history,
    set_setting,
)
from infra.db import get_workspaces_dir
from service.course_service import (
    create_course,
    link_document,
    list_course_documents,
    list_courses,
)
from service.document_service import list_documents
from service.ingest_service import IngestError
from service.paper_service import add_tags, list_papers, list_tags
from service.presentation_service import list_sources
from service.api_mode_adapter import ApiModeAdapter, ApiModeError
from service.coach_service import (
    clear_coach_sessions,
    list_coach_sessions,
    show_coach_session,
    start_coach,
    submit_coach,
)


def _ensure_retrieval_mode(workspace_id: str | None) -> str:
    default_mode = "vector"
    if workspace_id:
        stored = get_setting(workspace_id, "retrieval_mode")
        if stored:
            default_mode = stored
    st.session_state["retrieval_mode"] = default_mode
    return default_mode


def _set_nav(target: str) -> None:
    st.session_state["active_nav"] = target
    st.rerun()


def _api_adapter() -> ApiModeAdapter:
    return ApiModeAdapter(
        st.session_state.get("api_mode", "direct"),
        st.session_state.get("api_base_url", "http://127.0.0.1:8000"),
    )


def render_home(
    center: st.delta_generator.DeltaGenerator,
    right: st.delta_generator.DeltaGenerator,
    workspace_id: str,
) -> None:
    from app.components.nav import _index_status

    status = _index_status(workspace_id)
    with center:
        st.markdown("### Workspace overview")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Documents", status["documents"])
        col_b.metric("Chunks", status["chunks"])
        col_c.metric("Vector items", status["vector_index"])
        st.caption(f"BM25 index present: {status['bm25_index']}")

        st.divider()
        st.markdown("### Start here")
        st.write("1) Import PDFs → 2) Build Index → 3) Ask or Generate")
        if st.button("Go to Library"):
            _set_nav("Library")
        if st.button("Go to Workflows"):
            _set_nav("Workflows")

    with right:
        st.markdown("### Recent activity")
        history = list_history(workspace_id)[:5]
        if not history:
            st.caption("No history yet.")
        else:
            for entry in history:
                st.write(f"{entry['created_at']} · {entry['action_type']}")
                if entry.get("summary"):
                    st.caption(entry["summary"])
                if entry.get("preview"):
                    st.caption(entry["preview"][:180])


def render_library(
    left: st.delta_generator.DeltaGenerator,
    center: st.delta_generator.DeltaGenerator,
    right: st.delta_generator.DeltaGenerator,
    workspace_id: str,
) -> None:
    adapter = _api_adapter()
    render_library_panel(
        left=left,
        center=center,
        right=right,
        workspace_id=workspace_id,
        api_adapter=adapter,
        retrieval_mode=_ensure_retrieval_mode(workspace_id),
        api_mode=st.session_state.get("api_mode", "direct"),
    )


def render_workflows(
    left: st.delta_generator.DeltaGenerator,
    center: st.delta_generator.DeltaGenerator,
    right: st.delta_generator.DeltaGenerator,
    workspace_id: str,
) -> None:
    with left:
        workflow_key = render_workflow_selector()
    render_workflow_steps(center, workflow_key)
    if workflow_key == "courses":
        render_courses(left, center, right, workspace_id)
    elif workflow_key == "papers":
        render_papers(left, center, right, workspace_id)
    else:
        render_presentations(left, center, right, workspace_id)


def render_courses(left: st.delta_generator.DeltaGenerator, center: st.delta_generator.DeltaGenerator, right: st.delta_generator.DeltaGenerator, workspace_id: str) -> None:
    courses = list_courses(workspace_id)
    adapter = _api_adapter()
    with left:
        selected = render_workbench_list(
            title="Courses",
            items=courses,
            label_key="name",
            id_key="id",
            search_key="course_search",
            new_label="Course name",
            new_placeholder="e.g. CS229",
            create_callback=lambda name: create_course(workspace_id, name),
            empty_hint="No courses yet.",
            selection_state_key="selected_course_id",
        )
    if not selected:
        with center:
            st.info("Create or select a course to begin.")
        return

    course_id = selected["id"]
    linked_docs = list_course_documents(course_id)
    ready, reason = llm_ready(
        st.session_state.get("llm_base_url", ""),
        st.session_state.get("llm_model", ""),
        st.session_state.get("llm_api_key", ""),
    )
    if st.session_state.get("api_mode") == "api":
        ready = True
        reason = ""
    if st.session_state.get("api_mode") == "api":
        ready = True
        reason = ""
    if st.session_state.get("api_mode") == "api":
        ready = True
        reason = ""
    retrieval_mode = _ensure_retrieval_mode(workspace_id)

    with center:
        st.markdown("### Course workspace")
        st.caption(f"Selected course: {selected['name']}")

        st.markdown("#### Linked lecture PDFs")
        if not linked_docs:
            st.caption("No lecture PDFs linked yet.")
        else:
            for doc in linked_docs:
                st.write(f"- {doc['filename']} ({doc.get('page_count') or 0} pages)")

        st.markdown("#### Link existing document")
        docs = list_documents(workspace_id)
        doc_options = {doc["filename"]: doc["id"] for doc in docs}
        selected_doc = st.selectbox("Choose document", options=["(none)"] + list(doc_options.keys()))
        if selected_doc != "(none)" and st.button("Link to course"):
            link_document(course_id, doc_options[selected_doc])
            st.success("Document linked.")

        st.markdown("#### Upload new lecture PDF")
        upload = st.file_uploader("Upload PDF", type=["pdf"], key="course_upload")
        if st.button("Ingest & link", disabled=upload is None):
            try:
                result = adapter.ingest(
                    workspace_id=workspace_id,
                    filename=upload.name,
                    data=upload.getvalue(),
                    save_dir=get_workspaces_dir() / workspace_id / "uploads",
                    kind="document",
                    ocr_mode=st.session_state.get("ocr_mode", "off"),
                    ocr_threshold=int(st.session_state.get("ocr_threshold", 50)),
                )
                link_document(course_id, result["doc_id"])
                st.success("PDF ingested and linked.")
            except IngestError as exc:
                st.error(str(exc))
            except ApiModeError as exc:
                st.error(str(exc))
                if st.button("Switch to Direct Mode", key="api_switch_course_ingest"):
                    st.session_state["api_mode"] = "direct"
                    set_setting(None, "api_mode", "direct")

        st.divider()
        st.markdown("#### Actions")
        if st.button(
            "Generate COURSE_OVERVIEW",
            disabled=not ready,
            help=reason or "Generate a course overview with citations.",
        ):
            progress = st.progress(0)

            def _progress(current: int, total: int) -> None:
                progress.progress(min(current / total, 1.0))

            try:
                output = adapter.generate(
                    action_type="course_overview",
                    payload={
                        "workspace_id": workspace_id,
                        "course_id": course_id,
                        "retrieval_mode": retrieval_mode,
                        "progress_cb": _progress,
                    },
                )
                st.session_state.setdefault("course_outputs", {})[course_id] = {
                    "overview": output
                }
                add_history(
                    workspace_id=workspace_id,
                    action_type="course_overview",
                    summary=f"Course overview for {selected['name']}",
                    preview=output.content[:200],
                    source_ref=course_id,
                    citations_count=len(output.citations),
                    run_id=output.run_id,
                )
                st.success("Course overview generated.")
            except ApiModeError as exc:
                st.error(str(exc))
                if st.button("Switch to Direct Mode", key="api_switch_course_overview"):
                    st.session_state["api_mode"] = "direct"
                    set_setting(None, "api_mode", "direct")
            except Exception as exc:
                st.error(str(exc))

        if st.button(
            "Generate EXAM_CHEATSHEET",
            disabled=not ready,
            help=reason or "Generate a cheat sheet for exam prep.",
        ):
            progress = st.progress(0)

            def _progress_cs(current: int, total: int) -> None:
                progress.progress(min(current / total, 1.0))

            try:
                output = adapter.generate(
                    action_type="course_cheatsheet",
                    payload={
                        "workspace_id": workspace_id,
                        "course_id": course_id,
                        "retrieval_mode": retrieval_mode,
                        "progress_cb": _progress_cs,
                    },
                )
                st.session_state.setdefault("course_outputs", {}).setdefault(course_id, {})[
                    "cheatsheet"
                ] = output
                add_history(
                    workspace_id=workspace_id,
                    action_type="course_cheatsheet",
                    summary=f"Cheatsheet for {selected['name']}",
                    preview=output.content[:200],
                    source_ref=course_id,
                    citations_count=len(output.citations),
                    run_id=output.run_id,
                )
                st.success("Exam cheatsheet generated.")
            except ApiModeError as exc:
                st.error(str(exc))
                if st.button("Switch to Direct Mode", key="api_switch_course_cheatsheet"):
                    st.session_state["api_mode"] = "direct"
                    set_setting(None, "api_mode", "direct")
            except Exception as exc:
                st.error(str(exc))

        st.markdown("#### Explain selection")
        selection = st.text_area("Paste text to explain", key="course_explain_text")
        mode = st.selectbox(
            "Mode",
            options=["plain", "example", "pitfall", "link_prev"],
            key="course_explain_mode",
        )
        if st.button(
            "Explain",
            disabled=not ready or not selection.strip(),
            help=reason or "Explain a selection with citations.",
        ):
            try:
                output = adapter.generate(
                    action_type="course_explain",
                    payload={
                        "workspace_id": workspace_id,
                        "course_id": course_id,
                        "selection": selection.strip(),
                        "mode": mode,
                        "retrieval_mode": retrieval_mode,
                    },
                )
                st.session_state.setdefault("course_outputs", {}).setdefault(course_id, {})[
                    "explain"
                ] = output
                add_history(
                    workspace_id=workspace_id,
                    action_type="course_explain",
                    summary=f"Explain selection ({mode})",
                    preview=output.content[:200],
                    source_ref=course_id,
                    citations_count=len(output.citations),
                    run_id=output.run_id,
                )
                st.success("Explanation generated.")
            except ApiModeError as exc:
                st.error(str(exc))
                if st.button("Switch to Direct Mode", key="api_switch_course_explain"):
                    st.session_state["api_mode"] = "direct"
                    set_setting(None, "api_mode", "direct")
            except Exception as exc:
                st.error(str(exc))

        st.divider()
        st.markdown("#### Outputs")
        outputs = st.session_state.get("course_outputs", {}).get(course_id, {})
        tabs = st.tabs(["Overview", "Cheatsheet", "Explain"])
        with tabs[0]:
            if outputs.get("overview"):
                st.write(outputs["overview"].content)
                render_download(
                    "Download COURSE_OVERVIEW",
                    outputs["overview"].content,
                    "COURSE_OVERVIEW.txt",
                )
                st.caption(
                    f"Asset version: v{outputs['overview'].asset_version_index or '-'}"
                )
            else:
                st.caption("No overview yet.")
        with tabs[1]:
            if outputs.get("cheatsheet"):
                st.write(outputs["cheatsheet"].content)
                render_download(
                    "Download EXAM_CHEATSHEET",
                    outputs["cheatsheet"].content,
                    "EXAM_CHEATSHEET.txt",
                )
                st.caption(
                    f"Asset version: v{outputs['cheatsheet'].asset_version_index or '-'}"
                )
            else:
                st.caption("No cheatsheet yet.")
        with tabs[2]:
            if outputs.get("explain"):
                st.write(outputs["explain"].content)
                st.caption(
                    f"Asset version: v{outputs['explain'].asset_version_index or '-'}"
                )
            else:
                st.caption("No explanation yet.")

        render_chat_panel(
            workspace_id=workspace_id,
            default_retrieval_mode=retrieval_mode,
            api_adapter=adapter,
            api_mode=st.session_state.get("api_mode", "direct"),
        )

    with right:
        st.markdown("### Inspector")
        outputs = st.session_state.get("course_outputs", {}).get(course_id, {})
        view = st.selectbox(
            "View",
            options=["overview", "cheatsheet", "explain"],
            index=0,
        )
        output = outputs.get(view)
        if not output:
            st.caption("No output selected.")
            return
        render_section_title("Citations")
        render_citations(output.citations)
        render_run_info(workspace_id, output.run_id)
        render_section_title("Versions")
        render_asset_versions(
            workspace_id=workspace_id,
            asset_id=output.asset_id,
        )


def render_papers(left: st.delta_generator.DeltaGenerator, center: st.delta_generator.DeltaGenerator, right: st.delta_generator.DeltaGenerator, workspace_id: str) -> None:
    papers = list_papers(workspace_id)
    adapter = _api_adapter()
    with left:
        selected = render_workbench_list(
            title="Papers",
            items=papers,
            label_key="title",
            id_key="id",
            search_key="paper_search",
            new_label="Paper title (optional)",
            new_placeholder="Auto-detected on ingest",
            create_callback=None,
            empty_hint="No papers yet. Upload PDFs to create them.",
            selection_state_key="selected_paper_id",
        )
    ready, reason = llm_ready(
        st.session_state.get("llm_base_url", ""),
        st.session_state.get("llm_model", ""),
        st.session_state.get("llm_api_key", ""),
    )
    retrieval_mode = _ensure_retrieval_mode(workspace_id)

    with center:
        st.markdown("### Paper workspace")
        upload = st.file_uploader("Upload paper PDF", type=["pdf"], key="paper_upload")
        if st.button("Ingest paper", disabled=upload is None):
            try:
                result = adapter.ingest(
                    workspace_id=workspace_id,
                    filename=upload.name,
                    data=upload.getvalue(),
                    save_dir=get_workspaces_dir() / workspace_id / "uploads",
                    kind="paper",
                    ocr_mode=st.session_state.get("ocr_mode", "off"),
                    ocr_threshold=int(st.session_state.get("ocr_threshold", 50)),
                )
                paper_id = result.get("paper_id")
                if paper_id:
                    st.session_state["selected_paper_id"] = paper_id
                st.success("Paper ingested.")
                if result.get("title"):
                    st.caption(
                        f"{result.get('title')} · {result.get('authors')} · {result.get('year')}"
                    )
            except IngestError as exc:
                st.error(str(exc))
            except ApiModeError as exc:
                st.error(str(exc))
                if st.button("Switch to Direct Mode", key="api_switch_paper_ingest"):
                    st.session_state["api_mode"] = "direct"
                    set_setting(None, "api_mode", "direct")

        if not selected:
            st.info("Select a paper to generate outputs.")
        else:
            st.caption(f"Selected paper: {selected['title']}")
            st.markdown("#### Tags")
            tag_input = st.text_input(
                "Add tags (comma-separated)", key="paper_tags_input"
            )
            if st.button("Save paper tags", disabled=not tag_input.strip()):
                add_tags(selected["id"], [tag.strip() for tag in tag_input.split(",")])
                st.success("Tags saved.")

            st.markdown("#### Actions")
            if st.button(
                "Generate PAPER_CARD",
                disabled=not ready,
                help=reason or "Generate a paper card with citations.",
            ):
                progress = st.progress(0)

                def _progress(current: int, total: int) -> None:
                    progress.progress(min(current / total, 1.0))

                try:
                    output = adapter.generate(
                        action_type="paper_card",
                        payload={
                            "workspace_id": workspace_id,
                            "doc_id": selected["doc_id"],
                            "retrieval_mode": retrieval_mode,
                            "progress_cb": _progress,
                        },
                    )
                    st.session_state.setdefault("paper_outputs", {})[selected["id"]] = {
                        "card": output
                    }
                    add_history(
                        workspace_id=workspace_id,
                        action_type="paper_card",
                        summary=f"Paper card for {selected['title']}",
                        preview=output.content[:200],
                        source_ref=selected["id"],
                        citations_count=len(output.citations),
                        run_id=output.run_id,
                    )
                    st.success("Paper card generated.")
                except ApiModeError as exc:
                    st.error(str(exc))
                    if st.button("Switch to Direct Mode", key="api_switch_paper_card"):
                        st.session_state["api_mode"] = "direct"
                        set_setting(None, "api_mode", "direct")
                except Exception as exc:
                    st.error(str(exc))

            st.markdown("#### Aggregate multiple papers")
            selected_papers = st.multiselect(
                "Choose papers",
                options=[paper["title"] for paper in papers],
                default=[],
            )
            question = st.text_area("Aggregation question", key="paper_aggregate_question")
            if st.button(
                "Run aggregation",
                disabled=not ready or not question.strip() or not selected_papers,
                help=reason or "Generate cross-paper synthesis.",
            ):
                doc_ids = [
                    paper["doc_id"]
                    for paper in papers
                    if paper["title"] in selected_papers
                ]
                try:
                    output = adapter.generate(
                        action_type="paper_aggregate",
                        payload={
                            "workspace_id": workspace_id,
                            "doc_ids": doc_ids,
                            "question": question.strip(),
                            "retrieval_mode": retrieval_mode,
                        },
                    )
                    st.session_state.setdefault("paper_outputs", {}).setdefault(
                        selected["id"], {}
                    )["aggregate"] = output
                    add_history(
                        workspace_id=workspace_id,
                        action_type="paper_aggregate",
                        summary="Paper aggregation",
                        preview=output.content[:200],
                        source_ref=",".join(doc_ids),
                        citations_count=len(output.citations),
                        run_id=output.run_id,
                    )
                    st.success("Aggregation generated.")
                except ApiModeError as exc:
                    st.error(str(exc))
                    if st.button("Switch to Direct Mode", key="api_switch_paper_agg"):
                        st.session_state["api_mode"] = "direct"
                        set_setting(None, "api_mode", "direct")
                except Exception as exc:
                    st.error(str(exc))

            st.divider()
            st.markdown("#### Outputs")
            outputs = st.session_state.get("paper_outputs", {}).get(selected["id"], {})
            tabs = st.tabs(["Paper card", "Aggregation"])
            with tabs[0]:
                if outputs.get("card"):
                    st.write(outputs["card"].content)
                    render_download(
                        "Download PAPER_CARD",
                        outputs["card"].content,
                        "PAPER_CARD.txt",
                    )
                    st.caption(
                        f"Asset version: v{outputs['card'].asset_version_index or '-'}"
                    )
                else:
                    st.caption("No paper card yet.")
            with tabs[1]:
                if outputs.get("aggregate"):
                    st.write(outputs["aggregate"].content)
                    st.caption(
                        f"Asset version: v{outputs['aggregate'].asset_version_index or '-'}"
                    )
                else:
                    st.caption("No aggregation yet.")

        render_chat_panel(
            workspace_id=workspace_id,
            default_retrieval_mode=retrieval_mode,
            api_adapter=adapter,
            api_mode=st.session_state.get("api_mode", "direct"),
        )

    with right:
        st.markdown("### Inspector")
        if not selected:
            st.caption("No paper selected.")
            return
        tags = list_tags(selected["id"])
        render_metadata(
            {
                "Title": selected["title"],
                "Authors": selected["authors"],
                "Year": selected["year"],
                "Tags": ", ".join(tags) if tags else "None",
            }
        )
        outputs = st.session_state.get("paper_outputs", {}).get(selected["id"], {})
        view = st.selectbox(
            "View",
            options=["card", "aggregate"],
            index=0,
        )
        output = outputs.get(view)
        if output:
            render_section_title("Citations")
            render_citations(output.citations)
            render_run_info(workspace_id, output.run_id)
            render_section_title("Versions")
            render_asset_versions(
                workspace_id=workspace_id,
                asset_id=output.asset_id,
            )
        else:
            st.caption("No output selected.")


def render_presentations(left: st.delta_generator.DeltaGenerator, center: st.delta_generator.DeltaGenerator, right: st.delta_generator.DeltaGenerator, workspace_id: str) -> None:
    history = list_history(workspace_id, "slides")
    adapter = _api_adapter()
    with left:
        st.markdown("### Decks")
        if not history:
            st.caption("No decks generated yet.")
        else:
            for entry in history[:10]:
                st.write(f"{entry['created_at']} · {entry['summary']}")
                if entry.get("preview"):
                    st.caption(entry["preview"][:140])

    ready, reason = llm_ready(
        st.session_state.get("llm_base_url", ""),
        st.session_state.get("llm_model", ""),
        st.session_state.get("llm_api_key", ""),
    )
    retrieval_mode = _ensure_retrieval_mode(workspace_id)
    sources = list_sources(workspace_id)
    with center:
        st.markdown("### Presentation builder")
        if not sources:
            st.info("No sources available. Ingest PDFs first.")
            return
        source_label = st.selectbox(
            "Select source",
            options=[source["label"] for source in sources],
        )
        duration = st.selectbox("Duration", options=["3", "5", "10", "20"])
        if st.button(
            "Generate slides",
            disabled=not ready,
            help=reason or "Generate Marp deck + Q&A.",
        ):
            source = next(item for item in sources if item["label"] == source_label)
            try:
                output = adapter.generate(
                    action_type="slides",
                    payload={
                        "workspace_id": workspace_id,
                        "doc_id": source["doc_id"],
                        "duration": duration,
                        "retrieval_mode": retrieval_mode,
                    },
                )
                st.session_state["slides_output"] = output
                add_history(
                    workspace_id=workspace_id,
                    action_type="slides",
                    summary=f"Slides ({duration} min)",
                    preview=output.deck[:200],
                    source_ref=source["doc_id"],
                    citations_count=len(output.citations),
                    run_id=output.run_id,
                )
                st.success("Slides generated.")
            except ApiModeError as exc:
                st.error(str(exc))
                if st.button("Switch to Direct Mode", key="api_switch_slides"):
                    st.session_state["api_mode"] = "direct"
                    set_setting(None, "api_mode", "direct")
            except Exception as exc:
                st.error(str(exc))

        output = st.session_state.get("slides_output")
        if output:
            st.divider()
            st.markdown("#### Slides preview")
            st.code(output.deck[:1200] + ("..." if len(output.deck) > 1200 else ""))
            render_download("Download slides (Markdown)", output.deck, "slides.md")
            render_download("Download Q&A", "\n".join(output.qa), "slides_qa.txt")
            st.caption(f"Asset version: v{output.asset_version_index or '-'}")

        render_chat_panel(
            workspace_id=workspace_id,
            default_retrieval_mode=retrieval_mode,
            api_adapter=adapter,
            api_mode=st.session_state.get("api_mode", "direct"),
        )

    with right:
        st.markdown("### Inspector")
        output = st.session_state.get("slides_output")
        if not output:
            st.caption("No slides generated yet.")
            return
        render_section_title("Citations")
        render_citations(output.citations)
        render_run_info(workspace_id, output.run_id)
        render_section_title("Versions")
        render_asset_versions(
            workspace_id=workspace_id,
            asset_id=output.asset_id,
        )


def render_coach(left: st.delta_generator.DeltaGenerator, center: st.delta_generator.DeltaGenerator, right: st.delta_generator.DeltaGenerator, workspace_id: str) -> None:
    retrieval_mode = _ensure_retrieval_mode(workspace_id)
    sessions = list_coach_sessions(workspace_id)
    with left:
        st.markdown("### Coach Sessions")
        if not sessions:
            st.caption("No coach sessions yet.")
        else:
            for session in sessions[:10]:
                st.write(f"{session.created_at[:19]} · {session.id}")
                st.caption(session.problem[:120])
        if confirm_action(
            key="confirm_clear_coach",
            label="Confirm clear sessions",
            help_text="Remove all coach sessions in this workspace.",
        ):
            if st.button("Clear coach sessions", type="primary"):
                clear_coach_sessions(workspace_id)
                st.success("Coach sessions cleared.")

    with center:
        st.markdown("### Study Coach")
        ready, reason = llm_ready(
            st.session_state.get("llm_base_url", ""),
            st.session_state.get("llm_model", ""),
            st.session_state.get("llm_api_key", ""),
        )
        st.markdown("#### Phase A — Framework")
        problem = st.text_area("Problem statement", height=140, key="coach_problem")
        if st.button(
            "Start coaching",
            disabled=not problem.strip() or not ready,
            help=reason or "Generate framework and hints.",
        ):
            try:
                result = start_coach(
                    workspace_id=workspace_id,
                    problem=problem.strip(),
                    retrieval_mode=retrieval_mode,
                )
                st.session_state["coach_last_session_id"] = result.session.id
                st.success("Phase A complete.")
                st.write(result.output.content)
                for citation in result.output.citations:
                    st.write(citation)
            except Exception as exc:
                st.error(str(exc))

        st.divider()
        st.markdown("#### Phase B — Review")
        session_ids = [session.id for session in sessions]
        selected_session = st.selectbox(
            "Select session",
            options=["(none)"] + session_ids,
        )
        answer = st.text_area("Your answer", height=140, key="coach_answer")
        if st.button(
            "Submit answer",
            disabled=selected_session == "(none)" or not answer.strip() or not ready,
            help=reason or "Get feedback and rubric.",
        ):
            try:
                result = submit_coach(
                    workspace_id=workspace_id,
                    session_id=selected_session,
                    answer=answer.strip(),
                    retrieval_mode=retrieval_mode,
                )
                st.session_state["coach_last_session_id"] = result.session.id
                st.success("Phase B complete.")
                st.write(result.output.content)
                for citation in result.output.citations:
                    st.write(citation)
            except Exception as exc:
                st.error(str(exc))

    with right:
        st.markdown("### Inspector")
        session_id = st.session_state.get("coach_last_session_id")
        if not session_id:
            st.caption("No session selected.")
            return
        session = show_coach_session(session_id)
        render_metadata(
            {
                "Session": session.id,
                "Status": session.status or "-",
                "Updated": session.updated_at[:19],
            }
        )
        if session.phase_a_output:
            render_section_title("Phase A")
            st.write(session.phase_a_output[:600] + ("..." if len(session.phase_a_output) > 600 else ""))
        if session.phase_b_output:
            render_section_title("Phase B")
            st.write(session.phase_b_output[:600] + ("..." if len(session.phase_b_output) > 600 else ""))


def render_plugins(
    left: st.delta_generator.DeltaGenerator,
    center: st.delta_generator.DeltaGenerator,
    right: st.delta_generator.DeltaGenerator,
    workspace_id: str,
) -> None:
    with center:
        render_plugins_center(workspace_id=workspace_id)


def render_tasks(center: st.delta_generator.DeltaGenerator, workspace_id: str | None) -> None:
    with center:
        render_tasks_center(workspace_id=workspace_id)


def render_exports(center: st.delta_generator.DeltaGenerator, workspace_id: str | None) -> None:
    with center:
        render_exports_center(workspace_id=workspace_id)


def render_diagnostics(center: st.delta_generator.DeltaGenerator, workspace_id: str | None) -> None:
    with center:
        render_diagnostics_center(workspace_id=workspace_id)


def render_history_page(center: st.delta_generator.DeltaGenerator, right: st.delta_generator.DeltaGenerator, workspace_id: str) -> None:
    with center:
        st.markdown("### History")
        action_filter = st.selectbox(
            "Filter",
            options=[
                "all",
                "chat",
                "course_overview",
                "course_cheatsheet",
                "course_explain",
                "paper_card",
                "paper_aggregate",
                "slides",
                "library_ingest",
            ],
            index=0,
        )
        entries = list_history(workspace_id, action_filter)
        if not entries:
            st.caption("No history yet.")
            return
        selected = st.selectbox(
            "Select entry",
            options=[entry["id"] for entry in entries],
            format_func=lambda entry_id: next(
                (
                    f"{entry['created_at']} · {entry['action_type']} · {entry.get('run_id') or '-'} · success"
                    for entry in entries
                    if entry["id"] == entry_id
                ),
                entry_id,
            ),
        )
        selected_entry = next(entry for entry in entries if entry["id"] == selected)
        if confirm_action(
            key="confirm_clear_history",
            label="Confirm clear history",
            help_text="Clears all history for this workspace.",
        ):
            if st.button("Clear history", type="primary"):
                clear_history(workspace_id)
                st.success("History cleared.")
    with right:
        st.markdown("### Entry details")
        if not entries:
            st.caption("No history to inspect.")
            return
        render_metadata(
            {
                "Action": selected_entry["action_type"],
                "Created": selected_entry["created_at"],
                "Source": selected_entry.get("source_ref") or "-",
                "Run ID": selected_entry.get("run_id") or "-",
                "Status": "success",
                "Citations": str(selected_entry.get("citations_count") or 0),
            }
        )
        st.divider()
        if selected_entry.get("summary"):
            st.markdown("#### Summary")
            st.write(selected_entry["summary"])
        if selected_entry.get("preview"):
            st.markdown("#### Preview")
            st.write(selected_entry["preview"])


def render_settings(
    center: st.delta_generator.DeltaGenerator,
    right: st.delta_generator.DeltaGenerator,
    workspace_id: str | None,
) -> None:
    render_settings_center(center=center, right=right, workspace_id=workspace_id)


def main() -> None:
    load_dotenv()
    try:
        apply_profile(load_config())
    except ConfigError:
        pass

    st.set_page_config(page_title="StudyFlow-AI", layout="wide")
    apply_theme()
    init_app_state()

    workspace_id, nav = render_sidebar()
    maybe_auto_refresh(workspace_id=workspace_id)

    main_col, inspector_col = render_main_columns()
    api_adapter = _api_adapter()

    if nav == "Start":
        render_start_page(
            main_col=main_col,
            inspector_col=inspector_col,
            workspace_id=workspace_id,
            api_adapter=api_adapter,
        )
    elif nav == "Library":
        render_library_page(
            main_col=main_col,
            inspector_col=inspector_col,
            workspace_id=workspace_id,
        )
    elif nav == "Create":
        render_create_page(
            main_col=main_col,
            inspector_col=inspector_col,
            workspace_id=workspace_id,
            api_adapter=api_adapter,
        )
    elif nav == "Tools":
        render_tools_page(
            main_col=main_col,
            inspector_col=inspector_col,
            workspace_id=workspace_id,
        )
    elif nav == "Help":
        render_help_page(
            main_col=main_col,
            inspector_col=inspector_col,
            workspace_id=workspace_id,
        )

    inject_auto_refresh(workspace_id=workspace_id)


if __name__ == "__main__":
    main()

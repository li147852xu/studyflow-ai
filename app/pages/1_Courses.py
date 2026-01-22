import os
import streamlit as st

from app.ui import init_app_state, require_workspace
from app.components.sidebar import sidebar_llm, sidebar_retrieval_mode, sidebar_workspace
from app.components.history_view import render_history
from core.ui_state.storage import add_history
from core.ui_state.guards import llm_ready
from core.ingest.cite import build_citation
from infra.db import get_workspaces_dir
from service.chat_service import ChatConfigError, chat
from service.document_service import list_documents
from service.ingest_service import IngestError, get_random_chunks, ingest_pdf
from service.retrieval_service import (
    RetrievalError,
    build_or_refresh_index,
    answer_with_retrieval,
)
from core.telemetry.run_logger import _run_dir, log_run
from service.course_service import (
    create_course,
    list_courses,
    link_document,
    list_course_documents,
    generate_overview,
    generate_cheatsheet,
    explain_selection,
)


def main() -> None:
    st.set_page_config(page_title="Courses", layout="wide")
    init_app_state()
    workspace_id = sidebar_workspace()
    sidebar_llm()
    retrieval_mode = sidebar_retrieval_mode(workspace_id)
    if workspace_id:
        render_history(workspace_id)

    st.title("Courses")
    workspace_id = require_workspace()
    if not workspace_id:
        return
    ready, reason = llm_ready(
        st.session_state.get("llm_base_url", ""),
        st.session_state.get("llm_model", ""),
        st.session_state.get("llm_api_key", ""),
    )

    st.subheader("Data")
    courses = list_courses(workspace_id)
    course_names = {course["name"]: course["id"] for course in courses}
    selected_course = st.selectbox(
        "Select course",
        options=["(new)"] + list(course_names.keys()),
    )
    if selected_course == "(new)":
        new_name = st.text_input("New course name")
        if st.button("Create course", disabled=not new_name.strip(), help="Create a new course in this workspace."):
            if not new_name.strip():
                st.error("Course name cannot be empty.")
            else:
                course_id = create_course(workspace_id, new_name.strip())
                st.session_state["course_id"] = course_id
                st.success("Course created.")
    else:
        st.session_state["course_id"] = course_names[selected_course]

    course_id = st.session_state.get("course_id")
    if course_id:
        linked_docs = list_course_documents(course_id)
        if linked_docs:
            st.caption("Linked lecture PDFs")
            for doc in linked_docs:
                st.write(f"- {doc['filename']}")

    st.subheader("Upload PDF")
    uploaded = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded is not None:
        if st.button("Save PDF", help="Save and ingest PDF into the workspace."):
            try:
                result = ingest_pdf(
                    workspace_id=workspace_id,
                    filename=uploaded.name,
                    data=uploaded.getvalue(),
                    save_dir=get_workspaces_dir() / workspace_id / "uploads",
                )
                st.session_state["last_ingest"] = result
                if result.skipped:
                    st.warning("This PDF was already ingested. Skipped re-ingest.")
                else:
                    st.success("PDF ingested successfully.")
                if course_id:
                    link_document(course_id, result.doc_id)
                    st.info("Linked PDF to selected course.")
            except IngestError as exc:
                st.error(str(exc))
            except OSError:
                st.error("Failed to save file. Please check permissions.")

    documents = list_documents(workspace_id)
    if documents:
        st.caption("Recent uploads")
        for doc in documents[:5]:
            st.write(f"- {doc['filename']}")

    ingest_info = st.session_state.get("last_ingest")
    if ingest_info:
        st.subheader("Ingest Result")
        st.write(f"Pages: {ingest_info.page_count}")
        st.write(f"Chunks: {ingest_info.chunk_count}")
        st.write(f"Page range: 1-{ingest_info.page_count}")

        if st.button("Build/Refresh Vector Index", help="Required for vector retrieval mode."):
            progress = st.progress(0)

            def _progress(current: int, total: int) -> None:
                progress.progress(min(current / total, 1.0))

            try:
                result = build_or_refresh_index(
                    workspace_id=workspace_id, reset=True, progress_cb=_progress
                )
                st.success(
                    f"Indexed {result.indexed_count} chunks across {result.doc_count} documents."
                )
            except Exception as exc:
                st.error(f"Index build failed: {exc}")

        if st.button("Show citations preview", help="Preview 3 sample citations from this PDF."):
            preview_chunks = get_random_chunks(ingest_info.doc_id, limit=3)
            if not preview_chunks:
                st.info("No chunks available for preview.")
            for chunk in preview_chunks:
                citation = build_citation(
                    filename=ingest_info.filename,
                    page_start=chunk["page_start"],
                    page_end=chunk["page_end"],
                    text=chunk["text"],
                )
                st.write(citation.render())

    if course_id:
        st.subheader("Actions")
        if st.button(
            "Generate Course Overview",
            disabled=not ready,
            help=reason or "Generate a course overview with citations.",
        ):
            progress = st.progress(0)

            def _progress(current: int, total: int) -> None:
                progress.progress(min(current / total, 1.0))

            try:
                output = generate_overview(
                    workspace_id=workspace_id,
                    course_id=course_id,
                    retrieval_mode=retrieval_mode,
                    progress_cb=_progress,
                )
                st.session_state["overview_output"] = output
                st.success("Course overview generated.")
                add_history(
                    workspace_id=workspace_id,
                    action_type="course_overview",
                    summary=f"Course overview for {course_id}",
                    preview=output.content[:200],
                    source_ref=course_id,
                    citations_count=len(output.citations),
                )
            except Exception as exc:
                st.error(str(exc))

        if st.button(
            "Generate Exam Cheatsheet",
            disabled=not ready,
            help=reason or "Generate a cheat sheet for exam prep.",
        ):
            progress = st.progress(0)

            def _progress_cs(current: int, total: int) -> None:
                progress.progress(min(current / total, 1.0))

            try:
                output = generate_cheatsheet(
                    workspace_id=workspace_id,
                    course_id=course_id,
                    retrieval_mode=retrieval_mode,
                    progress_cb=_progress_cs,
                )
                st.session_state["cheatsheet_output"] = output
                st.success("Exam cheatsheet generated.")
                add_history(
                    workspace_id=workspace_id,
                    action_type="course_cheatsheet",
                    summary=f"Cheatsheet for {course_id}",
                    preview=output.content[:200],
                    source_ref=course_id,
                    citations_count=len(output.citations),
                )
            except Exception as exc:
                st.error(str(exc))

        overview_output = st.session_state.get("overview_output")
        if overview_output:
            st.subheader("Results")
            st.subheader("COURSE_OVERVIEW")
            st.write(overview_output.content)
            st.download_button(
                "Download COURSE_OVERVIEW (.txt)",
                overview_output.content,
                file_name="COURSE_OVERVIEW.txt",
            )
            st.subheader("Citations")
            for citation in overview_output.citations:
                st.write(citation)
            if overview_output.run_id:
                st.caption(
                    f"Last run_id: {overview_output.run_id} | "
                    f"log: {_run_dir(workspace_id)}/run_{overview_output.run_id}.json"
                )

        cheatsheet_output = st.session_state.get("cheatsheet_output")
        if cheatsheet_output:
            st.subheader("EXAM_CHEATSHEET")
            st.write(cheatsheet_output.content)
            st.download_button(
                "Download EXAM_CHEATSHEET (.txt)",
                cheatsheet_output.content,
                file_name="EXAM_CHEATSHEET.txt",
            )
            st.subheader("Citations")
            for citation in cheatsheet_output.citations:
                st.write(citation)
            if cheatsheet_output.run_id:
                st.caption(
                    f"Last run_id: {cheatsheet_output.run_id} | "
                    f"log: {_run_dir(workspace_id)}/run_{cheatsheet_output.run_id}.json"
                )

        st.subheader("Explain Selection")
        selection = st.text_area("Paste text to explain")
        mode = st.selectbox(
            "Mode",
            options=["plain", "example", "pitfall", "link_prev"],
        )
        if st.button(
            "Explain",
            disabled=not ready or not selection.strip(),
            help=reason or "Explain a selection with citations.",
        ):
            if not selection.strip():
                st.error("Please provide text to explain.")
            else:
                try:
                    output = explain_selection(
                        workspace_id=workspace_id,
                        course_id=course_id,
                        selection=selection.strip(),
                        mode=mode,
                        retrieval_mode=retrieval_mode,
                    )
                    st.write(output.content)
                    st.subheader("Citations")
                    for citation in output.citations:
                        st.write(citation)
                    if output.run_id:
                        st.caption(
                            f"Last run_id: {output.run_id} | "
                            f"log: {_run_dir(workspace_id)}/run_{output.run_id}.json"
                        )
                    add_history(
                        workspace_id=workspace_id,
                        action_type="course_explain",
                        summary=f"Explain selection ({mode})",
                        preview=output.content[:200],
                        source_ref=course_id,
                        citations_count=len(output.citations),
                    )
                except Exception as exc:
                    st.error(str(exc))

    st.subheader("Results")
    st.subheader("Chat")
    use_retrieval = st.toggle("Use Retrieval (V0.2)", value=False)
    prompt = st.text_input("Ask a question")
    if st.button(
        "Send",
        key="chat_send",
        disabled=not prompt.strip() or not ready,
        help=reason or "Ask a question with or without retrieval.",
    ):
        if not prompt.strip():
            st.error("Please enter a question.")
            return
        try:
            if use_retrieval:
                response, hits, citations, run_id = answer_with_retrieval(
                    workspace_id=workspace_id,
                    query=prompt,
                    mode=retrieval_mode,
                )
                st.write(response)
                st.subheader("Retrieval Hits")
                for idx, hit in enumerate(hits, start=1):
                    st.write(
                        f"[{idx}] {hit.filename} p.{hit.page_start}-{hit.page_end} "
                        f"(score={hit.score:.4f})"
                    )
                    st.caption(hit.text[:300] + ("..." if len(hit.text) > 300 else ""))
                st.subheader("Citations")
                for citation in citations:
                    st.write(citation)
                st.caption(
                    f"Last run_id: {run_id} | "
                    f"log: {_run_dir(workspace_id)}/run_{run_id}.json"
                )
                add_history(
                    workspace_id=workspace_id,
                    action_type="chat",
                    summary="Chat with retrieval",
                    preview=response[:200],
                    source_ref=None,
                    citations_count=len(citations),
                )
            else:
                response = chat(
                    prompt=prompt,
                    base_url=st.session_state.get("llm_base_url"),
                    api_key=st.session_state.get("llm_api_key"),
                    model=st.session_state.get("llm_model"),
                )
                st.write(response)
                run_id = log_run(
                    workspace_id=workspace_id,
                    action_type="chat",
                    input_payload={"query": prompt},
                    retrieval_mode="none",
                    hits=[],
                    model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
                    embed_model=os.getenv("STUDYFLOW_EMBED_MODEL", ""),
                    latency_ms=0,
                    errors=None,
                )
                st.caption(
                    f"Last run_id: {run_id} | "
                    f"log: {_run_dir(workspace_id)}/run_{run_id}.json"
                )
                add_history(
                    workspace_id=workspace_id,
                    action_type="chat",
                    summary="Chat (no retrieval)",
                    preview=response[:200],
                    source_ref=None,
                    citations_count=0,
                )
        except ChatConfigError as exc:
            st.error(str(exc))
        except RetrievalError as exc:
            st.error(str(exc))
        except Exception:
            st.error("LLM request failed. Please check your network or key.")


if __name__ == "__main__":
    main()

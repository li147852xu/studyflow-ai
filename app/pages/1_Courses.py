import streamlit as st

from app.ui import init_app_state, require_workspace, sidebar_llm, sidebar_workspace
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
    sidebar_workspace()
    sidebar_llm()

    st.title("Courses")
    workspace_id = require_workspace()
    if not workspace_id:
        return

    st.subheader("Course")
    courses = list_courses(workspace_id)
    course_names = {course["name"]: course["id"] for course in courses}
    selected_course = st.selectbox(
        "Select course",
        options=["(new)"] + list(course_names.keys()),
    )
    if selected_course == "(new)":
        new_name = st.text_input("New course name")
        if st.button("Create course"):
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
        if st.button("Save PDF"):
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

        if st.button("Build/Refresh Vector Index"):
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

        if st.button("Show citations preview"):
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
        st.subheader("Course Generation")
        if st.button("Generate Course Overview"):
            progress = st.progress(0)

            def _progress(current: int, total: int) -> None:
                progress.progress(min(current / total, 1.0))

            try:
                output = generate_overview(
                    workspace_id=workspace_id,
                    course_id=course_id,
                    progress_cb=_progress,
                )
                st.session_state["overview_output"] = output
                st.success("Course overview generated.")
            except Exception as exc:
                st.error(str(exc))

        if st.button("Generate Exam Cheatsheet"):
            progress = st.progress(0)

            def _progress_cs(current: int, total: int) -> None:
                progress.progress(min(current / total, 1.0))

            try:
                output = generate_cheatsheet(
                    workspace_id=workspace_id,
                    course_id=course_id,
                    progress_cb=_progress_cs,
                )
                st.session_state["cheatsheet_output"] = output
                st.success("Exam cheatsheet generated.")
            except Exception as exc:
                st.error(str(exc))

        overview_output = st.session_state.get("overview_output")
        if overview_output:
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

        st.subheader("Explain Selection")
        selection = st.text_area("Paste text to explain")
        mode = st.selectbox(
            "Mode",
            options=["plain", "example", "pitfall", "link_prev"],
        )
        if st.button("Explain"):
            if not selection.strip():
                st.error("Please provide text to explain.")
            else:
                try:
                    output = explain_selection(
                        workspace_id=workspace_id,
                        course_id=course_id,
                        selection=selection.strip(),
                        mode=mode,
                    )
                    st.write(output.content)
                    st.subheader("Citations")
                    for citation in output.citations:
                        st.write(citation)
                except Exception as exc:
                    st.error(str(exc))

    st.subheader("Chat")
    use_retrieval = st.toggle("Use Retrieval (V0.0.3)", value=False)
    prompt = st.text_input("Ask a question")
    if st.button("Send", key="chat_send"):
        if not prompt.strip():
            st.error("Please enter a question.")
            return
        try:
            if use_retrieval:
                response, hits, citations = answer_with_retrieval(
                    workspace_id=workspace_id,
                    query=prompt,
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
            else:
                response = chat(
                    prompt=prompt,
                    base_url=st.session_state.get("llm_base_url"),
                    api_key=st.session_state.get("llm_api_key"),
                    model=st.session_state.get("llm_model"),
                )
                st.write(response)
        except ChatConfigError as exc:
            st.error(str(exc))
        except RetrievalError as exc:
            st.error(str(exc))
        except Exception:
            st.error("LLM request failed. Please check your network or key.")


if __name__ == "__main__":
    main()

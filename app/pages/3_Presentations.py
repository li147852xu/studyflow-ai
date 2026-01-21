import streamlit as st

from app.ui import init_app_state, require_workspace, sidebar_llm, sidebar_workspace
from core.ingest.cite import build_citation
from infra.db import get_workspaces_dir
from service.chat_service import ChatConfigError, chat
from service.document_service import list_documents
from service.ingest_service import IngestError, get_random_chunks, ingest_pdf


def main() -> None:
    st.set_page_config(page_title="Presentations", layout="wide")
    init_app_state()
    sidebar_workspace()
    sidebar_llm()

    st.title("Presentations")
    workspace_id = require_workspace()
    if not workspace_id:
        return

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

    st.subheader("Chat")
    prompt = st.text_input("Ask a question")
    if st.button("Send", key="chat_send"):
        if not prompt.strip():
            st.error("Please enter a question.")
            return
        try:
            response = chat(
                prompt=prompt,
                base_url=st.session_state.get("llm_base_url"),
                api_key=st.session_state.get("llm_api_key"),
                model=st.session_state.get("llm_model"),
            )
            st.write(response)
        except ChatConfigError as exc:
            st.error(str(exc))
        except Exception:
            st.error("LLM request failed. Please check your network or key.")


if __name__ == "__main__":
    main()

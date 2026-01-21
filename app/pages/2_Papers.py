import streamlit as st

from app.ui import init_app_state, require_workspace, sidebar_llm, sidebar_workspace
from service.chat_service import ChatConfigError, chat
from service.document_service import list_documents, save_document_bytes


def main() -> None:
    st.set_page_config(page_title="Papers", layout="wide")
    init_app_state()
    sidebar_workspace()
    sidebar_llm()

    st.title("Papers")
    workspace_id = require_workspace()
    if not workspace_id:
        return

    st.subheader("Upload PDF")
    uploaded = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded is not None:
        if st.button("Save PDF"):
            try:
                save_document_bytes(
                    workspace_id=workspace_id,
                    filename=uploaded.name,
                    data=uploaded.getvalue(),
                )
                st.success("File saved to workspace.")
            except OSError:
                st.error("Failed to save file. Please check permissions.")

    documents = list_documents(workspace_id)
    if documents:
        st.caption("Recent uploads")
        for doc in documents[:5]:
            st.write(f"- {doc['filename']}")

    st.subheader("Chat")
    st.caption("Note: V0.0.1 chat does not read uploaded PDFs.")
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

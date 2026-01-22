import streamlit as st
from dotenv import load_dotenv

from core.config.loader import load_config, apply_profile, ConfigError

from app.ui import init_app_state
from app.components.sidebar import sidebar_llm, sidebar_retrieval_mode, sidebar_workspace
from app.components.history_view import render_history


def main() -> None:
    load_dotenv()
    try:
        apply_profile(load_config())
    except ConfigError:
        pass
    st.set_page_config(page_title="StudyFlow-AI", layout="wide")
    init_app_state()
    workspace_id = sidebar_workspace()
    sidebar_llm()
    sidebar_retrieval_mode(workspace_id)
    if workspace_id:
        render_history(workspace_id)

    st.title("StudyFlow-AI")
    st.write("Use the pages in the sidebar to upload PDFs and run your workflows.")
    st.info("Open Help / Docs for a full walkthrough and troubleshooting tips.")


if __name__ == "__main__":
    main()

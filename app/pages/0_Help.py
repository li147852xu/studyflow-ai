import streamlit as st

from app.ui import init_app_state
from app.components.sidebar import sidebar_llm, sidebar_retrieval_mode, sidebar_workspace
from app.components.history_view import render_history
from app.help_content import HELP_TEXT


def main() -> None:
    st.set_page_config(page_title="Help / Docs", layout="wide")
    init_app_state()
    workspace_id = sidebar_workspace()
    sidebar_llm()
    sidebar_retrieval_mode(workspace_id)
    if workspace_id:
        render_history(workspace_id)

    st.title("Help / Docs")
    st.markdown(HELP_TEXT)


if __name__ == "__main__":
    main()

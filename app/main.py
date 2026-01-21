import streamlit as st
from dotenv import load_dotenv

from app.ui import init_app_state, sidebar_llm, sidebar_workspace


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="StudyFlow-AI", layout="wide")
    init_app_state()
    sidebar_workspace()
    sidebar_llm()

    st.title("StudyFlow-AI V0.0.1 Skeleton")
    st.write(
        "Use the pages in the sidebar to upload PDFs and chat with your LLM."
    )
    st.info("This version does not perform retrieval or citations.")


if __name__ == "__main__":
    main()

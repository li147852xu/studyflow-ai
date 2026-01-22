import os
import streamlit as st

from app.ui import init_app_state, require_workspace
from app.components.sidebar import sidebar_llm, sidebar_retrieval_mode, sidebar_workspace
from app.components.history_view import render_history
from core.ui_state.storage import add_history
from core.ui_state.guards import llm_ready
from service.retrieval_service import build_or_refresh_index
from service.presentation_service import list_sources, generate_slides
from core.telemetry.run_logger import _run_dir


def main() -> None:
    st.set_page_config(page_title="Presentations", layout="wide")
    init_app_state()
    workspace_id = sidebar_workspace()
    sidebar_llm()
    retrieval_mode = sidebar_retrieval_mode(workspace_id)
    if workspace_id:
        render_history(workspace_id)

    st.title("Presentations")
    workspace_id = require_workspace()
    if not workspace_id:
        return
    ready, reason = llm_ready(
        st.session_state.get("llm_base_url", ""),
        st.session_state.get("llm_model", ""),
        st.session_state.get("llm_api_key", ""),
    )

    st.subheader("Data")
    st.subheader("Source Selection")
    sources = list_sources(workspace_id)
    if not sources:
        st.warning("No documents/papers available. Upload PDFs first.")
        return

    labels = [source["label"] for source in sources]
    selected_label = st.selectbox("Select source", options=labels)
    selected_source = next(s for s in sources if s["label"] == selected_label)

    st.subheader("Index")
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

    st.subheader("Actions")
    st.subheader("Generate Slides")
    duration = st.selectbox("Duration (minutes)", options=["3", "5", "10", "20"])
    save_outputs = st.toggle("Save deck to outputs/", value=True)
    if st.button(
        "Generate Marp Deck",
        disabled=not ready,
        help=reason or "Generate a Marp deck with Q&A and citations.",
    ):
        try:
            output = generate_slides(
                workspace_id=workspace_id,
                doc_id=selected_source["doc_id"],
                duration=duration,
                retrieval_mode=retrieval_mode,
                save_outputs=save_outputs,
            )
            st.session_state["slides_output"] = output
            st.success("Slides generated.")
            add_history(
                workspace_id=workspace_id,
                action_type="slides",
                summary=f"Slides ({duration} min)",
                preview=output.deck[:200],
                source_ref=selected_source["doc_id"],
                citations_count=len(output.citations),
            )
        except Exception as exc:
            st.error(str(exc))

    slides_output = st.session_state.get("slides_output")
    if slides_output:
        st.subheader("Results")
        st.subheader("Deck Preview (Marp)")
        st.text_area("Deck", slides_output.deck, height=400)
        st.download_button(
            "Download Marp .md",
            slides_output.deck,
            file_name="slides_deck.md",
        )
        if slides_output.saved_path:
            st.caption(f"Saved to: {slides_output.saved_path}")

        st.subheader("Q&A (10)")
        for qa in slides_output.qa:
            st.write(qa)

        st.subheader("Citations")
        for citation in slides_output.citations:
            st.write(citation)
        if slides_output.run_id:
            st.caption(
                f"Last run_id: {slides_output.run_id} | "
                f"log: {_run_dir(workspace_id)}/run_{slides_output.run_id}.json"
            )


if __name__ == "__main__":
    main()

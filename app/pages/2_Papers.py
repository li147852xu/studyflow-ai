import os
import streamlit as st

from app.ui import init_app_state, require_workspace, sidebar_llm, sidebar_workspace
from infra.db import get_workspaces_dir
from service.chat_service import ChatConfigError, chat
from service.ingest_service import IngestError
from service.retrieval_service import (
    RetrievalError,
    answer_with_retrieval,
    build_or_refresh_index,
)
from service.paper_service import (
    ingest_paper,
    list_papers,
    update_paper_metadata,
    add_tags,
    list_tags,
)
from service.paper_generate_service import generate_paper_card, aggregate_papers
from core.telemetry.run_logger import _run_dir, log_run


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
                paper_id, metadata = ingest_paper(
                    workspace_id=workspace_id,
                    filename=uploaded.name,
                    data=uploaded.getvalue(),
                    save_dir=get_workspaces_dir() / workspace_id / "uploads",
                )
                st.session_state["last_paper_id"] = paper_id
                st.success("Paper ingested successfully.")
                st.info(
                    f"Metadata: {metadata.title} | {metadata.authors} | {metadata.year}"
                )
            except IngestError as exc:
                st.error(str(exc))
            except OSError:
                st.error("Failed to save file. Please check permissions.")

    papers = list_papers(workspace_id)
    retrieval_mode = "vector"
    if papers:
        retrieval_mode = st.selectbox(
            "Retrieval Mode",
            options=["vector", "bm25", "hybrid"],
            index=0,
            key="paper_retrieval_mode",
        )

        st.subheader("Paper Library")
        selected = st.selectbox(
            "Select paper",
            options=["(none)"] + [paper["title"] for paper in papers],
        )
        if selected != "(none)":
            paper = next(p for p in papers if p["title"] == selected)
            st.session_state["selected_paper"] = paper
        else:
            st.session_state.pop("selected_paper", None)

    selected_paper = st.session_state.get("selected_paper")
    if selected_paper:
        st.subheader("Paper Metadata")
        title = st.text_input("Title", value=selected_paper["title"])
        authors = st.text_input("Authors", value=selected_paper["authors"])
        year = st.text_input("Year", value=selected_paper["year"])
        tags_input = st.text_input(
            "Tags (comma separated)",
            value=", ".join(list_tags(selected_paper["id"])),
        )
        if st.button("Save Metadata"):
            update_paper_metadata(
                paper_id=selected_paper["id"],
                title=title,
                authors=authors,
                year=year,
            )
            add_tags(selected_paper["id"], [t.strip() for t in tags_input.split(",")])
            st.success("Metadata updated.")

        if st.button("Generate PAPER_CARD"):
            progress = st.progress(0)

            def _progress(current: int, total: int) -> None:
                progress.progress(min(current / total, 1.0))

            try:
                output = generate_paper_card(
                    workspace_id=workspace_id,
                    doc_id=selected_paper["doc_id"],
                    retrieval_mode=retrieval_mode,
                    progress_cb=_progress,
                )
                st.session_state["paper_card_output"] = output
                st.success("PAPER_CARD generated.")
            except Exception as exc:
                st.error(str(exc))

        paper_card_output = st.session_state.get("paper_card_output")
        if paper_card_output:
            st.subheader("PAPER_CARD")
            st.write(paper_card_output.content)
            st.download_button(
                "Download PAPER_CARD (.txt)",
                paper_card_output.content,
                file_name="PAPER_CARD.txt",
            )
            st.subheader("Citations")
            for citation in paper_card_output.citations:
                st.write(citation)
            if paper_card_output.run_id:
                st.caption(
                    f"Last run_id: {paper_card_output.run_id} | "
                    f"log: {_run_dir(workspace_id)}/run_{paper_card_output.run_id}.json"
                )

    if papers:
        st.subheader("Cross-paper Aggregator")
        paper_titles = [paper["title"] for paper in papers]
        selected_titles = st.multiselect(
            "Select papers",
            options=paper_titles,
        )

        if "agg_question" not in st.session_state:
            st.session_state["agg_question"] = ""

        if st.button("Template: 共识"):
            st.session_state["agg_question"] = "共识是什么？"
        if st.button("Template: 分歧"):
            st.session_state["agg_question"] = "分歧是什么？"
        if st.button("Template: 路线"):
            st.session_state["agg_question"] = "方法路线分支有哪些？"
        if st.button("Template: Related Work"):
            st.session_state["agg_question"] = "related work 应该怎么分段？"

        st.text_input("Aggregation question", key="agg_question")

        if st.button("Run Aggregation"):
            if not selected_titles:
                st.error("Select at least one paper.")
            else:
                progress = st.progress(0)

                def _progress_agg(current: int, total: int) -> None:
                    progress.progress(min(current / total, 1.0))

                try:
                    doc_ids = [
                        paper["doc_id"]
                        for paper in papers
                        if paper["title"] in selected_titles
                    ]
                    output = aggregate_papers(
                        workspace_id=workspace_id,
                        doc_ids=doc_ids,
                        question=st.session_state.get("agg_question", ""),
                        retrieval_mode=retrieval_mode,
                        progress_cb=_progress_agg,
                    )
                    st.session_state["agg_output"] = output
                    st.success("Aggregation completed.")
                except Exception as exc:
                    st.error(str(exc))

        agg_output = st.session_state.get("agg_output")
        if agg_output:
            st.subheader("Aggregation Output")
            st.write(agg_output.content)
            st.subheader("Citations")
            for citation in agg_output.citations:
                st.write(citation)
            if agg_output.run_id:
                st.caption(
                    f"Last run_id: {agg_output.run_id} | "
                    f"log: {_run_dir(workspace_id)}/run_{agg_output.run_id}.json"
                )

    st.subheader("Vector Index")
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

    st.subheader("Chat")
    use_retrieval = st.toggle("Use Retrieval (V0.2)", value=False)
    prompt = st.text_input("Ask a question")
    if st.button("Send", key="chat_send"):
        if not prompt.strip():
            st.error("Please enter a question.")
            return
        try:
            if use_retrieval:
                response, hits, citations, run_id = answer_with_retrieval(
                    workspace_id=workspace_id,
                    query=prompt,
                    mode=retrieval_mode if papers else "vector",
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
        except ChatConfigError as exc:
            st.error(str(exc))
        except RetrievalError as exc:
            st.error(str(exc))
        except Exception:
            st.error("LLM request failed. Please check your network or key.")


if __name__ == "__main__":
    main()

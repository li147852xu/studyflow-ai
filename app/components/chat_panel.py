from __future__ import annotations

import streamlit as st

from app.ui.locks import running_task_summary
from core.retrieval.retriever import Hit
from core.telemetry.run_logger import _run_dir, log_run
from core.ui_state.guards import llm_ready
from core.ui_state.storage import add_history, list_history, set_setting
from service.api_mode_adapter import ApiModeAdapter, ApiModeError
from service.asset_service import ask_ref_id, create_asset_version
from service.chat_service import ChatConfigError, chat
from service.metadata_service import llm_metadata
from service.retrieval_service import RetrievalError, answer_with_retrieval


def render_chat_panel(
    *,
    workspace_id: str,
    default_retrieval_mode: str,
    api_adapter: ApiModeAdapter,
    api_mode: str,
    title: str = "Chat",
) -> None:
    with st.expander(title, expanded=False):
        ready, reason = llm_ready(
            st.session_state.get("llm_base_url", ""),
            st.session_state.get("llm_model", ""),
            st.session_state.get("llm_api_key", ""),
        )
        locked, lock_msg = running_task_summary(workspace_id)
        if api_mode == "api":
            ready = True
            reason = ""
        retrieval_mode = st.selectbox(
            "Retrieval mode",
            options=["vector", "bm25", "hybrid"],
            index=["vector", "bm25", "hybrid"].index(default_retrieval_mode)
            if default_retrieval_mode in ["vector", "bm25", "hybrid"]
            else 0,
            key=f"chat_retrieval_mode_{workspace_id}",
            help="Vector uses embeddings, BM25 uses lexical match, Hybrid fuses both.",
        )
        set_setting(workspace_id, "retrieval_mode", retrieval_mode)
        use_retrieval = st.toggle(
            "Use retrieval",
            value=True,
            disabled=api_mode == "api",
            help="API mode only supports retrieval queries.",
        )
        query = st.text_area("Ask a question", height=120)
        if st.button(
            "Send",
            key=f"chat_send_{workspace_id}",
            disabled=locked or not query.strip() or not ready,
            help=lock_msg or reason or "Ask with or without retrieval.",
        ):
            if not query.strip():
                st.error("Please enter a question.")
                return
            try:
                if use_retrieval:
                    if api_mode == "api":
                        result = api_adapter.query(
                            workspace_id=workspace_id,
                            query=query.strip(),
                            mode=retrieval_mode,
                        )
                        response = result.answer
                        hits = result.hits
                        citations = result.citations
                        run_id = result.run_id
                    else:
                        response, hits, citations, run_id = answer_with_retrieval(
                            workspace_id=workspace_id,
                            query=query.strip(),
                            mode=retrieval_mode,
                        )
                    st.success("Answer ready.")
                    st.write(response)
                    st.subheader("Retrieval hits")
                    for idx, hit in enumerate(hits, start=1):
                        if isinstance(hit, dict):
                            st.write(
                                f"[{idx}] {hit.get('filename')} p.{hit.get('page_start')}-{hit.get('page_end')} "
                                f"(score={float(hit.get('score') or 0):.4f})"
                            )
                            text = hit.get("text") or ""
                            st.caption(text[:240] + ("..." if len(text) > 240 else ""))
                        else:
                            st.write(
                                f"[{idx}] {hit.filename} p.{hit.page_start}-{hit.page_end} "
                                f"(score={hit.score:.4f})"
                            )
                            st.caption(hit.text[:240] + ("..." if len(hit.text) > 240 else ""))
                    st.subheader("Citations")
                    for citation in citations:
                        st.write(citation)
                    st.caption(
                        f"run_id: {run_id} | log: {_run_dir(workspace_id)}/run_{run_id}.json"
                    )
                    add_history(
                        workspace_id=workspace_id,
                        action_type="chat",
                        summary="Chat with retrieval",
                        preview=response[:200],
                        source_ref=None,
                        citations_count=len(citations),
                        run_id=run_id,
                    )
                    hit_records = [
                        Hit(
                            chunk_id=item.get("chunk_id", ""),
                            doc_id=item.get("doc_id", ""),
                            workspace_id=item.get("workspace_id", ""),
                            filename=item.get("filename", ""),
                            page_start=int(item.get("page_start") or 0),
                            page_end=int(item.get("page_end") or 0),
                            text=item.get("text", ""),
                            score=float(item.get("score") or 0),
                        )
                        if isinstance(item, dict)
                        else item
                        for item in hits
                    ]
                    create_asset_version(
                        workspace_id=workspace_id,
                        kind="ask",
                        ref_id=ask_ref_id(query.strip(), run_id),
                        content=response,
                        content_type="text",
                        run_id=run_id,
                        model=None,
                        provider=None,
                        temperature=None,
                        max_tokens=None,
                        retrieval_mode=retrieval_mode,
                        embed_model=None,
                        seed=None,
                        prompt_version="v1",
                        hits=hit_records,
                    )
                    st.text_area("Answer (copy)", value=response, height=200)
                    st.text_area("Citations (copy)", value="\n".join(citations), height=160)
                else:
                    response = chat(
                        prompt=query.strip(),
                        base_url=st.session_state.get("llm_base_url"),
                        api_key=st.session_state.get("llm_api_key"),
                        model=st.session_state.get("llm_model"),
                        temperature=st.session_state.get("llm_temperature"),
                    )
                    st.success("Answer ready.")
                    st.write(response)
                    llm_meta = llm_metadata(
                        temperature=st.session_state.get("llm_temperature")
                    )
                    run_id = log_run(
                        workspace_id=workspace_id,
                        action_type="chat",
                        input_payload={"query": query.strip()},
                        retrieval_mode="none",
                        hits=[],
                        model=llm_meta["model"],
                        provider=llm_meta["provider"],
                        temperature=llm_meta["temperature"],
                        max_tokens=llm_meta["max_tokens"],
                        embed_model=llm_meta["embed_model"],
                        seed=llm_meta["seed"],
                        prompt_version=None,
                        latency_ms=0,
                        citation_incomplete=None,
                        errors=None,
                    )
                    st.caption(
                        f"run_id: {run_id} | log: {_run_dir(workspace_id)}/run_{run_id}.json"
                    )
                    add_history(
                        workspace_id=workspace_id,
                        action_type="chat",
                        summary="Chat (no retrieval)",
                        preview=response[:200],
                        source_ref=None,
                        citations_count=0,
                        run_id=run_id,
                    )
                    create_asset_version(
                        workspace_id=workspace_id,
                        kind="ask",
                        ref_id=ask_ref_id(query.strip(), run_id),
                        content=response,
                        content_type="text",
                        run_id=run_id,
                        model=None,
                        provider=None,
                        temperature=None,
                        max_tokens=None,
                        retrieval_mode="none",
                        embed_model=None,
                        seed=None,
                        prompt_version="v1",
                        hits=[],
                    )
                    st.text_area("Answer (copy)", value=response, height=200)
            except ChatConfigError as exc:
                st.error(str(exc))
            except RetrievalError as exc:
                st.error(str(exc))
            except ApiModeError as exc:
                st.error(str(exc))
                if st.button("Switch to Direct Mode", key=f"api_switch_chat_{workspace_id}"):
                    st.session_state["api_mode"] = "direct"
                    set_setting(None, "api_mode", "direct")
            except Exception:
                st.error("LLM request failed. Please check your network or key.")

        st.subheader("Recent chats")
        recent = [item for item in list_history(workspace_id, "chat")[:5]]
        if not recent:
            st.caption("No chat history yet.")
        else:
            for entry in recent:
                st.write(f"{entry['created_at']} · {entry['summary']}")
                if entry.get("preview"):
                    st.caption(entry["preview"][:160])

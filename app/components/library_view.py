from __future__ import annotations

import streamlit as st

from app.components.dialogs import confirm_action
from app.components.inspector import render_citations, render_metadata, render_run_info
from core.ingest.cite import build_citation
from core.ui_state.storage import add_history, set_setting
from infra.db import get_connection, get_workspaces_dir
from service.document_service import (
    add_document_tags,
    delete_document_by_id,
    list_document_tags,
    list_documents,
)
from service.ingest_service import IngestError, get_random_chunks
from service.retrieval_service import build_or_refresh_index
from service.api_mode_adapter import ApiModeAdapter, ApiModeError


def _doc_preview(doc_id: str, limit: int = 2) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT page_start, page_end, text
            FROM chunks
            WHERE doc_id = ?
            ORDER BY chunk_index ASC
            LIMIT ?
            """,
            (doc_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def render_library_view(
    *,
    left: st.delta_generator.DeltaGenerator,
    center: st.delta_generator.DeltaGenerator,
    right: st.delta_generator.DeltaGenerator,
    workspace_id: str,
    api_adapter: ApiModeAdapter,
) -> None:
    docs = list_documents(workspace_id)
    tags_map = {doc["id"]: list_document_tags(doc["id"]) for doc in docs}
    all_tags = sorted({tag for tags in tags_map.values() for tag in tags})

    with left:
        st.markdown("### Library")
        search = st.text_input("Search", key="library_search", placeholder="Search documents")
        tag_filter = st.selectbox(
            "Tag filter",
            options=["(all)"] + all_tags,
            index=0,
            help="Filter documents by tag.",
        )
        sort_mode = st.selectbox(
            "Sort",
            options=["Newest", "Name A-Z"],
            index=0,
        )
        filtered = []
        for doc in docs:
            if search and search.lower() not in doc["filename"].lower():
                continue
            if tag_filter != "(all)" and tag_filter not in tags_map.get(doc["id"], []):
                continue
            filtered.append(doc)
        if sort_mode == "Name A-Z":
            filtered = sorted(filtered, key=lambda item: item["filename"].lower())
        else:
            filtered = sorted(filtered, key=lambda item: item["created_at"], reverse=True)

        if not filtered:
            st.info("No documents yet. Upload a PDF to get started.")
        selected_doc_id = st.session_state.get("selected_doc_id")
        for doc in filtered:
            is_selected = doc["id"] == selected_doc_id
            with st.container():
                st.markdown(f"**{doc['filename']}**")
                meta = f"{doc.get('page_count') or 0} pages · {doc['created_at'][:10]}"
                if tags_map.get(doc["id"]):
                    meta = f"{meta} · {', '.join(tags_map[doc['id']])}"
                st.caption(meta)
                if st.button(
                    "Select",
                    key=f"select_doc_{doc['id']}",
                    disabled=is_selected,
                ):
                    st.session_state["selected_doc_id"] = doc["id"]
                    selected_doc_id = doc["id"]

    selected_doc = None
    for doc in docs:
        if doc["id"] == st.session_state.get("selected_doc_id"):
            selected_doc = doc
            break

    with center:
        st.markdown("### Upload PDFs")
        uploads = st.file_uploader(
            "Drop PDFs here",
            type=["pdf"],
            accept_multiple_files=True,
        )
        if st.button(
            "Ingest files",
            disabled=not uploads,
            help="Extract text and save into this workspace.",
        ):
            with st.status("Ingesting PDFs...", expanded=True) as status:
                for upload in uploads or []:
                    try:
                        result = api_adapter.ingest(
                            workspace_id=workspace_id,
                            filename=upload.name,
                            data=upload.getvalue(),
                            save_dir=get_workspaces_dir() / workspace_id / "uploads",
                            kind="document",
                        )
                        msg = "Skipped (already ingested)" if result.get("skipped") else "Ingested"
                        st.write(
                            f"{upload.name}: {msg} ({result.get('chunk_count', 0)} chunks)"
                        )
                    except IngestError as exc:
                        st.error(f"{upload.name}: {exc}")
                    except ApiModeError as exc:
                        st.error(str(exc))
                        if st.button("Switch to Direct Mode", key="api_switch_library"):
                            st.session_state["api_mode"] = "direct"
                            set_setting(None, "api_mode", "direct")
                    except OSError:
                        st.error(f"{upload.name}: failed to save file.")
                status.update(label="Ingestion complete.", state="complete")
            add_history(
                workspace_id=workspace_id,
                action_type="library_ingest",
                summary="Ingested PDFs",
                preview="Uploaded files to library.",
                source_ref=None,
                citations_count=0,
            )

        st.divider()
        st.markdown("### Indexing")
        if st.button(
            "Build/Refresh Vector Index",
            disabled=not docs,
            help="Required for vector retrieval.",
        ):
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

        if not selected_doc:
            st.info("Select a document from the left to view details.")
            return

        st.divider()
        st.markdown("### Document Preview")
        preview = _doc_preview(selected_doc["id"])
        if not preview:
            st.caption("No chunks available for preview.")
        else:
            for chunk in preview:
                st.write(chunk["text"][:600] + ("..." if len(chunk["text"]) > 600 else ""))
                st.caption(f"Pages {chunk['page_start']}-{chunk['page_end']}")

        st.markdown("### Tags")
        tag_input = st.text_input(
            "Add tags (comma-separated)",
            key="library_tags_input",
            placeholder="e.g. calculus, week1, summary",
        )
        if st.button(
            "Save tags",
            disabled=not tag_input.strip(),
            help="Add tags for filtering and organization.",
        ):
            add_document_tags(selected_doc["id"], [tag.strip() for tag in tag_input.split(",")])
            st.success("Tags saved. Refresh to see updates.")

        st.markdown("### Actions")
        if confirm_action(
            key="confirm_delete_doc",
            label="Confirm document delete",
            help_text="This removes document metadata and chunks.",
        ):
            if st.button("Delete document", type="primary"):
                delete_document_by_id(workspace_id, selected_doc["id"])
                st.success("Document deleted. Refresh list.")

        if st.button("Show sample chunks"):
            samples = get_random_chunks(selected_doc["id"], limit=3)
            if not samples:
                st.info("No chunks available.")
            for chunk in samples:
                st.caption(
                    f"Pages {chunk['page_start']}-{chunk['page_end']} · "
                    f"{chunk['text'][:200]}{'...' if len(chunk['text']) > 200 else ''}"
                )

    with right:
        st.markdown("### Inspector")
        if not selected_doc:
            st.caption("No document selected.")
            return
        metadata = {
            "Filename": selected_doc["filename"],
            "Pages": str(selected_doc.get("page_count") or 0),
            "Uploaded": selected_doc["created_at"][:19],
            "Path": selected_doc["path"],
        }
        render_metadata(metadata)
        st.divider()
        st.markdown("#### Sample citations")
        samples = get_random_chunks(selected_doc["id"], limit=2)
        citations = []
        for chunk in samples:
            citation = build_citation(
                filename=selected_doc["filename"],
                page_start=chunk["page_start"],
                page_end=chunk["page_end"],
                text=chunk["text"],
            )
            citations.append(citation.render())
        render_citations(citations)
        render_run_info(workspace_id, None)

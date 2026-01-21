from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.ingest.cite import build_citation
from core.retrieval.embedder import (
    EmbeddingError,
    EmbeddingSettings,
    build_embedding_settings,
    embed_texts,
)
from core.retrieval.retriever import Hit, retrieve
from core.retrieval.vector_store import VectorStore, VectorStoreSettings
from infra.db import get_connection, get_workspaces_dir
from service.chat_service import ChatConfigError, chat


class RetrievalError(RuntimeError):
    pass


@dataclass
class IndexResult:
    doc_count: int
    chunk_count: int
    indexed_count: int


def _index_dir(workspace_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "index" / "chroma"


def _collection_name(workspace_id: str) -> str:
    return f"workspace_{workspace_id}"


def _fetch_chunks(workspace_id: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT chunks.id as chunk_id,
                   chunks.doc_id as doc_id,
                   chunks.workspace_id as workspace_id,
                   chunks.chunk_index as chunk_index,
                   chunks.page_start as page_start,
                   chunks.page_end as page_end,
                   chunks.text as text,
                   documents.filename as filename
            FROM chunks
            JOIN documents ON documents.id = chunks.doc_id
            WHERE chunks.workspace_id = ?
            ORDER BY chunks.doc_id, chunks.chunk_index
            """,
            (workspace_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _fetch_doc_count(workspace_id: str) -> int:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) as count FROM documents WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
    return int(row["count"]) if row else 0


def _build_store(workspace_id: str) -> VectorStore:
    settings = VectorStoreSettings(
        persist_directory=_index_dir(workspace_id),
        collection_name=_collection_name(workspace_id),
    )
    return VectorStore(settings)


def build_or_refresh_index(
    *,
    workspace_id: str,
    reset: bool = True,
    batch_size: int = 32,
    progress_cb: callable | None = None,
) -> IndexResult:
    chunks = _fetch_chunks(workspace_id)
    if not chunks:
        raise RetrievalError("No chunks available. Please ingest a PDF first.")

    try:
        embed_settings = build_embedding_settings()
    except EmbeddingError as exc:
        raise RetrievalError(str(exc)) from exc
    store = _build_store(workspace_id)
    if reset:
        store.reset()

    total = len(chunks)
    indexed_count = 0
    for start in range(0, total, batch_size):
        batch = chunks[start : start + batch_size]
        texts = [item["text"] for item in batch]
        try:
            embeddings = embed_texts(texts, embed_settings)
        except EmbeddingError as exc:
            raise RetrievalError(str(exc)) from exc
        store.upsert(
            ids=[item["chunk_id"] for item in batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {
                    "chunk_id": item["chunk_id"],
                    "doc_id": item["doc_id"],
                    "workspace_id": item["workspace_id"],
                    "filename": item["filename"],
                    "page_start": item["page_start"],
                    "page_end": item["page_end"],
                }
                for item in batch
            ],
        )
        indexed_count += len(batch)
        if progress_cb:
            progress_cb(indexed_count, total)

    return IndexResult(
        doc_count=_fetch_doc_count(workspace_id),
        chunk_count=total,
        indexed_count=indexed_count,
    )


def ensure_index(workspace_id: str) -> None:
    store = _build_store(workspace_id)
    if store.count() == 0:
        build_or_refresh_index(workspace_id=workspace_id, reset=True)


def retrieve_hits(
    *,
    workspace_id: str,
    query: str,
    top_k: int = 8,
) -> list[Hit]:
    ensure_index(workspace_id)
    try:
        embed_settings = build_embedding_settings()
    except EmbeddingError as exc:
        raise RetrievalError(str(exc)) from exc
    store = _build_store(workspace_id)
    try:
        return retrieve(
            query=query, embed_settings=embed_settings, store=store, top_k=top_k
        )
    except EmbeddingError as exc:
        raise RetrievalError(str(exc)) from exc


def _build_context(hits: list[Hit], max_chars: int = 3500) -> str:
    parts: list[str] = []
    total = 0
    for idx, hit in enumerate(hits, start=1):
        snippet = hit.text.strip().replace("\n", " ")
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        entry = f"[{idx}] {snippet}"
        if total + len(entry) > max_chars:
            break
        parts.append(entry)
        total += len(entry)
    return "\n".join(parts)


def answer_with_retrieval(
    *,
    workspace_id: str,
    query: str,
    top_k: int = 8,
) -> tuple[str, list[Hit], list[str]]:
    hits = retrieve_hits(workspace_id=workspace_id, query=query, top_k=top_k)
    if not hits:
        raise RetrievalError("No retrieval hits found. Try another query.")

    context = _build_context(hits)
    prompt = (
        "Answer the question using the context below. "
        "Cite sources with [n] inline.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}"
    )
    answer = chat(prompt=prompt)

    citations = []
    for idx, hit in enumerate(hits, start=1):
        citation = build_citation(
            filename=hit.filename,
            page_start=hit.page_start,
            page_end=hit.page_end,
            text=hit.text,
        )
        citations.append(f"[{idx}] {citation.render()}")

    return answer, hits, citations

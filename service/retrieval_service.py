from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib

from core.ingest.cite import build_citation
from core.retrieval.embedder import (
    EmbeddingError,
    EmbeddingSettings,
    build_embedding_settings,
    embed_texts,
)
from core.retrieval.embedding_cache import CacheEntry, get_cached_embeddings, put_cached_embeddings
import os
import time

from core.retrieval.retriever import Hit, retrieve
from core.retrieval.bm25_index import build_bm25_index, query_bm25, load_bm25_index
from core.retrieval.hybrid import fuse_scores
from core.prompts.instructions import (
    general_knowledge_label,
    grounded_label,
    language_instruction,
    rag_balance_instruction,
    normalize_language,
)
from core.telemetry.run_logger import log_run
from core.retrieval.vector_store import VectorStore, VectorStoreSettings
from infra.db import get_connection, get_workspaces_dir
from service.chat_service import ChatConfigError, chat
from core.quality.citations_check import check_citations
from service.metadata_service import llm_metadata
from service.document_service import filter_doc_ids_by_types
from core.ui_state.storage import get_setting


class RetrievalError(RuntimeError):
    pass


@dataclass
class IndexResult:
    doc_count: int
    chunk_count: int
    indexed_count: int


def _index_dir(workspace_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "index" / "chroma"


def _bm25_index_dir(workspace_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "index" / "bm25"


def _collection_name(workspace_id: str) -> str:
    return f"workspace_{workspace_id}"


def _chunk_query(doc_ids: list[str] | None = None) -> tuple[str, tuple]:
    if doc_ids:
        placeholders = ",".join(["?"] * len(doc_ids))
        query = f"""
            SELECT chunks.id as chunk_id,
                   chunks.doc_id as doc_id,
                   chunks.workspace_id as workspace_id,
                   chunks.chunk_index as chunk_index,
                   chunks.page_start as page_start,
                   chunks.page_end as page_end,
                   chunks.text as text,
                   documents.filename as filename,
                   documents.doc_type as doc_type
            FROM chunks
            JOIN documents ON documents.id = chunks.doc_id
            WHERE chunks.workspace_id = ? AND chunks.doc_id IN ({placeholders})
            ORDER BY chunks.doc_id, chunks.chunk_index
            LIMIT ? OFFSET ?
            """
        return query, tuple(doc_ids)
    query = """
        SELECT chunks.id as chunk_id,
               chunks.doc_id as doc_id,
               chunks.workspace_id as workspace_id,
               chunks.chunk_index as chunk_index,
               chunks.page_start as page_start,
               chunks.page_end as page_end,
               chunks.text as text,
               documents.filename as filename,
               documents.doc_type as doc_type
        FROM chunks
        JOIN documents ON documents.id = chunks.doc_id
        WHERE chunks.workspace_id = ?
        ORDER BY chunks.doc_id, chunks.chunk_index
        LIMIT ? OFFSET ?
        """
    return query, tuple()


def _fetch_chunk_batch(
    workspace_id: str, doc_ids: list[str] | None, limit: int, offset: int
) -> list[dict]:
    query, doc_params = _chunk_query(doc_ids)
    params = (workspace_id, *doc_params, limit, offset)
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def _count_chunks(workspace_id: str, doc_ids: list[str] | None = None) -> int:
    if doc_ids:
        placeholders = ",".join(["?"] * len(doc_ids))
        query = f"SELECT COUNT(*) as count FROM chunks WHERE workspace_id = ? AND doc_id IN ({placeholders})"
        params = (workspace_id, *doc_ids)
    else:
        query = "SELECT COUNT(*) as count FROM chunks WHERE workspace_id = ?"
        params = (workspace_id,)
    with get_connection() as connection:
        row = connection.execute(query, params).fetchone()
    return int(row["count"]) if row else 0


def get_chunks_for_documents(doc_ids: list[str]) -> list[dict]:
    if not doc_ids:
        return []
    placeholders = ",".join(["?"] * len(doc_ids))
    with get_connection() as connection:
        rows = connection.execute(
            f"""
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
            WHERE chunks.doc_id IN ({placeholders})
            ORDER BY chunks.doc_id, chunks.chunk_index
            """,
            tuple(doc_ids),
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
    doc_ids: list[str] | None = None,
    progress_cb: callable | None = None,
    stop_check: callable | None = None,
) -> IndexResult:
    total = _count_chunks(workspace_id, doc_ids)
    if total == 0:
        raise RetrievalError("No chunks available. Please ingest a PDF first.")

    try:
        embed_settings = build_embedding_settings()
    except EmbeddingError as exc:
        raise RetrievalError(str(exc)) from exc
    store = _build_store(workspace_id)
    if reset:
        store.reset()

    indexed_count = 0
    cache_enabled = os.getenv("STUDYFLOW_EMBED_CACHE", "off").lower() in (
        "1",
        "true",
        "on",
        "yes",
    )
    cache_path = (
        get_workspaces_dir() / workspace_id / "cache" / "embeddings.sqlite"
        if cache_enabled
        else None
    )
    for start in range(0, total, batch_size):
        if stop_check and stop_check():
            raise RetrievalError("Indexing stopped by user.")
        batch = _fetch_chunk_batch(workspace_id, doc_ids, batch_size, start)
        texts = [item["text"] for item in batch]
        embeddings: list[list[float]] = []
        cache_entries: list[CacheEntry] = []
        if cache_path:
            keys = [
                hashlib.sha256(
                    f"{embed_settings.model}:{text}".encode("utf-8")
                ).hexdigest()
                for text in texts
            ]
            cached = get_cached_embeddings(cache_path, keys)
            missing_texts: list[str] = []
            missing_keys: list[str] = []
            missing_positions: list[int] = []
            embeddings = [None] * len(texts)
            for index, (key, text) in enumerate(zip(keys, texts)):
                if key in cached:
                    embeddings[index] = cached[key]
                else:
                    missing_keys.append(key)
                    missing_texts.append(text)
                    missing_positions.append(index)
            if missing_texts:
                try:
                    computed = embed_texts(missing_texts, embed_settings)
                except EmbeddingError as exc:
                    raise RetrievalError(str(exc)) from exc
                for key, vector, position in zip(
                    missing_keys, computed, missing_positions
                ):
                    embeddings[position] = vector
                    cache_entries.append(
                        CacheEntry(
                            key=key,
                            vector=vector,
                            model=embed_settings.model,
                            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        )
                    )
                put_cached_embeddings(cache_path, cache_entries)
            embeddings = [item for item in embeddings if item is not None]
        else:
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
                "doc_type": item.get("doc_type") or "other",
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


def ensure_bm25_index(workspace_id: str) -> Path:
    index = load_bm25_index(workspace_id)
    if index is None:
        return build_bm25_index(workspace_id)
    return _bm25_index_dir(workspace_id) / "index.pkl"


def index_status(workspace_id: str) -> dict:
    chunk_count = _count_chunks(workspace_id)
    doc_count = _fetch_doc_count(workspace_id)
    orphan_chunks = _count_orphan_chunks(workspace_id)
    vector_count = 0
    try:
        store = _build_store(workspace_id)
        vector_count = store.count()
    except Exception:
        vector_count = -1
    bm25_path = _bm25_index_dir(workspace_id) / "index.pkl"
    return {
        "workspace_id": workspace_id,
        "doc_count": doc_count,
        "chunk_count": chunk_count,
        "orphan_chunks": orphan_chunks,
        "vector_count": vector_count,
        "bm25_exists": bm25_path.exists(),
    }


def _count_orphan_chunks(workspace_id: str) -> int:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) as count
            FROM chunks
            LEFT JOIN documents ON documents.id = chunks.doc_id
            WHERE chunks.workspace_id = ? AND documents.id IS NULL
            """,
            (workspace_id,),
        ).fetchone()
    return int(row["count"]) if row else 0


def vacuum_index(workspace_id: str) -> dict:
    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM document_pages
            WHERE doc_id NOT IN (SELECT id FROM documents)
            """
        )
        connection.execute(
            """
            DELETE FROM chunks
            WHERE doc_id NOT IN (SELECT id FROM documents)
            """
        )
        connection.commit()
    status = index_status(workspace_id)
    if status["chunk_count"] == 0:
        return status
    if status["vector_count"] != status["chunk_count"]:
        build_or_refresh_index(workspace_id=workspace_id, reset=True)
    build_bm25_index(workspace_id)
    return index_status(workspace_id)


def retrieve_hits(
    *,
    workspace_id: str,
    query: str,
    top_k: int = 8,
    doc_ids: list[str] | None = None,
    doc_types: list[str] | None = None,
) -> list[Hit]:
    if doc_ids and doc_types:
        doc_ids = filter_doc_ids_by_types(doc_ids, doc_types)
        doc_types = None
    ensure_index(workspace_id)
    try:
        embed_settings = build_embedding_settings()
    except EmbeddingError as exc:
        raise RetrievalError(str(exc)) from exc
    store = _build_store(workspace_id)
    try:
        return retrieve(
            query=query,
            embed_settings=embed_settings,
            store=store,
            top_k=top_k,
            doc_ids=doc_ids,
        doc_types=doc_types,
        )
    except EmbeddingError as exc:
        raise RetrievalError(str(exc)) from exc


def retrieve_hits_mode(
    *,
    workspace_id: str,
    query: str,
    mode: str,
    top_k: int = 8,
    doc_ids: list[str] | None = None,
    doc_types: list[str] | None = None,
    max_per_doc: int | None = None,
    min_docs: int | None = None,
) -> tuple[list[Hit], str]:
    if doc_ids and doc_types:
        doc_ids = filter_doc_ids_by_types(doc_ids, doc_types)
        doc_types = None
    def _apply_doc_diversity(hits: list[Hit]) -> list[Hit]:
        if not hits or not max_per_doc:
            return hits
        doc_counts: dict[str, int] = {}
        seen_chunks: set[str] = set()
        balanced: list[Hit] = []

        if min_docs:
            for hit in hits:
                if hit.chunk_id in seen_chunks:
                    continue
                if hit.doc_id in doc_counts:
                    continue
                balanced.append(hit)
                seen_chunks.add(hit.chunk_id)
                doc_counts[hit.doc_id] = 1
                if len(doc_counts) >= min_docs:
                    break

        for hit in hits:
            if hit.chunk_id in seen_chunks:
                continue
            count = doc_counts.get(hit.doc_id, 0)
            if count >= max_per_doc:
                continue
            balanced.append(hit)
            seen_chunks.add(hit.chunk_id)
            doc_counts[hit.doc_id] = count + 1
            if len(balanced) >= top_k:
                break

        return balanced

    if mode == "vector":
        candidate_k = top_k
        if max_per_doc and doc_ids and len(doc_ids) > 1:
            candidate_k = max(top_k * 3, 20)
        hits = retrieve_hits(
            workspace_id=workspace_id,
            query=query,
            top_k=candidate_k,
            doc_ids=doc_ids,
            doc_types=doc_types,
        )
        if max_per_doc and doc_ids and len(doc_ids) > 1:
            hits = _apply_doc_diversity(hits)
        hits = hits[:top_k]
        return hits, "vector"
    if mode == "bm25":
        ensure_bm25_index(workspace_id)
        candidate_k = 20
        if max_per_doc and doc_ids and len(doc_ids) > 1:
            candidate_k = max(top_k * 3, 20)
        results = query_bm25(
            workspace_id=workspace_id,
            query=query,
            top_k=candidate_k,
            doc_ids=doc_ids,
            doc_types=doc_types,
        )
        hits = [
            Hit(
                chunk_id=item["chunk_id"],
                doc_id=item["doc_id"],
                workspace_id=item["workspace_id"],
                filename=item["filename"],
                page_start=item["page_start"],
                page_end=item["page_end"],
                text=item["text"],
                score=item["score"],
            )
            for item in results[:candidate_k]
        ]
        if max_per_doc and doc_ids and len(doc_ids) > 1:
            hits = _apply_doc_diversity(hits)
        hits = hits[:top_k]
        return hits, "bm25"

    if mode == "hybrid":
        bm25_results = query_bm25(
            workspace_id=workspace_id,
            query=query,
            top_k=20,
            doc_ids=doc_ids,
            doc_types=doc_types,
        )
        try:
            candidate_k = 20
            if max_per_doc and doc_ids and len(doc_ids) > 1:
                candidate_k = max(top_k * 3, 20)
            vector_hits = retrieve_hits(
                workspace_id=workspace_id,
                query=query,
                top_k=candidate_k,
                doc_ids=doc_ids,
                doc_types=doc_types,
            )
            vec_dicts = [
                {
                    "chunk_id": hit.chunk_id,
                    "doc_id": hit.doc_id,
                    "workspace_id": hit.workspace_id,
                    "filename": hit.filename,
                    "page_start": hit.page_start,
                    "page_end": hit.page_end,
                    "text": hit.text,
                    "score": hit.score,
                }
                for hit in vector_hits
            ]
            fused = fuse_scores(
                vector_hits=vec_dicts, bm25_hits=bm25_results, top_k=candidate_k
            )
            hits = [
                Hit(
                    chunk_id=item.chunk_id,
                    doc_id=item.doc_id,
                    workspace_id=item.workspace_id,
                    filename=item.filename,
                    page_start=item.page_start,
                    page_end=item.page_end,
                    text=item.text,
                    score=item.score,
                )
                for item in fused
            ]
            if max_per_doc and doc_ids and len(doc_ids) > 1:
                hits = _apply_doc_diversity(hits)
            hits = hits[:top_k]
            return hits, "hybrid"
        except RetrievalError:
            # fallback to BM25 if vector fails
            hits = [
                Hit(
                    chunk_id=item["chunk_id"],
                    doc_id=item["doc_id"],
                    workspace_id=item["workspace_id"],
                    filename=item["filename"],
                    page_start=item["page_start"],
                    page_end=item["page_end"],
                    text=item["text"],
                    score=item["score"],
                )
                for item in bm25_results[:top_k]
            ]
            if max_per_doc and doc_ids and len(doc_ids) > 1:
                hits = _apply_doc_diversity(hits)
            hits = hits[:top_k]
            return hits, "bm25"

    raise RetrievalError("Unknown retrieval mode.")


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
    mode: str = "vector",
    top_k: int = 8,
) -> tuple[str, list[Hit], list[str], str]:
    start = time.time()
    hits, used_mode = retrieve_hits_mode(
        workspace_id=workspace_id, query=query, mode=mode, top_k=top_k
    )
    if not hits:
        raise RetrievalError("No retrieval hits found. Try another query.")

    context = _build_context(hits)
    language = get_setting(workspace_id, "output_language") or get_setting(
        None, "output_language"
    )
    lang = normalize_language(language or "en")
    grounded = grounded_label(lang)
    general = general_knowledge_label(lang)
    prompt = (
        "Answer the question using the context below.\n"
        f"{language_instruction(lang)}\n"
        f"{rag_balance_instruction(lang)}"
        f"Output format:\n- {grounded}: include citations like [n]\n- {general}: no citations\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}"
    )
    try:
        answer = chat(prompt=prompt)
    except ChatConfigError as exc:
        raise RetrievalError(
            "LLM not configured. Set STUDYFLOW_LLM_BASE_URL/STUDYFLOW_LLM_MODEL/STUDYFLOW_LLM_API_KEY."
        ) from exc

    citations = []
    for idx, hit in enumerate(hits, start=1):
        citation = build_citation(
            filename=hit.filename,
            page_start=hit.page_start,
            page_end=hit.page_end,
            text=hit.text,
        )
        citations.append(f"[{idx}] {citation.render()}")

    latency_ms = int((time.time() - start) * 1000)
    meta = llm_metadata(temperature=None)
    citation_ok, citation_error = check_citations(answer, hits)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="chat",
        input_payload={"query": query},
        retrieval_mode=used_mode,
        hits=hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=None,
        latency_ms=latency_ms,
        citation_incomplete=not citation_ok,
        errors=citation_error,
    )

    return answer, hits, citations, run_id

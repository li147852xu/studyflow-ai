from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

from infra.db import get_connection, get_workspaces_dir


@dataclass
class BM25Index:
    bm25: BM25Okapi
    chunk_ids: list[str]
    metadatas: list[dict]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _index_path(workspace_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "index" / "bm25" / "index.pkl"


def build_bm25_index(workspace_id: str) -> Path:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT chunks.id as chunk_id,
                   chunks.doc_id as doc_id,
                   chunks.workspace_id as workspace_id,
                   chunks.page_start as page_start,
                   chunks.page_end as page_end,
                   chunks.text as text,
                   documents.filename as filename,
                   documents.file_type as file_type,
                   documents.doc_type as doc_type
            FROM chunks
            JOIN documents ON documents.id = chunks.doc_id
            WHERE chunks.workspace_id = ?
            ORDER BY chunks.doc_id, chunks.chunk_index
            """,
            (workspace_id,),
        ).fetchall()
    chunks = [dict(row) for row in rows]
    if not chunks:
        raise RuntimeError("No chunks available for BM25 index.")

    corpus = [chunk["text"] for chunk in chunks]
    tokenized = [_tokenize(text) for text in corpus]
    bm25 = BM25Okapi(tokenized)

    index = BM25Index(
        bm25=bm25,
        chunk_ids=[chunk["chunk_id"] for chunk in chunks],
        metadatas=[
            {
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "workspace_id": chunk["workspace_id"],
                "filename": chunk["filename"],
                "file_type": chunk.get("file_type"),
                "doc_type": chunk.get("doc_type") or "other",
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "text": chunk["text"],
            }
            for chunk in chunks
        ],
    )

    path = _index_path(workspace_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(index, handle)
    return path


def load_bm25_index(workspace_id: str) -> BM25Index | None:
    path = _index_path(workspace_id)
    if not path.exists():
        return None
    with path.open("rb") as handle:
        return pickle.load(handle)


def query_bm25(
    *,
    workspace_id: str,
    query: str,
    top_k: int = 20,
    doc_ids: list[str] | None = None,
    doc_types: list[str] | None = None,
) -> list[dict]:
    index = load_bm25_index(workspace_id)
    if index is None:
        build_bm25_index(workspace_id)
        index = load_bm25_index(workspace_id)
        if index is None:
            raise RuntimeError("Failed to load BM25 index.")

    scores = index.bm25.get_scores(_tokenize(query))
    scored = list(zip(index.metadatas, scores))
    if doc_ids:
        scored = [item for item in scored if item[0]["doc_id"] in doc_ids]
    if doc_types:
        scored = [item for item in scored if item[0].get("doc_type") in doc_types]
    scored.sort(key=lambda x: x[1], reverse=True)
    results = []
    for metadata, score in scored[:top_k]:
        results.append(
            {
                "chunk_id": metadata["chunk_id"],
                "doc_id": metadata["doc_id"],
                "workspace_id": metadata["workspace_id"],
                "filename": metadata["filename"],
                "page_start": metadata["page_start"],
                "page_end": metadata["page_end"],
                "text": metadata["text"],
                "score": float(score),
            }
        )
    return results

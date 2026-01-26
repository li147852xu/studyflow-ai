from __future__ import annotations

from dataclasses import dataclass

from core.retrieval.embedder import EmbeddingSettings, embed_texts
from core.retrieval.vector_store import VectorStore


@dataclass
class Hit:
    chunk_id: str
    doc_id: str
    workspace_id: str
    filename: str
    page_start: int
    page_end: int
    text: str
    score: float


def retrieve(
    *,
    query: str,
    embed_settings: EmbeddingSettings,
    store: VectorStore,
    top_k: int = 8,
    doc_ids: list[str] | None = None,
    doc_types: list[str] | None = None,
) -> list[Hit]:
    embedding = embed_texts([query], embed_settings)[0]
    where = None
    if doc_ids and doc_types:
        where = {"$and": [{"doc_id": {"$in": doc_ids}}, {"doc_type": {"$in": doc_types}}]}
    elif doc_ids:
        where = {"doc_id": {"$in": doc_ids}}
    elif doc_types:
        where = {"doc_type": {"$in": doc_types}}
    result = store.query(embedding=embedding, top_k=top_k, where=where)
    metadatas = result.get("metadatas", [[]])[0]
    documents = result.get("documents", [[]])[0]
    distances = result.get("distances", [[]])[0]

    hits: list[Hit] = []
    for metadata, doc_text, distance in zip(metadatas, documents, distances):
        similarity = 1.0 / (1.0 + float(distance))
        hits.append(
            Hit(
                chunk_id=metadata["chunk_id"],
                doc_id=metadata["doc_id"],
                workspace_id=metadata["workspace_id"],
                filename=metadata["filename"],
                page_start=int(metadata["page_start"]),
                page_end=int(metadata["page_end"]),
                text=doc_text,
                score=similarity,
            )
        )
    return hits

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
) -> list[Hit]:
    embedding = embed_texts([query], embed_settings)[0]
    result = store.query(embedding=embedding, top_k=top_k)
    metadatas = result.get("metadatas", [[]])[0]
    documents = result.get("documents", [[]])[0]
    distances = result.get("distances", [[]])[0]

    hits: list[Hit] = []
    for metadata, doc_text, distance in zip(metadatas, documents, distances):
        hits.append(
            Hit(
                chunk_id=metadata["chunk_id"],
                doc_id=metadata["doc_id"],
                workspace_id=metadata["workspace_id"],
                filename=metadata["filename"],
                page_start=int(metadata["page_start"]),
                page_end=int(metadata["page_end"]),
                text=doc_text,
                score=float(distance),
            )
        )
    return hits

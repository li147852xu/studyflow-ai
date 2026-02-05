from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoredHit:
    chunk_id: str
    doc_id: str
    workspace_id: str
    filename: str
    page_start: int
    page_end: int
    text: str
    score: float
    file_type: str | None = None


VECTOR_WEIGHT = 0.55
BM25_WEIGHT = 0.45


def _min_max(values: list[float]) -> list[float]:
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        return [1.0 for _ in values]
    return [(val - vmin) / (vmax - vmin) for val in values]


def fuse_scores(
    *,
    vector_hits: list[dict],
    bm25_hits: list[dict],
    top_k: int = 8,
) -> list[ScoredHit]:
    combined = {}

    vec_scores = [hit["score"] for hit in vector_hits]
    bm_scores = [hit["score"] for hit in bm25_hits]
    vec_norm = _min_max(vec_scores)
    bm_norm = _min_max(bm_scores)

    for hit, norm in zip(vector_hits, vec_norm):
        combined[hit["chunk_id"]] = {
            "hit": hit,
            "vec": norm,
            "bm": 0.0,
        }

    for hit, norm in zip(bm25_hits, bm_norm):
        if hit["chunk_id"] in combined:
            combined[hit["chunk_id"]]["bm"] = norm
        else:
            combined[hit["chunk_id"]] = {
                "hit": hit,
                "vec": 0.0,
                "bm": norm,
            }

    scored = []
    for entry in combined.values():
        score = entry["vec"] * VECTOR_WEIGHT + entry["bm"] * BM25_WEIGHT
        hit = entry["hit"]
        scored.append(
            ScoredHit(
                chunk_id=hit["chunk_id"],
                doc_id=hit["doc_id"],
                workspace_id=hit["workspace_id"],
                filename=hit["filename"],
                file_type=hit.get("file_type"),
                page_start=hit["page_start"],
                page_end=hit["page_end"],
                text=hit["text"],
                score=score,
            )
        )

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]

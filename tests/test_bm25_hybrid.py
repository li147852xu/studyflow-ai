from core.retrieval.hybrid import fuse_scores


def test_hybrid_fusion():
    vector_hits = [
        {"chunk_id": "c1", "doc_id": "d1", "workspace_id": "w1", "filename": "a", "page_start": 1, "page_end": 1, "text": "x", "score": 0.2},
        {"chunk_id": "c2", "doc_id": "d1", "workspace_id": "w1", "filename": "a", "page_start": 2, "page_end": 2, "text": "y", "score": 0.1},
    ]
    bm25_hits = [
        {"chunk_id": "c2", "doc_id": "d1", "workspace_id": "w1", "filename": "a", "page_start": 2, "page_end": 2, "text": "y", "score": 10.0},
    ]
    fused = fuse_scores(vector_hits=vector_hits, bm25_hits=bm25_hits, top_k=2)
    assert len(fused) == 2
    assert fused[0].chunk_id in {"c1", "c2"}

from __future__ import annotations

from core.rag import classify_query, map_reduce_course_query, map_reduce_project_query
from core.ui_state.storage import get_setting
from service.retrieval_service import answer_with_retrieval


def _token_budget(workspace_id: str | None) -> tuple[int, int]:
    map_tokens = int(get_setting(workspace_id, "rag_map_tokens") or 250)
    reduce_tokens = int(get_setting(workspace_id, "rag_reduce_tokens") or 600)
    return map_tokens, reduce_tokens


def course_query(
    *,
    workspace_id: str,
    course_id: str,
    query: str,
    doc_ids: list[str],
) -> dict:
    query_type = classify_query(query)
    if query_type == "global":
        map_tokens, reduce_tokens = _token_budget(workspace_id)
        result = map_reduce_course_query(
            workspace_id=workspace_id,
            course_id=course_id,
            query=query,
            map_tokens=map_tokens,
            reduce_tokens=reduce_tokens,
        )
        return {
            "answer": result.answer,
            "coverage": result.coverage,
            "citations": result.citations,
            "query_type": "global",
        }
    mode = get_setting(workspace_id, "retrieval_mode") or "hybrid"
    answer, hits, citations, run_id = answer_with_retrieval(
        workspace_id=workspace_id, query=query, mode=mode, top_k=8, doc_ids=doc_ids
    )
    return {
        "answer": answer,
        "hits": hits,
        "citations": citations,
        "run_id": run_id,
        "query_type": "local",
    }


def project_query(
    *,
    workspace_id: str,
    project_id: str,
    query: str,
    doc_ids: list[str],
) -> dict:
    query_type = classify_query(query)
    if query_type == "global":
        map_tokens, reduce_tokens = _token_budget(workspace_id)
        result = map_reduce_project_query(
            workspace_id=workspace_id,
            project_id=project_id,
            query=query,
            map_tokens=map_tokens,
            reduce_tokens=reduce_tokens,
        )
        return {
            "answer": result.answer,
            "coverage": result.coverage,
            "citations": result.citations,
            "query_type": "global",
        }
    mode = get_setting(workspace_id, "retrieval_mode") or "hybrid"
    answer, hits, citations, run_id = answer_with_retrieval(
        workspace_id=workspace_id, query=query, mode=mode, top_k=8, doc_ids=doc_ids
    )
    return {
        "answer": answer,
        "hits": hits,
        "citations": citations,
        "run_id": run_id,
        "query_type": "local",
    }

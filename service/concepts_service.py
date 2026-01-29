from __future__ import annotations

import time

from core.concepts.builder import build_concepts
from core.concepts.store import (
    add_evidence,
    create_card,
    get_processing_mark,
    upsert_processing_mark,
)
from core.ingest.cite import build_citation
from core.telemetry.run_logger import log_run
from service.course_service import list_course_doc_ids
from service.document_service import get_document
from service.metadata_service import llm_metadata
from service.paper_service import list_papers


class ConceptsServiceError(RuntimeError):
    pass


def _resolve_doc_ids(
    *, workspace_id: str, paper_ids: list[str] | None, course_id: str | None
) -> list[str]:
    if course_id:
        return list_course_doc_ids(course_id)
    if paper_ids:
        papers = [paper for paper in list_papers(workspace_id) if paper["id"] in paper_ids]
        return [paper["doc_id"] for paper in papers]
    return []


def build_concept_cards(
    *,
    workspace_id: str,
    retrieval_mode: str,
    paper_ids: list[str] | None = None,
    course_id: str | None = None,
    incremental: bool = False,
) -> dict:
    doc_ids = _resolve_doc_ids(
        workspace_id=workspace_id,
        paper_ids=paper_ids,
        course_id=course_id,
    )
    if not doc_ids:
        raise ConceptsServiceError("No documents available for concept extraction.")
    if incremental:
        pending: list[str] = []
        for doc_id in doc_ids:
            doc = get_document(doc_id)
            if not doc:
                continue
            mark = get_processing_mark(
                workspace_id=workspace_id,
                doc_id=doc_id,
                processor="concepts",
            )
            if not mark or mark.get("doc_hash") != (doc.get("sha256") or ""):
                pending.append(doc_id)
        doc_ids = pending
        if not doc_ids:
            return {"cards_created": 0, "skipped": True}
    start = time.time()
    result = build_concepts(
        workspace_id=workspace_id,
        doc_ids=doc_ids,
        retrieval_mode=retrieval_mode,
    )
    created = 0
    for card in result.cards:
        name = str(card.get("name", "")).strip()
        type_value = str(card.get("type", "definition")).strip()
        content = str(card.get("content", "")).strip()
        if not name or not content:
            continue
        card_id = create_card(
            workspace_id=workspace_id,
            name=name,
            type=type_value,
            content=content,
        )
        for idx in card.get("evidence", []):
            if not isinstance(idx, int) or idx < 1 or idx > len(result.hits):
                continue
            hit = result.hits[idx - 1]
            citation = build_citation(
                filename=hit.filename,
                page_start=hit.page_start,
                page_end=hit.page_end,
                text=hit.text,
            )
            add_evidence(
                card_id=card_id,
                doc_id=hit.doc_id,
                chunk_id=hit.chunk_id,
                page_start=hit.page_start,
                page_end=hit.page_end,
                snippet=citation.snippet,
            )
        created += 1
    latency_ms = int((time.time() - start) * 1000)
    meta = llm_metadata(temperature=0.2)
    log_run(
        workspace_id=workspace_id,
        action_type="concepts_build",
        input_payload={
            "doc_ids": doc_ids,
            "prompt_version": result.prompt_version,
        },
        retrieval_mode=result.retrieval_mode,
        hits=result.hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=result.prompt_version,
        latency_ms=latency_ms,
        errors=None,
    )
    for doc_id in doc_ids:
        doc = get_document(doc_id)
        if not doc:
            continue
        upsert_processing_mark(
            workspace_id=workspace_id,
            doc_id=doc_id,
            processor="concepts",
            doc_hash=doc.get("sha256") or "",
        )
    return {
        "cards_created": created,
        "retrieval_mode": result.retrieval_mode,
        "prompt_version": result.prompt_version,
        "citations": result.citations,
    }

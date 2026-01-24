from __future__ import annotations

import json
from dataclasses import dataclass

from core.formatting.citations import build_citation_bundle
from core.prompts.registry import build_prompt
from core.retrieval.retriever import Hit
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits_mode


class RelatedManagerError(RuntimeError):
    pass


@dataclass
class RelatedResult:
    comparison_axes: list[str]
    sections: list[dict]
    draft: str
    hits: list[Hit]
    citations: list[str]
    retrieval_mode: str
    prompt_version: str | None = None
    insert_suggestions: list[str] | None = None


def _merge_hits(batches: list[list[Hit]]) -> list[Hit]:
    seen = set()
    merged: list[Hit] = []
    for batch in batches:
        for hit in batch:
            if hit.chunk_id in seen:
                continue
            seen.add(hit.chunk_id)
            merged.append(hit)
    return merged


def build_related(
    *,
    workspace_id: str,
    doc_ids: list[str],
    topic: str,
    retrieval_mode: str,
) -> RelatedResult:
    batches: list[list[Hit]] = []
    used_mode = retrieval_mode
    for query in [topic, "related work", "comparison"]:
        hits, used_mode = retrieve_hits_mode(
            workspace_id=workspace_id,
            query=query,
            mode=retrieval_mode,
            top_k=8,
            doc_ids=doc_ids,
        )
        if hits:
            batches.append(hits)
    merged_hits = _merge_hits(batches)
    if not merged_hits:
        raise RelatedManagerError("No retrieval hits found for related work.")
    bundle = build_citation_bundle(merged_hits)
    prompt, prompt_version = build_prompt(
        "related_create",
        workspace_id,
        context=bundle.numbered_context,
        topic=topic,
    )
    try:
        response = chat(prompt=prompt, temperature=0.2)
    except ChatConfigError as exc:
        raise RelatedManagerError(str(exc)) from exc
    try:
        payload = json.loads(response)
    except json.JSONDecodeError as exc:
        raise RelatedManagerError("Related work output returned invalid JSON.") from exc
    return RelatedResult(
        comparison_axes=payload.get("comparison_axes", []),
        sections=payload.get("sections", []),
        draft=payload.get("draft", ""),
        hits=merged_hits,
        citations=bundle.citations,
        retrieval_mode=used_mode,
        prompt_version=prompt_version,
    )


def update_related(
    *,
    workspace_id: str,
    doc_ids: list[str],
    topic: str,
    existing_outline: str,
    retrieval_mode: str,
) -> RelatedResult:
    hits, used_mode = retrieve_hits_mode(
        workspace_id=workspace_id,
        query=topic,
        mode=retrieval_mode,
        top_k=8,
        doc_ids=doc_ids,
    )
    if not hits:
        raise RelatedManagerError("No retrieval hits found for related update.")
    bundle = build_citation_bundle(hits)
    prompt, prompt_version = build_prompt(
        "related_update",
        workspace_id,
        context=bundle.numbered_context,
        topic=topic,
        existing_outline=existing_outline,
    )
    try:
        response = chat(prompt=prompt, temperature=0.2)
    except ChatConfigError as exc:
        raise RelatedManagerError(str(exc)) from exc
    try:
        payload = json.loads(response)
    except json.JSONDecodeError as exc:
        raise RelatedManagerError("Related update output returned invalid JSON.") from exc
    return RelatedResult(
        comparison_axes=payload.get("comparison_axes", []),
        sections=payload.get("sections", []),
        draft=payload.get("draft", ""),
        hits=hits,
        citations=bundle.citations,
        retrieval_mode=used_mode,
        prompt_version=prompt_version,
        insert_suggestions=payload.get("insert_suggestions", []),
    )

from __future__ import annotations

import json
from dataclasses import dataclass

from core.formatting.citations import build_citation_bundle
from core.prompts.registry import build_prompt
from core.retrieval.retriever import Hit
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits_mode


class ConceptsBuildError(RuntimeError):
    pass


@dataclass
class ConceptsBuildResult:
    cards: list[dict]
    hits: list[Hit]
    citations: list[str]
    retrieval_mode: str
    prompt_version: str | None = None


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


def build_concepts(
    *,
    workspace_id: str,
    doc_ids: list[str],
    retrieval_mode: str,
) -> ConceptsBuildResult:
    queries = [
        "definition",
        "formula",
        "method",
        "assumption",
        "limitation",
        "metric",
    ]
    batches: list[list[Hit]] = []
    used_mode = retrieval_mode
    for query in queries:
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
        raise ConceptsBuildError("No retrieval hits found for concept extraction.")
    bundle = build_citation_bundle(merged_hits)
    prompt, prompt_version = build_prompt(
        "concept_cards",
        workspace_id,
        context=bundle.numbered_context,
    )
    try:
        response = chat(prompt=prompt, temperature=0.2)
    except ChatConfigError as exc:
        raise ConceptsBuildError(str(exc)) from exc
    try:
        cards = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ConceptsBuildError("Concept extraction returned invalid JSON.") from exc
    if not isinstance(cards, list):
        raise ConceptsBuildError("Concept extraction output must be a JSON list.")
    return ConceptsBuildResult(
        cards=cards,
        hits=merged_hits,
        citations=bundle.citations,
        retrieval_mode=used_mode,
        prompt_version=prompt_version,
    )

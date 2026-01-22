from __future__ import annotations

from dataclasses import dataclass

from core.formatting.citations import build_citation_bundle
from core.prompts.paper_prompts import aggregator_prompt
from core.retrieval.retriever import Hit
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits


class PaperAggregatorError(RuntimeError):
    pass


@dataclass
class AggregationOutput:
    content: str
    citations: list[str]


class PaperAggregator:
    def __init__(self, workspace_id: str, doc_ids: list[str]) -> None:
        self.workspace_id = workspace_id
        self.doc_ids = doc_ids

    def aggregate(self, question: str, progress_cb: callable | None = None) -> AggregationOutput:
        if not self.doc_ids:
            raise PaperAggregatorError("No papers selected.")

        # Retrieval: 2 rounds per paper to control cost
        batches: list[list[Hit]] = []
        total = len(self.doc_ids) * 2
        current = 0
        for doc_id in self.doc_ids:
            for query in [question, "related work"]:
                hits = retrieve_hits(
                    workspace_id=self.workspace_id,
                    query=query,
                    top_k=8,
                    doc_ids=[doc_id],
                )
                if hits:
                    batches.append(hits)
                current += 1
                if progress_cb:
                    progress_cb(current, total)

        merged_hits = _merge_hits(batches)
        if not merged_hits:
            raise PaperAggregatorError("No retrieval hits across selected papers.")
        bundle = build_citation_bundle(merged_hits)
        prompt = aggregator_prompt(bundle.numbered_context, question)
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise PaperAggregatorError(str(exc)) from exc
        return AggregationOutput(content=content, citations=bundle.citations)


def _merge_hits(batches: list[list[Hit]]) -> list[Hit]:
    seen = set()
    merged = []
    for batch in batches:
        for hit in batch:
            if hit.chunk_id in seen:
                continue
            seen.add(hit.chunk_id)
            merged.append(hit)
    return merged

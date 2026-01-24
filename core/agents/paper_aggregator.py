from __future__ import annotations

from dataclasses import dataclass

from core.formatting.citations import build_citation_bundle
from core.prompts.registry import build_prompt
from core.retrieval.retriever import Hit
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits_mode


class PaperAggregatorError(RuntimeError):
    pass


@dataclass
class AggregationOutput:
    content: str
    citations: list[str]
    hits: list[Hit]
    retrieval_mode: str
    run_id: str | None = None
    asset_id: str | None = None
    asset_version_id: str | None = None
    asset_version_index: int | None = None
    prompt_version: str | None = None


class PaperAggregator:
    def __init__(self, workspace_id: str, doc_ids: list[str], retrieval_mode: str) -> None:
        self.workspace_id = workspace_id
        self.doc_ids = doc_ids
        self.retrieval_mode = retrieval_mode

    def aggregate(self, question: str, progress_cb: callable | None = None) -> AggregationOutput:
        if not self.doc_ids:
            raise PaperAggregatorError("No papers selected.")

        # Retrieval: 2 rounds per paper to control cost
        batches: list[list[Hit]] = []
        total = len(self.doc_ids) * 2
        current = 0
        used_mode = self.retrieval_mode
        for doc_id in self.doc_ids:
            for query in [question, "related work"]:
                hits, used_mode = retrieve_hits_mode(
                    workspace_id=self.workspace_id,
                    query=query,
                    mode=self.retrieval_mode,
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
        prompt, prompt_version = build_prompt(
            "paper_aggregate",
            self.workspace_id,
            context=bundle.numbered_context,
            question=question,
        )
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise PaperAggregatorError(str(exc)) from exc
        return AggregationOutput(
            content=content,
            citations=bundle.citations,
            hits=merged_hits,
            retrieval_mode=used_mode,
            prompt_version=prompt_version,
        )


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

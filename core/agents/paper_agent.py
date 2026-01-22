from __future__ import annotations

from dataclasses import dataclass

from core.formatting.citations import build_citation_bundle
from core.prompts.paper_prompts import paper_card_prompt
from core.retrieval.retriever import Hit
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits_mode


class PaperAgentError(RuntimeError):
    pass


@dataclass
class PaperCardOutput:
    content: str
    citations: list[str]
    hits: list[Hit]
    retrieval_mode: str
    run_id: str | None = None


class PaperAgent:
    def __init__(self, workspace_id: str, doc_id: str, retrieval_mode: str) -> None:
        self.workspace_id = workspace_id
        self.doc_id = doc_id
        self.retrieval_mode = retrieval_mode

    def generate_paper_card(self, progress_cb: callable | None = None) -> PaperCardOutput:
        queries = [
            "paper summary",
            "key contributions",
            "strengths weaknesses",
            "extension ideas",
        ]
        batches: list[list[Hit]] = []
        total = len(queries)
        used_mode = self.retrieval_mode
        for idx, query in enumerate(queries, start=1):
            hits, used_mode = retrieve_hits_mode(
                workspace_id=self.workspace_id,
                query=query,
                mode=self.retrieval_mode,
                top_k=8,
                doc_ids=[self.doc_id],
            )
            if not hits:
                raise PaperAgentError("No retrieval hits for paper.")
            batches.append(hits)
            if progress_cb:
                progress_cb(idx, total)

        merged_hits = _merge_hits(batches)
        bundle = build_citation_bundle(merged_hits)
        prompt = paper_card_prompt(bundle.numbered_context)
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise PaperAgentError(str(exc)) from exc
        return PaperCardOutput(
            content=content,
            citations=bundle.citations,
            hits=merged_hits,
            retrieval_mode=used_mode,
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

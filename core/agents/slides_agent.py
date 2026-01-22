from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.formatting.citations import build_citation_bundle
from core.prompts.slides_prompts import qa_prompt, slides_prompt
from core.retrieval.retriever import Hit
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits


class SlidesAgentError(RuntimeError):
    pass


@dataclass
class SlidesOutput:
    deck: str
    citations: list[str]
    qa: list[str]
    saved_path: str | None = None


_DURATION_TO_PAGES = {
    "3": 4,
    "5": 6,
    "10": 9,
    "20": 13,
}


class SlidesAgent:
    def __init__(self, workspace_id: str, doc_id: str) -> None:
        self.workspace_id = workspace_id
        self.doc_id = doc_id

    def generate(self, duration: str, output_dir: Path | None = None) -> SlidesOutput:
        if duration not in _DURATION_TO_PAGES:
            raise SlidesAgentError("Unsupported duration.")

        page_count = _DURATION_TO_PAGES[duration]
        # Retrieval rounds: summary + methods + results + discussion (4 rounds)
        queries = ["summary", "methods", "results", "discussion"]
        batches: list[list[Hit]] = []
        for query in queries:
            hits = retrieve_hits(
                workspace_id=self.workspace_id,
                query=query,
                top_k=8,
                doc_ids=[self.doc_id],
            )
            if hits:
                batches.append(hits)
        merged_hits = _merge_hits(batches)
        if not merged_hits:
            raise SlidesAgentError("No retrieval hits found for slides.")

        bundle = build_citation_bundle(merged_hits)
        try:
            deck = chat(
                prompt=slides_prompt(bundle.numbered_context, page_count),
                temperature=0.2,
            )
            qa_text = chat(
                prompt=qa_prompt(bundle.numbered_context),
                temperature=0.2,
            )
        except ChatConfigError as exc:
            raise SlidesAgentError(str(exc)) from exc

        deck = _normalize_deck(deck, page_count)

        qa_lines = [line.strip() for line in qa_text.splitlines() if line.strip()]
        qa = qa_lines[:10]

        saved_path = None
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = output_dir / f"deck_{timestamp}.md"
            target.write_text(deck, encoding="utf-8")
            saved_path = str(target)

        return SlidesOutput(deck=deck, citations=bundle.citations, qa=qa, saved_path=saved_path)


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


def _normalize_deck(deck: str, target_pages: int) -> str:
    deck = deck.strip()
    if not deck.startswith("---"):
        deck = "---\nmarp: true\n---\n\n" + deck

    slides = [slide.strip() for slide in deck.split("\n---\n")]
    normalized = []
    for slide in slides:
        if "Notes:" not in slide:
            slide = slide + "\n\nNotes:\n- TBD"
        normalized.append(slide)

    # Ensure at least target_pages slides (including front matter slide counts)
    while len(normalized) < target_pages + 1:
        normalized.append("Title\n- TBD\n\nNotes:\n- TBD")

    return "\n---\n".join(normalized)

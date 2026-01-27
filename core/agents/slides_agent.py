from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.formatting.citations import build_citation_bundle
from core.prompts.registry import build_prompt
from core.retrieval.retriever import Hit
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits_mode
from core.quality.validators import validate_slides_deck


class SlidesAgentError(RuntimeError):
    pass


@dataclass
class SlidesOutput:
    deck: str
    citations: list[str]
    qa: list[str]
    saved_path: str | None = None
    hits: list[Hit] | None = None
    retrieval_mode: str | None = None
    warnings: list[str] | None = None
    run_id: str | None = None
    asset_id: str | None = None
    asset_version_id: str | None = None
    asset_version_index: int | None = None
    prompt_version: str | None = None


_DURATION_TO_PAGES = {
    "1": 2,
    "2": 3,
    "3": 4,
    "4": 5,
    "5": 6,
    "6": 7,
    "7": 7,
    "8": 8,
    "9": 8,
    "10": 9,
    "11": 9,
    "12": 10,
    "13": 10,
    "14": 11,
    "15": 11,
    "16": 11,
    "17": 12,
    "18": 12,
    "19": 12,
    "20": 13,
    "21": 13,
    "22": 14,
    "23": 14,
    "24": 15,
    "25": 15,
    "26": 16,
    "27": 16,
    "28": 17,
    "29": 17,
    "30": 18,
}


class SlidesAgent:
    def __init__(self, workspace_id: str, doc_id: str, retrieval_mode: str) -> None:
        self.workspace_id = workspace_id
        self.doc_id = doc_id
        self.retrieval_mode = retrieval_mode

    def generate(self, duration: str, output_dir: Path | None = None) -> SlidesOutput:
        if duration not in _DURATION_TO_PAGES:
            raise SlidesAgentError("Unsupported duration.")

        page_count = _DURATION_TO_PAGES[duration]
        # Retrieval rounds: summary + methods + results + discussion (4 rounds)
        queries = ["summary", "methods", "results", "discussion"]
        batches: list[list[Hit]] = []
        used_mode = self.retrieval_mode
        for query in queries:
            hits, used_mode = retrieve_hits_mode(
                workspace_id=self.workspace_id,
                query=query,
                mode=self.retrieval_mode,
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
            deck_prompt, prompt_version = build_prompt(
                "slides",
                self.workspace_id,
                context=bundle.numbered_context,
                page_count=page_count,
            )
            qa_prompt, _ = build_prompt(
                "slides_qa",
                self.workspace_id,
                context=bundle.numbered_context,
            )
            deck = chat(
                prompt=deck_prompt,
                temperature=0.2,
            )
            qa_text = chat(
                prompt=qa_prompt,
                temperature=0.2,
            )
        except ChatConfigError as exc:
            raise SlidesAgentError(str(exc)) from exc

        deck = _normalize_deck(deck, page_count)
        warnings: list[str] | None = None
        valid, _ = validate_slides_deck(deck)
        if not valid:
            strict_prompt = (
                deck_prompt
                + "\n\nReturn a Marp deck with clear slide titles, bullet lists, and Notes section."
            )
            try:
                deck = chat(prompt=strict_prompt, temperature=0.1)
            except ChatConfigError as exc:
                raise SlidesAgentError(str(exc)) from exc
            deck = _normalize_deck(deck, page_count)
            valid, _ = validate_slides_deck(deck)
            if not valid:
                warnings = [
                    "Slides failed structured validation. Consider rebuilding index or retrying generation."
                ]
                deck = _normalize_deck("Title\n- TBD\n\nNotes:\n- TBD", page_count)

        qa_lines = [line.strip() for line in qa_text.splitlines() if line.strip()]
        qa = qa_lines[:10]

        saved_path = None
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = output_dir / f"deck_{timestamp}.md"
            target.write_text(deck, encoding="utf-8")
            saved_path = str(target)

        return SlidesOutput(
            deck=deck,
            citations=bundle.citations,
            qa=qa,
            saved_path=saved_path,
            hits=merged_hits,
            retrieval_mode=used_mode,
            prompt_version=prompt_version,
            warnings=warnings,
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
